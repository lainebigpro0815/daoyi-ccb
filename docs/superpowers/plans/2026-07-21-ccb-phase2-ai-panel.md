# CCB 项目管理系统 — Phase 2 AI 面板

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement task-by-task.

**Goal:** 右侧 AI 面板接入，实现对话式项目查询、计划调整、文档生成

**Architecture:** 前端 AIPanel.vue 组件（右侧可折叠）+ 后端 SSE 流式 AI 端点。前端发送用户消息 → 后端收集项目上下文 + 调用 Claude API → 流式返回文本 + 结构化 action。读写分离：读直接回答，写操作需 PM 确认。

**Tech Stack:** Vue3 + Element Plus (前端), FastAPI + SSE + anthropic Python SDK (后端)

## Global Constraints

- AI 端点需 `ANTHROPIC_API_KEY` 环境变量，缺失时返回友好提示
- SSE 流式输出，前端逐块渲染 Markdown
- 写操作（调整日期、更新状态）返回 JSON action，前端弹出确认后执行
- 右侧面板可折叠/展开，宽度 360px
- 不修改现有 API 和数据模型

---

## 文件结构

```
backend/
├── app/
│   ├── api/
│   │   └── ai.py                  # POST /api/projects/{id}/ai/query SSE 端点
│   ├── services/
│   │   └── ai_service.py          # AI 服务（构建上下文、调用 Claude、解析 action）
│   └── schemas/
│       └── ai.py                  # ChatMessage, AIRequest, AIAction schemas

frontend/
├── src/
│   ├── components/
│   │   └── AIPanel.vue            # 右侧 AI 面板（聊天界面 + 流式渲染）
│   ├── api/
│   │   └── ai.ts                  # AI API 调用（SSE 读取）
│   └── stores/
│       └── ai.ts                  # AI 面板状态（消息历史、loading、面板开关）
```

---

### Task 1: 后端 AI Service + API 端点

**Files:**
- Create: `backend/app/services/ai_service.py`
- Create: `backend/app/schemas/ai.py`
- Create: `backend/app/api/ai.py`

**Interfaces:**
- `build_project_context(db, project_id) -> str` — 构建项目上下文字符串
- `stream_ai_response(project_context, messages) -> AsyncGenerator[str]` — 调用 Claude API 流式返回
- `parse_action(text) -> AIAction | None` — 从 AI 回复中提取结构化 action
- `POST /api/projects/{id}/ai/query` — SSE 端点，接收 `{ "message": "...", "history": [...] }`

- [ ] **Step 1: Create schemas/ai.py**

```python
from pydantic import BaseModel
from typing import Optional, Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AIQueryRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class AIAction(BaseModel):
    action_type: Literal["update_task", "adjust_dates", "generate_doc", "none"]
    params: dict = {}
    summary: str = ""


class AIStreamEvent(BaseModel):
    type: Literal["text", "action", "error", "done"]
    content: str = ""
    action: Optional[AIAction] = None
```

- [ ] **Step 2: Create services/ai_service.py**

```python
import os, json, asyncio
from datetime import date
from typing import AsyncGenerator
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectPhase, ProjectTask
from app.schemas.ai import ChatMessage, AIAction


ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def build_project_context(db: Session, project_id: int) -> str:
    """构建项目上下文，供 AI 理解项目状态"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return "Project not found."

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


async def stream_ai_response(
    context: str,
    messages: list[ChatMessage],
    system_prompt: str = ""
) -> AsyncGenerator[str, None]:
    """
    调用 Claude API 流式返回。
    如果环境变量 ANTHROPIC_API_KEY 未设置，返回模拟响应。
    """
    if not ANTHROPIC_API_KEY:
        # Mock mode for development
        mock = f"【开发模式】已收到你的问题。\n\n项目上下文已加载（{len(context)}字符）。\n\n设置 ANTHROPIC_API_KEY 环境变量即可接入 Claude API。"
        for i in range(0, len(mock), 3):
            yield mock[i:i+3]
            await asyncio.sleep(0.02)
        return

    try:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

        system = system_prompt or f"""你是 CCB 项目管理系统的 AI 助手。
你擅长阅读项目状态、回答进度问题、给出风险预警、调整计划安排。

项目当前状态如下：
{context}

注意：
- 用户询问进度时，直接回答最新状态
- 如果用户要求调整计划，请输出 JSON action 格式：{{"action_type":"adjust_dates","params":{{"task_ids":[...],"new_end":"YYYY-MM-DD"}},"summary":"..."}}
- 操作需要用户确认后才执行
"""

        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system,
            messages=api_messages
        ) as stream:
            async for text in stream.text_stream:
                yield text

    except Exception as e:
        yield f"\n\n[AI 服务异常：{str(e)}]"


def parse_action(text: str) -> AIAction | None:
    """从 AI 回复中提取 JSON action（如果有）"""
    import re
    # Match ```json ... ``` blocks
    matches = re.findall(r'```json\n?(.*?)```', text, re.DOTALL)
    for m in matches:
        try:
            data = json.loads(m.strip())
            return AIAction(**data)
        except (json.JSONDecodeError, Exception):
            continue
    return None
```

