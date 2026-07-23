import os, json, asyncio
from datetime import date
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectPhase, ProjectTask
from app.schemas.ai import ChatMessage, AIAction

# ============ 配置：从 UI 设置读取 ============
CONFIG_FILE = Path(__file__).parent.parent.parent / "data" / "ai_config.json"


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "provider": os.environ.get("AI_PROVIDER", "mock"),
        "api_key": os.environ.get("OPENAI_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", ""),
        "api_base": os.environ.get("OPENAI_API_BASE", "https://api.deepseek.com"),
        "model": os.environ.get("OPENAI_MODEL", "deepseek-chat"),
    }


AI_PROVIDER = None  # resolved per-call from _load_config()
OPENAI_API_BASE = None
OPENAI_API_KEY = None
OPENAI_MODEL = None
ANTHROPIC_API_KEY = None


def get_provider_info() -> dict:
    """返回当前可用的 AI 提供方信息（前端选择用）"""
    cfg = _load_config()
    providers = [{"id": "mock", "name": "开发模式 (Mock)", "models": ["mock"]}]

    if cfg.get("api_key"):
        key = cfg["api_key"]
        base = cfg.get("api_base", "").lower()
        model = cfg.get("model", "")

        if cfg["provider"] == "anthropic":
            providers.insert(0, {"id": "anthropic", "name": "Claude (Anthropic)", "models": [model or "claude-sonnet-4-20250514"]})
        else:
            name = "OpenAI 兼容"
            if "deepseek" in base: name = "DeepSeek"
            elif "qwen" in base or "tongyi" in base: name = "通义千问"
            elif "glm" in base or "zhipu" in base: name = "智谱 GLM"
            elif "moonshot" in base: name = "Moonshot (月之暗面)"
            providers.insert(0, {"id": "openai", "name": name, "models": [model or "deepseek-chat"]})

    return {"current": cfg.get("provider", "mock"), "providers": providers}


def build_project_context(db: Session, project_id: int) -> str:
    """构建项目上下文"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return ""

    lines = [f"项目名称：{project.name}",
             f"客户名称：{project.customer_name}",
             f"项目阶段：{project.stage}",
             f"启动日期：{project.start_date}",
             f"计划结束：{project.planned_end_date or '未设置'}",
             f"状态：{project.status}",
             ""]

    phases = db.query(ProjectPhase).filter(
        ProjectPhase.project_id == project_id
    ).order_by(ProjectPhase.sort_order).all()

    total_tasks = 0
    completed_tasks = 0
    overdue_tasks = 0

    for phase in phases:
        tasks = db.query(ProjectTask).filter(
            ProjectTask.project_phase_id == phase.id
        ).order_by(ProjectTask.sort_order).all()

        phase_completed = sum(1 for t in tasks if t.status == "completed")
        total_tasks += len(tasks)
        completed_tasks += phase_completed

        lines.append(f"[{phase.status}] 阶段{phase.phase_number}：{phase.name} ({phase.planned_start}~{phase.planned_end})")
        for t in tasks:
            status_icon = {"completed": "[x]", "in_progress": "[>]", "pending": "[ ]", "blocked": "[!]"}
            icon = status_icon.get(t.status, "[?]")
            overdue = ""
            if t.status in ("pending", "in_progress") and t.planned_end and t.planned_end < date.today():
                overdue = " **已逾期**"
                overdue_tasks += 1
            lines.append(f"  {icon} {t.task_number} {t.name} (负责人:{t.assignee or '未分配'}, 进度:{t.progress}%, 计划完成:{t.planned_end}){overdue}")
        lines.append("")

    lines.append(f"--- 统计：共 {total_tasks} 个任务，已完成 {completed_tasks} 个，逾期 {overdue_tasks} 个")
    return "\n".join(lines)


def _msg_role(m: any) -> str:
    return m["role"] if isinstance(m, dict) else m.role


def _msg_content(m: any) -> str:
    return m["content"] if isinstance(m, dict) else m.content


def _to_api_msg(m: any) -> dict:
    return {"role": _msg_role(m), "content": _msg_content(m)}


def build_system_prompt(context: str) -> str:
    """构建 system prompt"""
    parts = ["你是 CCB 项目管理系统的 AI 助手，擅长回答项目相关问题。"]

    if context:
        parts.append(f"\n当前项目状态：\n{context}")
        parts.append("""
