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
def execute_action(project_id: int, body: dict, db: Session = Depends(get_db)):
    """通用 AI 操作执行器 — 对话改所有数据"""
    from app.models.stakeholder import Stakeholder
    from app.models.tracking import Risk, Issue, Milestone, AcceptanceItem, TrainingItem

    action_type = body.get("action_type", "none")   # create / update / delete
    entity = body.get("entity", "")                 # task / risk / issue / milestone / acceptance / training / stakeholder
    entity_id = body.get("entity_id")
    data = body.get("data", {})

    # Map entity to model class
    MODEL_MAP = {
        "task": ProjectTask,
        "risk": Risk,
        "issue": Issue,
        "milestone": Milestone,
        "acceptance": AcceptanceItem,
        "training": TrainingItem,
        "stakeholder": Stakeholder,
    }

    Model = MODEL_MAP.get(entity)
    if not Model:
        return {"status": "error", "reason": f"unknown entity: {entity}"}

    from datetime import date

    # CREATE
    if action_type == "create":
        if entity == "task":
            from app.models.project import ProjectPhase
            phase = db.query(ProjectPhase).filter(ProjectPhase.project_id == project_id).order_by(ProjectPhase.sort_order).first()
            if not phase:
                return {"status": "error", "reason": "no phases"}
            obj = Model(project_phase_id=phase.id, task_number="AI", name=data.get("name", "新任务"), status="pending")
        else:
            obj = Model(project_id=project_id, **data)
            if hasattr(obj, "created_at") and not obj.created_at:
                obj.created_at = date.today()
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return {"status": "ok", "action": "created", "entity": entity, "id": obj.id}

    # UPDATE
    if action_type == "update":
        filters = {Model.id: entity_id} if entity_id else {}
        if entity == "task":
            filters = {Model.id: entity_id} if entity_id else {}
        obj = db.query(Model).filter(Model.id == entity_id).first() if entity_id else None
        if not obj:
            return {"status": "error", "reason": f"{entity}#{entity_id} not found"}
        for k, v in data.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        db.commit()
        return {"status": "ok", "action": "updated", "entity": entity, "id": entity_id}

    # DELETE
    if action_type == "delete":
        obj = db.query(Model).filter(Model.id == entity_id).first() if entity_id else None
        if not obj:
            return {"status": "error", "reason": f"{entity}#{entity_id} not found"}
        db.delete(obj)
        db.commit()
        return {"status": "ok", "action": "deleted", "entity": entity, "id": entity_id}

    return {"status": "ignored", "reason": "unknown action"}