- [ ] **Step 3: Create api/ai.py**

```python
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.schemas.ai import AIQueryRequest
from app.services.ai_service import (
    build_project_context, stream_ai_response, parse_action
)

router = APIRouter(prefix="/api/projects/{project_id}/ai", tags=["ai"])


@router.post("/query")
async def ai_query(project_id: int, req: AIQueryRequest, db: Session = Depends(get_db)):
    """
    SSE 端点：用户发送消息，AI 流式返回。
    返回格式：data: {"type":"text","content":"..."}\n\n
              data: {"type":"action","action":{...}}\n\n
              data: {"type":"done"}\n\n
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    context = build_project_context(db, project_id)

    async def event_stream():
        # Build history with current message
        messages = [*req.history, {"role": "user", "content": req.message}]

        full_text = ""
        async for chunk in stream_ai_response(context, messages):
            full_text += chunk
            yield f"data: {json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False)}\n\n"

        # Check for action in complete response
        action = parse_action(full_text)
        if action and action.action_type != "none":
            yield f"data: {json.dumps({'type': 'action', 'action': action.model_dump()}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/execute")
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
            tasks = db.query(Project.task).filter(
                Project.task.id.in_(task_ids)
            ).all()
            for t in tasks:
                t.planned_end = end_date
            db.commit()
            return {"status": "ok", "updated": len(tasks)}

    elif action_type == "update_task":
        task_id = params.get("task_id")
        updates = params.get("updates", {})
        task = db.query(Project.task).filter(Project.task.id == task_id).first()
        if task:
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            db.commit()
            return {"status": "ok", "task_id": task_id}

    return {"status": "ignored", "reason": "unknown action type"}
```

- [ ] **Step 4: Register router in main.py**

```python
from app.api import ai as ai_api
app.include_router(ai_api.router)
```

- [ ] **Step 5: Install anthropic SDK**

```bash
cd D:\APM\backend
pip install anthropic
```

- [ ] **Step 6: Test**

```bash
cd D:\APM\backend
uvicorn main:app --reload --port 8000 &
sleep 3

# Test without API key (mock mode)
curl -s -N -X POST http://localhost:8000/api/projects/1/ai/query \
  -H "Content-Type: application/json" \
  -d '{"message":"这个项目现在什么进度？","history":[]}'
```

Expected: SSE events with mock text response, then done event.

---

### Task 2: 前端 AI Panel 组件

**Files:**
- Create: `frontend/src/components/AIPanel.vue`
- Create: `frontend/src/api/ai.ts`
- Create: `frontend/src/stores/ai.ts`

**Interfaces:**
- `AIPanel.vue` — 右侧可折叠面板，显示聊天界面
- `ai.ts` — `sendQuery(projectId, message, history)` → EventSource for SSE
- `ai.ts` — `executeAction(projectId, action)` → POST
- `stores/ai.ts` — Pinia store：消息列表、loading、面板展开状态

- [ ] **Step 1: Create stores/ai.ts**

```typescript
import { defineStore } from 'pinia'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AIAction {
  action_type: string
  params: Record<string, any>
  summary: string
}

interface AIState {
  messages: ChatMessage[]
  loading: boolean
  panelOpen: boolean
  pendingAction: AIAction | null
}

export const useAIStore = defineStore('ai', {
  state: (): AIState => ({
    messages: [],
    loading: false,
    panelOpen: true,
    pendingAction: null,
  }),
  actions: {
    togglePanel() {
      this.panelOpen = !this.panelOpen
    },
    addMessage(msg: ChatMessage) {
      this.messages.push(msg)
    },
    appendToLastMessage(text: string) {
      const last = this.messages[this.messages.length - 1]
      if (last && last.role === 'assistant') {
        last.content += text
      }
    },
    clearMessages() {
      this.messages = []
    },
  },
})
```

- [ ] **Step 2: Create api/ai.ts**

