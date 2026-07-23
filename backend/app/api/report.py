from datetime import date
from io import BytesIO
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.services.report_service import generate_weekly_report, generate_report_docx

router = APIRouter(prefix="/api/projects/{project_id}/report", tags=["report"])

REPORT_DIR = Path(__file__).parent.parent.parent / "data" / "reports"


@router.get("/weekly")
async def get_weekly_report(project_id: int, db: Session = Depends(get_db)):
    """生成并返回项目周报文本，同时保存 Word 文件"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    report_text = await generate_weekly_report(db, project_id)

    # 保存 docx 文件
    safe_name = project.name.replace("/", "_").replace("\\", "_").replace(":", "_")
    filename = f"{safe_name}_周报_{date.today().isoformat()}.docx"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = REPORT_DIR / filename

    docx_bytes = generate_report_docx(report_text, project.name)
    filepath.write_bytes(docx_bytes)

    return {
        "report_text": report_text,
        "report_url": f"/data/reports/{filename}",
    }


@router.get("/export")
async def export_report_docx(project_id: int, db: Session = Depends(get_db)):
    """导出项目周报为 Word 文档下载"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    report_text = await generate_weekly_report(db, project_id)
    docx_bytes = generate_report_docx(report_text, project.name)

    safe_name = project.name.replace("/", "_").replace("\\", "_").replace(":", "_")
    filename = f"{safe_name}_周报_{date.today().isoformat()}.docx"

    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
