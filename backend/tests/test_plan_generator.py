from datetime import date
from app.models.project import Project, ProjectProduct
from app.models.product import Product
from app.services.plan_generator import generate_project_plan


def test_generate_plan_with_single_product(db_session):
    """测试单个产品 → 生成项目计划"""
    product = db_session.query(Product).first()
    project = Project(name="测试项目", customer_name="测试客户",
                      start_date=date(2026, 8, 1), stage="signed")
    db_session.add(project)
    db_session.flush()

    db_session.add(ProjectProduct(project_id=project.id, product_id=product.id))
    db_session.commit()

    result = generate_project_plan(db_session, project.id)

    assert result.id == project.id
    assert len(result.phases) > 0
    assert result.planned_end_date is not None

    # 验证阶段有任务
    for phase in result.phases:
        assert len(phase.tasks) > 0, f"Phase '{phase.name}' has no tasks"

    print(f"Generated {len(result.phases)} phases, "
          f"{sum(len(p.tasks) for p in result.phases)} tasks")
    print(f"Project: {result.start_date} → {result.planned_end_date}")
    for p in result.phases:
        print(f"  {p.phase_number}. {p.name}: {p.planned_start} → {p.planned_end} [{p.status}]")
        for t in p.tasks:
            print(f"     {t.task_number} {t.name}: {t.planned_start} → {t.planned_end}")


def test_generate_plan_with_multiple_products(db_session):
    """测试多个产品 → 合并阶段"""
    products = db_session.query(Product).limit(2).all()
    project = Project(name="组合项目", customer_name="组合客户",
                      start_date=date(2026, 9, 1), stage="signed")
    db_session.add(project)
    db_session.flush()

    for p in products:
        db_session.add(ProjectProduct(project_id=project.id, product_id=p.id))
    db_session.commit()

    result = generate_project_plan(db_session, project.id)

    assert len(result.phases) > 0
    assert result.planned_end_date is not None
    # 验证合并后的阶段数少于两模板之和
    # 统一包企微4阶段 + 定制包5阶段 - 2重叠(立项/业务摸底) = 7
    assert len(result.phases) == 7, f"Expected 7 merged phases, got {len(result.phases)}"
    # 验证重叠阶段包含任务
    merged_phase = [p for p in result.phases if p.name == "项目立项准备"]
    assert len(merged_phase) == 1
    assert len(merged_phase[0].tasks) >= 2  # 合并后应有多个任务
    print(f"\nMulti-product: {len(result.phases)} phases merged")
    for p in result.phases:
        print(f"  {p.phase_number}. {p.name}: {len(p.tasks)} tasks")