```typescript
import api from './index'
import type { ChatMessage, AIAction } from '@/stores/ai'

export async function sendQuery(
  projectId: number,
  message: string,
  history: ChatMessage[],
  onText: (chunk: string) => void,
  onAction: (action: AIAction) => void,
  onDone: () => void,
  onError: (err: string) => void,
): Promise<void> {
  try {
    const resp = await fetch(`/api/projects/${projectId}/ai/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history }),
    })

    if (!resp.ok) {
      onError(`请求失败: ${resp.status}`)
      return
    }

    const reader = resp.body?.getReader()
    if (!reader) return

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'text') {
              onText(data.content)
            } else if (data.type === 'action') {
              onAction(data.action)
            } else if (data.type === 'done') {
              onDone()
            } else if (data.type === 'error') {
              onError(data.content)
            }
          } catch {
            // skip parse errors for incomplete chunks
          }
        }
      }
    }
  } catch (e: any) {
    onError(e.message || '连接失败')
  }
}

export async function executeAction(projectId: number, action: AIAction) {
  const res = await api.post(`/projects/${projectId}/ai/execute`, action)
  return res.data
}
```

- [ ] **Step 3: Create AIPanel.vue**

```vue
<template>
  <div class="ai-panel" :class="{ collapsed: !store.panelOpen }">
    <!-- 切换按钮 -->
    <div class="ai-toggle" @click="store.togglePanel()">
      <el-icon size="20"><ChatLineSquare /></el-icon>
      <span v-if="!store.panelOpen" style="writing-mode: vertical-rl; margin-top: 8px;">AI 助手</span>
    </div>

    <!-- 面板内容 -->
    <div v-show="store.panelOpen" class="ai-content">
      <div class="ai-header">
        <span style="font-weight: 600; font-size: 14px;">AI 助手</span>
        <el-button link size="small" @click="store.clearMessages()">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>

      <!-- 消息列表 -->
      <div class="ai-messages" ref="msgContainer">
        <div v-if="store.messages.length === 0" class="ai-welcome">
          <p style="font-size: 14px; font-weight: 500;">可以问我：</p>
          <ul style="font-size: 12px; color: #666; line-height: 1.8;">
            <li>这个项目现在到什么阶段了？</li>
            <li>第一阶段要注意什么？</li>
            <li>帮我查一下有没有逾期任务</li>
            <li>把定制包部署任务的截止日延后一周</li>
          </ul>
        </div>

        <div v-for="(msg, i) in store.messages" :key="i"
             class="ai-message" :class="msg.role">
          <div class="msg-label">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
          <div class="msg-content" v-html="renderMarkdown(msg.content)"></div>
        </div>

        <div v-if="store.loading" class="ai-message assistant">
          <div class="msg-label">AI</div>
          <div class="msg-content">
            <span class="typing-dot">.</span>
            <span class="typing-dot">.</span>
            <span class="typing-dot">.</span>
          </div>
        </div>
      </div>

      <!-- 操作确认弹窗 -->
      <el-dialog v-model="showConfirm" title="确认执行操作" width="360px">
        <p>{{ store.pendingAction?.summary }}</p>
        <template #footer>
          <el-button @click="rejectAction">取消</el-button>
          <el-button type="primary" @click="confirmAction">确认执行</el-button>
        </template>
      </el-dialog>

      <!-- 输入框 -->
      <div class="ai-input">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          placeholder="输入问题..."
          :disabled="store.loading"
          @keydown.enter.ctrl="sendMessage"
        />
        <el-button type="primary" :loading="store.loading"
                   @click="sendMessage" style="margin-top: 4px; width: 100%;">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useAIStore } from '@/stores/ai'
import { sendQuery, executeAction } from '@/api/ai'

const props = defineProps<{ projectId: number }>()
const store = useAIStore()
const inputMessage = ref('')
const msgContainer = ref<HTMLElement | null>(null)
const showConfirm = ref(false)

// Auto-scroll on new messages
watch(() => store.messages.length, () => {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
})

async function sendMessage() {
  const msg = inputMessage.value.trim()
  if (!msg || store.loading) return

  inputMessage.value = ''
  store.addMessage({ role: 'user', content: msg })
  store.loading = true
  store.addMessage({ role: 'assistant', content: '' })

  await sendQuery(
    props.projectId,
    msg,
    store.messages.filter(m => m.role === 'user' || m.role === 'assistant').slice(0, -1),
    (chunk) => store.appendToLastMessage(chunk),
    (action) => {
      store.pendingAction = action
      showConfirm.value = true
    },
    () => { store.loading = false },
    (err) => {
      store.loading = false
      store.appendToLastMessage(`\n\n[错误: ${err}]`)
    },
  )
}

