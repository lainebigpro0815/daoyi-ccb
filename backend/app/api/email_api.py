"""邮件配置 + 发送通知"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.project import Project, ProjectPhase, ProjectTask
from app.models.stakeholder import Stakeholder
from app.services.email_service import send_email, get_config, save_config
from datetime import date

router = APIRouter(prefix="/api/email", tags=["email"])
notify_router = APIRouter(prefix="/api", tags=["email"])


class EmailConfigBody(BaseModel):
    smtp_host: str
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_pass: str = ""
    sender_name: str = "CCB项目管理系统"
    use_ssl: bool = True


class NotifyBody(BaseModel):
    subject: str = ""
    message: str = ""


@router.get("/config")
def email_config():
    return get_config()


@router.post("/config")
def email_config_save(body: EmailConfigBody):
    return save_config(body.model_dump())


@router.post("/test")
def email_test(body: EmailConfigBody):
    """发送测试邮件"""
    result = send_email([body.smtp_user], "CCB系统测试邮件", "这是一封测试邮件，SMTP配置正常。")
    return result


@router.post("/send")
def email_send(to: list[str], subject: str, body: str):
    result = send_email(to, subject, body)
    return result


# ── 项目级通知 ──

@notify_router.post("/projects/{project_id}/notify/overdue")
def notify_overdue(project_id: int, db: Session = Depends(get_db)):
    """发送逾期通知给项目干系人（有邮箱的）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"success": False, "message": "项目不存在"}

    # 查逾期任务
    today = date.today()
    phases = db.query(ProjectPhase).filter(
        ProjectPhase.project_id == project_id
    ).all()
    phase_ids = [p.id for p in phases]

    overdue_tasks = db.query(ProjectTask).filter(
        ProjectTask.project_phase_id.in_(phase_ids),
        ProjectTask.planned_end != None,
        ProjectTask.planned_end < today,
        ProjectTask.status.in_(["pending", "in_progress"]),
    ).all()

    if not overdue_tasks:
        return {"success": False, "message": "暂无逾期任务"}

    # 构建邮件内容
    body_lines = [f"项目「{project.name}」逾期任务提醒：\n"]
    for t in overdue_tasks:
        phase_name = ""
        for p in phases:
            if p.id == t.project_phase_id:
                phase_name = p.name
                break
        body_lines.append(f"- [{phase_name}] {t.name} (负责人:{t.assignee or '未分配'}, 逾期{t.planned_end and (today - t.planned_end).days or 0}天)")

    body_lines.append(f"\n请及时处理。\n{date.today()}")

    subject = f"【CCB】{project.name} — 逾期任务提醒"
    body = "\n".join(body_lines)

    # 找有邮箱的干系人
    stakeholders = db.query(Stakeholder).filter(
        Stakeholder.project_id == project_id,
        Stakeholder.email != "",
        Stakeholder.email != None,
    ).all()

    to_addrs = [s.email for s in stakeholders if s.email]
    if not to_addrs:
        return {"success": False, "message": "项目干系人未配置邮箱"}

    result = send_email(to_addrs, subject, body)
    result["notified_count"] = len(to_addrs)
    result["overdue_count"] = len(overdue_tasks)
    return result