你可以通过对话修改项目数据。需要操作时，在回复末尾添加 ```json 块输出操作指令：

**操作格式：**
```json
{"action_type":"create|update|delete","entity":"task|risk|issue|milestone|acceptance|training|stakeholder","entity_id":数字,"data":{字段名:值}}
```

**可操作实体和字段：**
- task: name, assignee, status(pending/in_progress/completed/blocked), progress(0-100), planned_start, planned_end
- risk: level(高/中/低), description, category, impact, probability, mitigation, owner, status(open/closed)
- issue: severity(严重/一般/轻微), description, module, priority(高/中/低), assignee, status(open/in_progress/resolved/closed), resolution
- milestone: name, planned_date, actual_date, status(pending/completed/delayed), description
- acceptance: item, standard, status(pending/passed/failed), result
- training: content, target, planned_date, actual_date, status(pending/completed), remark
- stakeholder: group_name(客户联系人/内部联系人), name, company, role, phone, email

**示例：**
- 创建风险: {"action_type":"create","entity":"risk","data":{"level":"高","description":"客户可能延迟付款","mitigation":"提前沟通"}}
- 完成任务: {"action_type":"update","entity":"task","entity_id":5,"data":{"status":"completed","progress":100}}
- 删除问题: {"action_type":"delete","entity":"issue","entity_id":3}

注意：create 不需要 entity_id，update 和 delete 需要。操作需要用户确认后才执行。
""")
    else:
        parts.append("\n用户未选择具体项目时，可以回答通用问题，或询问用户想了解哪个项目。")

    return "\n".join(parts)


async def stream_ai_response(
    context: str,
    messages: list[ChatMessage],
    provider: str = "",
    model: str = "",
) -> AsyncGenerator[str, None]:
    """
    调用 AI API 流式返回。
    支持 provider: mock / openai / anthropic
    """
    cfg = _load_config()
    actual_provider = provider or cfg.get("provider", "mock")
    api_key = cfg.get("api_key", "")
    api_base = cfg.get("api_base", "https://api.deepseek.com")
    actual_model = model or cfg.get("model", "deepseek-chat")

    # Mock
    if actual_provider == "mock" or not api_key:
        ctx_len = len(context) if context else 0
        # Mock mode - simulate intent for UI testing
        msg_text = _msg_content(messages[-1]) if messages else ""
        mock_text = "【Mock 模式】已收到请求。"
        mock_action = None

        if "新增" in msg_text or "添加" in msg_text or "创建" in msg_text:
            mock_text += "\n\n已解析到创建意图。模拟创建一条示例数据。"
            mock_action = '{"action_type":"create","entity":"task","entity_id":null,"data":{"name":"模拟任务","assignee":"张三","status":"pending","progress":0}}'
        elif "改" in msg_text or "更新" in msg_text or "修改" in msg_text or "完成" in msg_text:
            mock_text += "\n\n已解析到更新意图。模拟完成任务 #1。"
            mock_action = '{"action_type":"update","entity":"task","entity_id":1,"data":{"status":"completed","progress":100}}'
        elif "删除" in msg_text or "移除" in msg_text:
            mock_text += "\n\n已解析到删除意图。模拟删除任务 #1。"
            mock_action = '{"action_type":"delete","entity":"task","entity_id":1,"data":{}}'
        else:
            mock_text += "\n\n对话功能需要配置 API Key 后使用。\n\n前往「系统设置」→ AI 模型配置 填写 API Key。"

        # 生成包含 action JSON 的回复，让前端能收到 action 事件
        full = mock_text
        if mock_action:
            full += f"\n\n模拟操作指令：\n```json\n{mock_action}\n```"
        for i in range(0, len(full), 3):
            yield full[i:i+3]
            await asyncio.sleep(0.02)
        return

    system = build_system_prompt(context)

    # OpenAI 兼容（DeepSeek / 通义千问 / GLM / 月之暗面 等）
    if actual_provider == "openai":
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url=api_base)
            api_messages = [{"role": "system", "content": system}]
            api_messages += [_to_api_msg(m) for m in messages]

            stream = await client.chat.completions.create(
                model=actual_model,
                messages=api_messages,
                max_tokens=2048,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            yield f"\n\n[AI 服务异常：{str(e)}]"

    # Anthropic Claude
    elif actual_provider == "anthropic":
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=api_key)
            api_messages = [_to_api_msg(m) for m in messages]

            async with client.messages.stream(
                model=actual_model,
                max_tokens=2048,
                system=system,
                messages=api_messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            yield f"\n\n[AI 服务异常：{str(e)}]"

    else:
        yield f"\n\n[未配置 AI Provider。请在系统设置中配置 AI 参数]"


def parse_action(text: str) -> AIAction | None:
    """从 AI 回复中提取 JSON action"""
    import re
    matches = re.findall(r'```json\n?(.*?)```', text, re.DOTALL)
    for m in matches:
        try:
            data = json.loads(m.strip())
            return AIAction(**data)
        except (json.JSONDecodeError, Exception):
            continue
    return None