async function confirmAction() {
  if (!store.pendingAction) return
  showConfirm.value = false
  try {
    const result = await executeAction(props.projectId, store.pendingAction)
    store.appendToLastMessage(`\n\n✅ 操作已执行: ${JSON.stringify(result)}`)
  } catch (e: any) {
    store.appendToLastMessage(`\n\n❌ 操作执行失败: ${e.message}`)
  }
  store.pendingAction = null
}

function rejectAction() {
  showConfirm.value = false
  store.appendToLastMessage('\n\n⚠️ 操作已取消')
  store.pendingAction = null
}

function renderMarkdown(text: string): string {
  // Simple markdown-like rendering
  return text
    .replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre style="background:#f5f5f5;padding:8px;border-radius:4px;font-size:12px;overflow-x:auto;">$2</pre>')
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}
</script>

<style scoped>
.ai-panel {
  display: flex;
  border-left: 1px solid #e4e7ed;
  background: #fff;
  transition: width 0.2s;
}

.ai-panel.collapsed {
  width: 48px !important;
  min-width: 48px !important;
}

.ai-toggle {
  width: 48px;
  min-width: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  cursor: pointer;
  background: #fafafa;
  border-left: 1px solid #e4e7ed;
}

.ai-toggle:hover {
  background: #f0f5ff;
  color: #409eff;
}

.ai-content {
  width: 360px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
}

.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.ai-welcome {
  padding: 16px 8px;
  color: #999;
}

.ai-message {
  margin-bottom: 12px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
}

.ai-message.user {
  background: #ecf5ff;
  margin-left: 20px;
}

.ai-message.assistant {
  background: #f5f7fa;
  margin-right: 20px;
}

.msg-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
  font-weight: 500;
}

.msg-content {
  word-break: break-all;
}

.typing-dot {
  animation: blink 1.4s infinite;
  font-size: 24px;
  line-height: 0;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0% { opacity: 0.2; } 50% { opacity: 1; } 100% { opacity: 0.2; } }

.ai-input {
  padding: 12px;
  border-top: 1px solid #e4e7ed;
}
</style>
```

- [ ] **Step 4: Integrate AIPanel into App.vue**

修改 `D:\APM\frontend\src\App.vue`:

```vue
<template>
  <div class="app-container">
    <div class="sidebar">
      <!-- existing sidebar -->
      <div style="padding: 16px; border-bottom: 1px solid #e4e7ed;">
        <h2 style="font-size: 18px; margin: 0;">
          <el-icon style="vertical-align: middle;"><Menu /></el-icon>
          CCB 项目管理系统
        </h2>
      </div>
      <el-menu router :default-active="route.path" style="border-right: none;">
        <el-menu-item index="/">
          <el-icon><List /></el-icon>
          <span>项目列表</span>
        </el-menu-item>
        <el-menu-item index="/projects/new">
          <el-icon><Plus /></el-icon>
          <span>新建项目</span>
        </el-menu-item>
      </el-menu>
    </div>
    <div class="main-content">
      <router-view />
    </div>
    <!-- AI Panel only visible on project detail page -->
    <AIPanel v-if="isProjectDetail" :project-id="projectId" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AIPanel from '@/components/AIPanel.vue'

const route = useRoute()

const isProjectDetail = computed(() => {
  return route.name === 'project-detail'
})

const projectId = computed(() => {
  return Number(route.params.id)
})
</script>
```

调整 `.main-content` 样式（不要 `width: 100%`）：

```css
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fff;
  min-width: 0; /* prevent overflow */
}
```

- [ ] **Step 5: Verify**

```bash
cd D:\APM\frontend
npx vue-tsc --noEmit 2>&1 | head -20
```

Expected: no type errors.

```bash
npm run dev
```

Open `http://localhost:5173/projects/1` → AI panel on right side. Test:
- Panel can collapse/expand
- Welcome messages shown
- Type question → see response (mock mode without API key)
- Works without ANTHROPIC_API_KEY (mock mode)

---

## 自审查

- Spec 覆盖：Phase 2 spec 中的 AI 面板、进度查询、计划调整（含确认流程）、操作指引均已覆盖。文档生成（generate_doc）作为 action_type 预留但未实现完整流程。
- 无占位符
- 类型一致

## 执行

```bash
# 需要 ANTHROPIC_API_KEY 环境变量以启用真实 AI
export ANTHROPIC_API_KEY=sk-ant-...
```
