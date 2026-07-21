from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectProduct, ProjectPhase, ProjectTask
from app.models.template import ProcessTemplate, PhaseDefinition, TaskDefinition


def generate_project_plan(db: Session, project_id: int) -> Project:
    """
    核心计划生成引擎。
    根据项目的产品组合，加载各产品的活跃模板，合并阶段和任务，
    以项目启动日为基准推算日期，写入数据库。
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # 1. 获取项目已关联的产品ID
    product_ids = [pp.product_id for pp in project.products]

    # 2. 获取这些产品的活跃模板，按模板加载阶段→任务
    templates = db.query(ProcessTemplate).filter(
        ProcessTemplate.product_id.in_(product_ids),
        ProcessTemplate.is_active == True
    ).order_by(ProcessTemplate.product_id).all()

    if not templates:
        raise ValueError("No active templates found for selected products")

    # 3. 合并阶段：按阶段名去重合并
    phase_map = {}  # name -> (phase_obj, template_id, tasks_from_template)

    for template in templates:
        phases = db.query(PhaseDefinition).filter(
            PhaseDefinition.template_id == template.id
        ).order_by(PhaseDefinition.sort_order).all()

        for phase_def in phases:
            tasks = db.query(TaskDefinition).filter(
                TaskDefinition.phase_id == phase_def.id
            ).order_by(TaskDefinition.sort_order).all()

            if phase_def.name in phase_map:
                # 同名阶段合并任务
                existing = phase_map[phase_def.name]
                existing[2].extend(tasks)
            else:
                phase_map[phase_def.name] = [phase_def, template.id, list(tasks)]

    # 4. 按 sort_order 排序合并后的阶段
    sorted_phases = sorted(phase_map.items(), key=lambda x: x[1][0].sort_order)

    # 5. 创建 ProjectPhase 和 ProjectTask，推算日期
    cursor_date = project.start_date
    for pi, (phase_name, (phase_def, tmpl_id, tasks)) in enumerate(sorted_phases, 1):
        # 计算本阶段总估算天数
        total_days = sum((t.estimated_days or 1) for t in tasks) if tasks else 1

        phase_start = cursor_date
        phase_end = _add_workdays(phase_start, total_days - 1)

        proj_phase = ProjectPhase(
            project_id=project.id,
            source_phase_id=phase_def.id,
            phase_number=pi,
            name=phase_name,
            planned_start=phase_start,
            planned_end=phase_end,
            status="pending",
            sort_order=pi,
        )
        db.add(proj_phase)
        db.flush()

        # 生成任务
        task_cursor = phase_start
        for ti, task_def in enumerate(tasks, 1):
            task_days = task_def.estimated_days or 1
            task_start = task_cursor
            task_end = _add_workdays(task_start, task_days - 1)

            proj_task = ProjectTask(
                project_phase_id=proj_phase.id,
                source_task_id=task_def.id,
                task_number=task_def.task_number,
                name=task_def.name,
                guide=task_def.guide or "",
                deliverable=task_def.deliverable or "",
                assignee="",
                planned_start=task_start,
                planned_end=task_end,
                status="pending",
                progress=0,
                sort_order=ti,
            )
            db.add(proj_task)
            task_cursor = _add_workdays(task_end, 1)  # 任务之间间隔1工作日

        cursor_date = _add_workdays(phase_end, 1)

    # 6. 更新项目计划结束日期
    project.planned_end_date = cursor_date - timedelta(days=1)
    db.commit()
    db.refresh(project)
    return project


def _add_workdays(from_date: date, days: int) -> date:
    """
    从 from_date 开始，增加 days 个工作日。
    注意：不处理法定节假日，仅跳过周六日。
    """
    current = from_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # 周一到周五
            added += 1
    return current
