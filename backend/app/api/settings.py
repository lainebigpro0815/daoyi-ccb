import json, os
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/api/settings", tags=["settings"])

CONFIG_FILE = Path(__file__).parent.parent.parent / "data" / "ai_config.json"


def _read_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"provider": "mock", "api_key": "", "api_base": "", "model": ""}


def _write_config(cfg: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/ai")
def get_ai_settings():
    """读取 AI 配置"""
    cfg = _read_config()
    # 显示当前配置（隐藏完整 key）
    masked = {**cfg}
    if masked.get("api_key") and len(masked["api_key"]) > 8:
        masked["api_key"] = masked["api_key"][:4] + "****" + masked["api_key"][-4:]
    return masked


@router.post("/ai")
def save_ai_settings(data: dict):
    """保存 AI 配置"""
    current = _read_config()
    current["provider"] = data.get("provider", current["provider"])
    current["model"] = data.get("model", current.get("model", ""))

    # Only update key if provided (frontend sends masked key as ****)
    new_key = data.get("api_key", "")
    if new_key and "****" not in new_key:
        current["api_key"] = new_key
    if "api_base" in data and data["api_base"]:
        current["api_base"] = data["api_base"]

    _write_config(current)
    return {"status": "ok"}


@router.post("/ai/test")
async def test_ai_connection(data: dict):
    """测试 AI 连接"""
    provider = data.get("provider", "mock")
    api_key = data.get("api_key", "")
    api_base = data.get("api_base", "")
    model = data.get("model", "")

    if provider == "mock" or not api_key or "****" in api_key:
        return {"status": "ok", "message": "Mock 模式无需测试"}

    try:
        if provider == "openai":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url=api_base)
            await client.chat.completions.create(
                model=model or "deepseek-chat",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
        elif provider == "anthropic":
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=api_key)
            await client.messages.create(
                model=model or "claude-sonnet-4-20250514",
                max_tokens=5,
                messages=[{"role": "user", "content": "hi"}],
            )
        return {"status": "ok", "message": "连接成功"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
