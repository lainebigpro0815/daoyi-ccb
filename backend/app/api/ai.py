import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project, ProjectTask
from app.schemas.ai import AIQueryRequest
from app.services.ai_service import (
    build_project_context, stream_ai_response, parse_action, get_provider_info
)

# ============ 通用 AI 路由（无需项目 ID） ============
router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/config")
def ai_config():
    """返回当前可用的 AI Provider 列表"""
    return get_provider_info()


@router.post("/query")
async def ai_query_general(req: AIQueryRequest):
    """通用 AI 对话（无需项目上下文）"""
    async def event_stream():
        messages = [*req.history, {"role": "user", "content": req.message}]
        full_text = ""
        async for chunk in stream_ai_response("", messages, req.provider, req.model):
            full_text += chunk
            yield f"data: {json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


# ============ 项目 AI 路由（需项目 ID） ============
project_router = APIRouter(prefix="/api/projects/{project_id}/ai", tags=["ai"])


@project_router.post("/query")
async def ai_query(project_id: int, req: AIQueryRequest, db: Session = Depends(get_db)):
    """项目级 AI 对话（带项目上下文）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    context = build_project_context(db, project_id)

    async def event_stream():
        messages = [*req.history, {"role": "user", "content": req.message}]
        full_text = ""
        async for chunk in stream_ai_response(context, messages, req.provider, req.model):
            full_text += chunk
            yield f"data: {json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False)}\n\n"

        action = parse_action(full_text)
        if action and action.action_type != "none":
            yield f"data: {json.dumps({'type': 'action', 'action': action.model_dump()}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@project_router.post("/execute")
def execute_action(project_id: int, action: dict, db: Session = Depends(get_db)):
    """执行 AI 建议的操作（用户确认后调用）"""
    action_type = action.get("action_type")
    params = action.get("params", {})

    if action_type == "adjust_dates":
        task_ids = params.get("task_ids", [])
        new_end = params.get("new_end")
        if new_end:
            from datetime import date
            end_date = date.fromisoformat(new_end)
            tasks = db.query(ProjectTask).filter(
                ProjectTask.id.in_(task_ids)
            ).all()
            for t in tasks:
                t.planned_end = end_date
            db.commit()
            return {"status": "ok", "updated": len(tasks)}

    elif action_type == "update_task":
        task_id = params.get("task_id")
        updates = params.get("updates", {})
        task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
        if task:
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            db.commit()
            return {"status": "ok", "task_id": task_id}

    return {"status": "ignored", "reason": "unknown action type"}
