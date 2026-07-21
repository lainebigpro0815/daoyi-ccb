<template>
  <div v-loading="store.loading">
    <div v-if="project" style="max-width: 1100px; margin: 0 auto;">
      <!-- 项目头部 -->
      <div class="page-header">
        <div>
          <el-button link @click="$router.push('/')" style="margin-bottom: 4px; font-size: 13px; padding: 0;">
            <el-icon><ArrowLeft /></el-icon> 返回
          </el-button>
          <h1 style="margin: 2px 0 4px;">{{ project.name }}</h1>
          <div class="project-meta">
            客户：<el-input v-model="editCustomer" size="small" style="width: 130px;" @blur="saveProject" />
            <el-divider direction="vertical" />
            阶段：<el-select v-model="editStage" size="small" style="width: 80px;" @change="saveProject">
              <el-option label="售前" value="presale" />
              <el-option label="已签约" value="signed" />
              <el-option label="执行中" value="executing" />
              <el-option label="已交付" value="delivered" />
              <el-option label="已归档" value="archived" />
            </el-select>
            <el-divider direction="vertical" />
            启动：<el-date-picker v-model="editStartDate" type="date" size="small" value-format="YYYY-MM-DD" style="width: 120px;" @change="saveProject" />
            <span v-if="project.planned_end_date" style="margin-left: 4px;">→ {{ project.planned_end_date }}</span>
          </div>
        </div>
        <div class="header-actions">
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button value="table">表格</el-radio-button>
            <el-radio-button value="card">卡片</el-radio-button>
            <el-radio-button value="kanban">看板</el-radio-button>
          </el-radio-group>
          <el-button size="small" @click="exportExcel" :loading="exporting">
            <el-icon><Download /></el-icon> Excel
          </el-button>
        </div>
      </div>

      <!-- 进度概览 -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 32px; flex-wrap: wrap;">
          <div class="stat-item"><div class="stat-label">阶段</div><div class="stat-value">{{ project.phases.length }}</div></div>
          <div class="stat-item"><div class="stat-label">任务</div><div class="stat-value">{{ totalTasks }}</div></div>
          <div class="stat-item"><div class="stat-label">已完成</div><div class="stat-value" style="color: #00b42a;">{{ completedTasks }}</div></div>
          <div style="flex: 1; min-width: 160px;"><el-progress :percentage="overallProgress" :stroke-width="14" /></div>
        </div>
      </el-card>

      <!-- Tab -->
      <el-tabs v-model="activeTab" type="border-card" style="margin-bottom: 16px;">
        <el-tab-pane label="任务计划" name="plan" />
        <el-tab-pane label="风险" name="risk" />
        <el-tab-pane label="问题" name="issue" />
        <el-tab-pane label="里程碑" name="milestone" />
        <el-tab-pane label="验收范围" name="acceptance" />
        <el-tab-pane label="培训计划" name="training" />
        <el-tab-pane label="干系人" name="stakeholder" />
        <el-tab-pane label="文档" name="doc" />
      </el-tabs>

      <!-- ========== 任务计划 ========== -->
      <div v-show="activeTab === 'plan'">
        <div style="margin-bottom: 8px;">
          <el-button size="small" type="primary" @click="addTask" v-if="viewMode === 'table'">+ 新任务</el-button>
        </div>
        <div v-show="viewMode === 'card'">
          <PhaseCard v-for="phase in project.phases" :key="phase.id" :phase="phase" :project-id="project.id" @refresh="refreshProject" />
        </div>
        <div v-show="viewMode === 'table'">
          <div v-if="flatTasks.length === 0" style="color: #999; text-align: center; padding: 40px;">暂无任务</div>
          <el-table v-else :data="flatTasks" :span-method="spanMethod" border stripe size="small" max-height="calc(100vh - 420px)" style="width: 100%;" highlight-current-row>
            <el-table-column label="#" width="55" prop="display.task_number" />
            <el-table-column label="任务名称" min-width="200">
              <template #default="{ row }">
                <div v-if="row._isPhase" class="phase-row">{{ row.display.name }}</div>
                <el-input v-else v-model="row.display.name" size="small" @blur="saveField(row, 'name')" placeholder="名称" />
              </template>
            </el-table-column>
            <el-table-column label="负责人" width="100">
              <template #default="{ row }"><el-input v-if="!row._isPhase" v-model="row.display.assignee" size="small" @blur="saveField(row, 'assignee')" placeholder="-" /></template>
            </el-table-column>
            <el-table-column label="开始" width="105">
              <template #default="{ row }"><el-date-picker v-if="!row._isPhase" v-model="row.display.planned_start" type="date" size="small" value-format="YYYY-MM-DD" style="width: 100%;" @change="saveField(row, 'planned_start')" /></template>
            </el-table-column>
            <el-table-column label="结束" width="105">
              <template #default="{ row }"><el-date-picker v-if="!row._isPhase" v-model="row.display.planned_end" type="date" size="small" value-format="YYYY-MM-DD" style="width: 100%;" @change="saveField(row, 'planned_end')" /></template>
            </el-table-column>
            <el-table-column label="进度" width="65">
              <template #default="{ row }"><el-progress v-if="!row._isPhase" :percentage="row.display.progress || 0" :width="48" :stroke-width="6" /></template>
            </el-table-column>
            <el-table-column label="状态" width="75">
              <template #default="{ row }"><el-select v-if="!row._isPhase" :model-value="row.display.status" size="small" @change="(v:string) => saveStatus(row, v)" style="width: 100%;">
                <el-option label="待开始" value="pending" /><el-option label="进行中" value="in_progress" /><el-option label="已完成" value="completed" /><el-option label="阻塞" value="blocked" />
              </el-select></template>
            </el-table-column>
            <el-table-column label="操作" width="55" fixed="right">
              <template #default="{ row }">
                <el-dropdown v-if="!row._isPhase" trigger="click">
                  <el-button link size="small"><el-icon><MoreFilled /></el-icon></el-button>
                  <template #dropdown>
                    <el-dropdown-item @click="quickComplete(row)" v-if="row.display.status !== 'completed'">标记完成</el-dropdown-item>
                    <el-dropdown-item @click="quickUncomplete(row)" v-if="row.display.status === 'completed'">重开</el-dropdown-item>
                    <el-dropdown-item divided @click="deleteTask(row)">删除</el-dropdown-item>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- ===== 看板 ====== -->
      <div v-show="activeTab === 'plan' && viewMode === 'kanban'" class="kanban-board">
        <div class="kanban-col" v-for="col in kanbanColumns" :key="col.status">
          <div class="kanban-header">
            <el-tag :type="col.tag">{{ col.label }}</el-tag>
            <span style="font-size: 12px; color: #999;">{{ tasksByStatus(col.status).length }}</span>
          </div>
          <div class="kanban-list" @dragover.prevent @drop="onDrop($event, col.status)">
            <div v-for="t in tasksByStatus(col.status)" :key="t.id" class="kanban-card" draggable="true" @dragstart="onDragStart($event, t)">
              <div style="font-weight: 500; font-size: 13px;">{{ t.name }}</div>
              <div style="font-size: 12px; color: #999; margin-top: 4px;">{{ t.assignee || '未分配' }} · {{ t.planned_end || '无期限' }}</div>
              <el-popover trigger="click" :width="200">
                <template #reference><el-tag :type="col.tag" size="small" style="margin-top: 4px; cursor: pointer;">{{ col.label }}</el-tag></template>
                <div style="display: flex; flex-direction: column; gap: 4px;">
                  <el-button size="small" @click="quickStatus(t, 'pending')" :type="t.status==='pending'?'primary':''">待开始</el-button>
                  <el-button size="small" @click="quickStatus(t, 'in_progress')" :type="t.status==='in_progress'?'primary':''">进行中</el-button>
                  <el-button size="small" @click="quickStatus(t, 'completed')" :type="t.status==='completed'?'primary':''">已完成</el-button>
                  <el-button size="small" @click="quickStatus(t, 'blocked')" :type="t.status==='blocked'?'primary':''">阻塞</el-button>
                </div>
              </el-popover>
            </div>
          </div>
        </div>
      </div>

      <!-- ========== 风险 ========== -->
      <div v-show="activeTab === 'risk'">
        <div style="margin-bottom: 8px;">
          <el-button size="small" type="primary" @click="addRisk">+ 新增风险</el-button>
        </div>
        <div v-show="viewMode === 'card'">
          <div style="display: flex; flex-wrap: wrap; gap: 12px;">
            <el-card v-for="r in risks" :key="r.id" shadow="hover" style="width: calc(50% - 6px);">
              <div style="display: flex; justify-content: space-between;">
                <el-tag :type="r.level === '高' ? 'danger' : r.level === '中' ? 'warning' : 'info'" size="small">{{ r.level }}</el-tag>
                <el-switch v-model="r.status" active-value="closed" inactive-value="open" size="small"
                           style="--el-switch-on-color: #67c23a;" @change="saveRisk(r)" />
              </div>
              <div style="font-weight: 500; margin: 8px 0;">{{ r.description || '未描述' }}</div>
              <div style="font-size: 12px; color: #666;">{{ r.category }} · {{ r.owner }} · {{ r.mitigation ? '有应对' : '无应对' }}</div>
              <el-button link size="small" type="danger" style="margin-top: 4px;" @click="deleteRisk(r)">删除</el-button>
            </el-card>
          </div>
        </div>
        <div v-show="viewMode === 'table'">
          <el-table :data="risks" border stripe size="small" style="width: 100%;">
            <el-table-column label="级别" width="55"><template #default="{ row }"><el-select v-model="row.level" size="small" @change="saveRisk(row)">
              <el-option label="高" value="高" /><el-option label="中" value="中" /><el-option label="低" value="低" />
            </el-select></template></el-table-column>
            <el-table-column label="风险描述" min-width="160"><template #default="{ row }"><el-input v-model="row.description" size="small" @blur="saveRisk(row)" /></template></el-table-column>
            <el-table-column label="类别" width="80"><template #default="{ row }"><el-input v-model="row.category" size="small" @blur="saveRisk(row)" /></template></el-table-column>
            <el-table-column label="影响" width="65"><template #default="{ row }"><el-input v-model="row.impact" size="small" @blur="saveRisk(row)" /></template></el-table-column>
            <el-table-column label="概率" width="60"><template #default="{ row }"><el-input v-model="row.probability" size="small" @blur="saveRisk(row)" /></template></el-table-column>
            <el-table-column label="应对措施" min-width="160"><template #default="{ row }"><el-input v-model="row.mitigation" size="small" @blur="saveRisk(row)" /></template></el-table-column>
            <el-table-column label="负责人" width="70"><template #default="{ row }"><el-input v-model="row.owner" size="small" @blur="saveRisk(row)" /></template></el-table-column>
            <el-table-column label="关闭" width="50"><template #default="{ row }"><el-switch v-model="row.status" active-value="closed" inactive-value="open" size="small" style="--el-switch-on-color: #67c23a;" @change="saveRisk(r)" /></template></el-table-column>
            <el-table-column label="操作" width="35"><template #default="{ row }"><el-button link size="small" type="danger" @click="deleteRisk(row)">x</el-button></template></el-table-column>
          </el-table>
        </div>
      </div>

      <!-- ========== 问题 ========== -->
      <div v-show="activeTab === 'issue'">
        <div style="margin-bottom: 8px;">
          <el-button size="small" type="primary" @click="addIssue">+ 新增问题</el-button>
        </div>
        <div v-show="viewMode === 'card'">
          <div style="display: flex; flex-wrap: wrap; gap: 12px;">
            <el-card v-for="i in issues" :key="i.id" shadow="hover" style="width: calc(50% - 6px);">
              <div style="display: flex; justify-content: space-between; gap: 8px;">
                <el-tag :type="i.severity === '严重' ? 'danger' : i.severity === '一般' ? 'warning' : 'info'" size="small">{{ i.severity }}</el-tag>
                <el-tag :type="i.status === 'closed' ? 'info' : i.status === 'resolved' ? 'success' : i.status === 'in_progress' ? 'warning' : 'danger'" size="small">
                  {{ {open:'待处理',in_progress:'处理中',resolved:'已解决',closed:'关闭'}[i.status] || i.status }}
                </el-tag>
              </div>
              <div style="font-weight: 500; margin: 8px 0;">{{ i.description || '未描述' }}</div>
              <div style="font-size: 12px; color: #666;">{{ i.module }} · {{ i.assignee }} · {{ i.priority }}优先级</div>
              <el-button link size="small" type="danger" style="margin-top: 4px;" @click="deleteIssue(i)">删除</el-button>
            </el-card>
          </div>
        </div>
        <div v-show="viewMode === 'table'">
          <el-table :data="issues" border stripe size="small" style="width: 100%;">
            <el-table-column label="严重" width="55"><template #default="{ row }"><el-select v-model="row.severity" size="small" @change="saveIssue(row)">
              <el-option label="严重" value="严重" /><el-option label="一般" value="一般" /><el-option label="轻微" value="轻微" />
            </el-select></template></el-table-column>
            <el-table-column label="问题描述" min-width="180"><template #default="{ row }"><el-input v-model="row.description" size="small" @blur="saveIssue(row)" /></template></el-table-column>
            <el-table-column label="模块" width="80"><template #default="{ row }"><el-input v-model="row.module" size="small" @blur="saveIssue(row)" /></template></el-table-column>
            <el-table-column label="优先级" width="65"><template #default="{ row }"><el-select v-model="row.priority" size="small" @change="saveIssue(row)">
              <el-option label="高" value="高" /><el-option label="中" value="中" /><el-option label="低" value="低" />
            </el-select></template></el-table-column>
            <el-table-column label="处理人" width="70"><template #default="{ row }"><el-input v-model="row.assignee" size="small" @blur="saveIssue(row)" /></template></el-table-column>
            <el-table-column label="状态" width="80"><template #default="{ row }"><el-select v-model="row.status" size="small" @change="saveIssue(row)">
              <el-option label="待处理" value="open" /><el-option label="处理中" value="in_progress" /><el-option label="已解决" value="resolved" /><el-option label="关闭" value="closed" />
            </el-select></template></el-table-column>
            <el-table-column label="解决方案" min-width="140"><template #default="{ row }"><el-input v-model="row.resolution" size="small" @blur="saveIssue(row)" /></template></el-table-column>
            <el-table-column label="操作" width="35"><template #default="{ row }"><el-button link size="small" type="danger" @click="deleteIssue(row)">x</el-button></template></el-table-column>
          </el-table>
        </div>
      </div>

      <!-- ===== 里程碑 ====== -->
      <div v-show="activeTab === 'milestone'">
        <div style="margin-bottom: 8px;"><el-button size="small" type="primary" @click="addMilestone">+ 新增里程碑</el-button></div>
        <div v-show="viewMode === 'card'" style="display: flex; flex-wrap: wrap; gap: 12px;">
          <el-card v-for="m in milestones" :key="m.id" shadow="hover" style="width: calc(33.33% - 8px);">
            <div style="font-weight: 600;">{{ m.name || '未命名' }}</div>
            <div style="font-size: 12px; color: #666; margin: 4px 0;">{{ m.planned_date }} → {{ m.actual_date || '未完成' }}</div>
            <el-tag :type="m.status === 'completed' ? 'success' : m.status === 'delayed' ? 'danger' : 'info'" size="small">
              {{ {pending:'待完成',completed:'已完成',delayed:'已延期'}[m.status] || m.status }}
            </el-tag>
          </el-card>
        </div>
        <div v-show="viewMode === 'table'">
          <el-table :data="milestones" border stripe size="small" style="width: 100%;">
            <el-table-column label="里程碑" min-width="160"><template #default="{ row }"><el-input v-model="row.name" size="small" @blur="saveMilestone(row)" /></template></el-table-column>
            <el-table-column label="计划日期" width="110"><template #default="{ row }"><el-input v-model="row.planned_date" size="small" placeholder="YYYY-MM-DD" @blur="saveMilestone(row)" /></template></el-table-column>
            <el-table-column label="实际日期" width="110"><template #default="{ row }"><el-input v-model="row.actual_date" size="small" placeholder="YYYY-MM-DD" @blur="saveMilestone(row)" /></template></el-table-column>
            <el-table-column label="状态" width="80"><template #default="{ row }"><el-select v-model="row.status" size="small" @change="saveMilestone(row)">
              <el-option label="待完成" value="pending" /><el-option label="已完成" value="completed" /><el-option label="已延期" value="delayed" />
            </el-select></template></el-table-column>
            <el-table-column label="说明" min-width="160"><template #default="{ row }"><el-input v-model="row.description" size="small" @blur="saveMilestone(row)" /></template></el-table-column>
            <el-table-column label="操作" width="35"><template #default="{ row }"><el-button link size="small" type="danger" @click="deleteMilestone(row)">x</el-button></template></el-table-column>
          </el-table>
        </div>
      </div>

      <!-- ===== 验收范围 ====== -->
      <div v-show="activeTab === 'acceptance'">
        <div style="margin-bottom: 8px;"><el-button size="small" type="primary" @click="addAcceptance">+ 新增验收项</el-button></div>
        <div v-show="viewMode === 'card'" style="display: flex; flex-wrap: wrap; gap: 12px;">
          <el-card v-for="a in acceptanceItems" :key="a.id" shadow="hover" style="width: calc(50% - 6px);">
            <div style="display: flex; justify-content: space-between;">
              <span style="font-weight: 600;">{{ a.item || '未命名' }}</span>
              <el-tag :type="a.status === 'passed' ? 'success' : a.status === 'failed' ? 'danger' : 'info'" size="small">
                {{ {pending:'待验收',passed:'通过',failed:'未通过'}[a.status] || a.status }}
              </el-tag>
            </div>
            <div style="font-size: 12px; color: #666; margin: 4px 0;">标准：{{ a.standard || '—' }}</div>
            <div style="font-size: 12px;">结果：{{ a.result || '—' }}</div>
          </el-card>
        </div>
        <div v-show="viewMode === 'table'">
          <el-table :data="acceptanceItems" border stripe size="small" style="width: 100%;">
            <el-table-column label="验收项" min-width="160"><template #default="{ row }"><el-input v-model="row.item" size="small" @blur="saveAcceptance(row)" /></template></el-table-column>
            <el-table-column label="验收标准" min-width="200"><template #default="{ row }"><el-input v-model="row.standard" size="small" @blur="saveAcceptance(row)" /></template></el-table-column>
            <el-table-column label="状态" width="80"><template #default="{ row }"><el-select v-model="row.status" size="small" @change="saveAcceptance(row)">
              <el-option label="待验收" value="pending" /><el-option label="通过" value="passed" /><el-option label="未通过" value="failed" />
            </el-select></template></el-table-column>
            <el-table-column label="验收结果" min-width="160"><template #default="{ row }"><el-input v-model="row.result" size="small" @blur="saveAcceptance(row)" /></template></el-table-column>
            <el-table-column label="操作" width="35"><template #default="{ row }"><el-button link size="small" type="danger" @click="deleteAcceptance(row)">x</el-button></template></el-table-column>
          </el-table>
        </div>
      </div>

      <!-- ===== 培训计划 ====== -->
      <div v-show="activeTab === 'training'">
        <div style="margin-bottom: 8px;"><el-button size="small" type="primary" @click="addTraining">+ 新增培训</el-button></div>
        <div v-show="viewMode === 'card'" style="display: flex; flex-wrap: wrap; gap: 12px;">
          <el-card v-for="t in trainingItems" :key="t.id" shadow="hover" style="width: calc(50% - 6px);">
            <div style="font-weight: 600;">{{ t.content || '未命名' }}</div>
            <div style="font-size: 12px; color: #666; margin: 4px 0;">对象：{{ t.target || '—' }} | 计划：{{ t.planned_date || '—' }}</div>
            <el-tag :type="t.status === 'completed' ? 'success' : 'info'" size="small">{{ t.status === 'completed' ? '已完成' : '待培训' }}</el-tag>
          </el-card>
        </div>
        <div v-show="viewMode === 'table'">
          <el-table :data="trainingItems" border stripe size="small" style="width: 100%;">
            <el-table-column label="培训内容" min-width="180"><template #default="{ row }"><el-input v-model="row.content" size="small" @blur="saveTraining(row)" /></template></el-table-column>
            <el-table-column label="培训对象" width="120"><template #default="{ row }"><el-input v-model="row.target" size="small" @blur="saveTraining(row)" /></template></el-table-column>
            <el-table-column label="计划日期" width="110"><template #default="{ row }"><el-input v-model="row.planned_date" size="small" placeholder="YYYY-MM-DD" @blur="saveTraining(row)" /></template></el-table-column>
            <el-table-column label="实际日期" width="110"><template #default="{ row }"><el-input v-model="row.actual_date" size="small" placeholder="YYYY-MM-DD" @blur="saveTraining(row)" /></template></el-table-column>
            <el-table-column label="状态" width="70"><template #default="{ row }"><el-switch v-model="row.status" active-value="completed" inactive-value="pending" @change="saveTraining(row)" style="--el-switch-on-color:#67c23a;" /></template></el-table-column>
            <el-table-column label="备注" min-width="140"><template #default="{ row }"><el-input v-model="row.remark" size="small" @blur="saveTraining(row)" /></template></el-table-column>
            <el-table-column label="操作" width="35"><template #default="{ row }"><el-button link size="small" type="danger" @click="deleteTraining(row)">x</el-button></template></el-table-column>
          </el-table>
        </div>
      </div>

      <!-- ========== 干系人 ========== -->
      <div v-show="activeTab === 'stakeholder'">
        <div style="margin-bottom: 8px;">
          <el-button size="small" type="primary" @click="addStakeholder">+ 添加</el-button>
        </div>
        <div v-show="viewMode === 'card'">
          <div style="display: flex; flex-wrap: wrap; gap: 12px;">
            <el-card v-for="s in stakeholders" :key="s.id" shadow="hover" style="width: calc(33.33% - 8px);">
              <div style="display: flex; align-items: center; gap: 12px;">
                <el-avatar :size="40">{{ s.name?.[0] || '?' }}</el-avatar>
                <div>
                  <div style="font-weight: 500;">{{ s.name || '未命名' }}</div>
                  <div style="font-size: 12px; color: #666;">{{ s.role }} · {{ s.company }}</div>
                </div>
              </div>
              <div style="font-size: 12px; color: #999; margin-top: 8px;">{{ s.phone }} {{ s.email }}</div>
              <el-button link size="small" type="danger" style="margin-top: 4px;" @click="deleteStakeholder(s)">删除</el-button>
            </el-card>
          </div>
        </div>
        <div v-show="viewMode === 'table'">
          <el-table :data="stakeholders" border stripe size="small" style="width: 100%;">
            <el-table-column label="分组" width="90"><template #default="{ row }"><el-select v-model="row.group_name" size="small" @change="saveStakeholder(row)">
              <el-option label="客户联系人" value="客户联系人" /><el-option label="内部联系人" value="内部联系人" />
            </el-select></template></el-table-column>
            <el-table-column label="姓名" width="80"><template #default="{ row }"><el-input v-model="row.name" size="small" @blur="saveStakeholder(row)" /></template></el-table-column>
            <el-table-column label="公司" width="130"><template #default="{ row }"><el-input v-model="row.company" size="small" @blur="saveStakeholder(row)" /></template></el-table-column>
            <el-table-column label="职位" width="110"><template #default="{ row }"><el-input v-model="row.role" size="small" @blur="saveStakeholder(row)" /></template></el-table-column>
            <el-table-column label="电话" width="110"><template #default="{ row }"><el-input v-model="row.phone" size="small" @blur="saveStakeholder(row)" /></template></el-table-column>
            <el-table-column label="邮箱" min-width="150"><template #default="{ row }"><el-input v-model="row.email" size="small" @blur="saveStakeholder(row)" /></template></el-table-column>
            <el-table-column label="操作" width="35"><template #default="{ row }"><el-button link size="small" type="danger" @click="deleteStakeholder(row)">x</el-button></template></el-table-column>
          </el-table>
        </div>
      </div>

      <!-- ========== 文档 ========== -->
      <div v-show="activeTab === 'doc'" class="doc-tab">
        <div style="display: flex; gap: 0; height: calc(100vh - 420px); margin: -16px; overflow: hidden;">
          <div class="doc-tree-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; border-bottom: 1px solid #f0f0f0;">
              <span style="font-weight: 600; font-size: 14px;">文档目录</span>
              <div style="display: flex; gap: 4px;">
                <el-button size="small" circle @click="downloadPackage" :loading="packaging"><el-icon><Download /></el-icon></el-button>
                <el-upload :action="`/api/projects/${projectId}/docs/upload`" :show-file-list="false" :on-success="loadDocTree">
                  <el-button size="small" circle><el-icon><Plus /></el-icon></el-button>
                </el-upload>
              </div>
            </div>
            <el-tree :data="docTree" :props="{ children: 'children', label: 'label' }" node-key="id" :highlight-current="true" @node-click="onDocClick" default-expand-all style="padding: 4px 0;">
              <template #default="{ data }">
                <span style="font-size: 13px; display: flex; align-items: center; gap: 4px;">
                  <el-icon v-if="data.type === 'folder'" size="14"><Folder /></el-icon>
                  <el-icon v-else-if="data.file_type === 'word'" size="14" style="color:#2b579a;"><Tickets /></el-icon>
                  <el-icon v-else-if="data.file_type === 'excel'" size="14" style="color:#217346;"><Grid /></el-icon>
                  <el-icon v-else-if="data.file_type === 'ppt'" size="14" style="color:#d04525;"><Monitor /></el-icon>
                  <el-icon v-else size="14"><Document /></el-icon>
                  {{ data.label }}
                </span>
              </template>
            </el-tree>
          </div>
          <div style="flex: 1; display: flex; flex-direction: column; overflow-y: auto;">
            <div v-if="!currentDoc" style="color: #999; text-align: center; margin-top: 80px;">
              <el-icon size="40"><FolderOpened /></el-icon><p style="margin-top: 8px;">选择文档查看</p>
            </div>
            <template v-else>
              <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #f0f0f0;">
                <div><span style="font-weight: 600;">{{ currentDoc.name }}</span><el-tag size="small" style="margin-left: 6px;">{{ currentDoc.ext }}</el-tag></div>
                <div style="display: flex; gap: 8px;">
                  <el-button size="small" @click="downloadDoc">下载</el-button>
                  <template v-if="currentDoc.ext === '.md'">
                    <el-switch v-model="docEditing" active-text="编辑" inactive-text="预览" size="small" />
                    <el-button v-if="docEditing" type="primary" size="small" @click="saveDoc">保存</el-button>
                  </template>
                </div>
              </div>
              <div style="padding: 20px; overflow-y: auto; flex: 1;">
                <template v-if="currentDoc.ext === '.md'">
                  <div v-if="!docEditing" class="markdown-body" v-html="renderedHtml"></div>
                  <el-input v-else v-model="docContent" type="textarea" :rows="25" />
                </template>
                <div v-else-if="currentDoc.html" class="office-preview" v-html="currentDoc.html"></div>
                <div v-else style="color: #999;">无法预览，请下载</div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/stores/project'
import { updateTask } from '@/api/tasks'
import api from '@/api'
import PhaseCard from '@/components/PhaseCard.vue'

const route = useRoute()
const store = useProjectStore()
const exporting = ref(false)
const projectId = computed(() => Number(route.params.id))
const project = computed(() => store.currentProject)

// View mode & active tab
const viewMode = ref(localStorage.getItem('ccb_view_mode') || 'table')
const activeTab = ref('plan')
watch(viewMode, (v) => localStorage.setItem('ccb_view_mode', v))

// Project editable fields
const editCustomer = ref(''); const editStage = ref(''); const editStartDate = ref('')
watch(project, (p) => { if (p) { editCustomer.value = p.customer_name; editStage.value = p.stage; editStartDate.value = p.start_date } })

// Data
const stakeholders = ref<any[]>([])
const risks = ref<any[]>([])
const issues = ref<any[]>([])
const docTree = ref<any[]>([])
const currentDoc = ref<any>(null)
const milestones = ref<any[]>([])
const acceptanceItems = ref<any[]>([])
const trainingItems = ref<any[]>([])
const packaging = ref(false)
const docContent = ref('')
const docEditing = ref(false)

const totalTasks = computed(() => project.value?.phases.reduce((s: number, p: any) => s + p.tasks.length, 0) || 0)
const completedTasks = computed(() => project.value?.phases.reduce((s: number, p: any) => s + p.tasks.filter((t: any) => t.status === 'completed').length, 0) || 0)
const overallProgress = computed(() => totalTasks.value ? Math.round(completedTasks.value / totalTasks.value * 100) : 0)

// Kanban
const kanbanColumns = [
  { status: 'pending', label: '待开始', tag: 'info' },
  { status: 'in_progress', label: '进行中', tag: 'warning' },
  { status: 'completed', label: '已完成', tag: 'success' },
  { status: 'blocked', label: '阻塞', tag: 'danger' },
]
const draggedTask = ref<any>(null)
function onDragStart(e: any, task: any) { draggedTask.value = task; e.dataTransfer.effectAllowed = 'move' }
async function onDrop(e: any, status: string) {
  if (!draggedTask.value || draggedTask.value.status === status) return
  await updateTask(projectId.value, draggedTask.value.id, { status, progress: status === 'completed' ? 100 : 0 })
  draggedTask.value = null; store.fetchProject(projectId.value)
}
async function quickStatus(task: any, status: string) {
  await updateTask(projectId.value, task.id, { status, progress: status === 'completed' ? 100 : 0 })
  store.fetchProject(projectId.value)
}
function tasksByStatus(status: string) {
  if (!project.value) return []
  const all: any[] = []
  for (const p of project.value.phases) { for (const t of p.tasks) all.push(t) }
  return all.filter(t => t.status === status)
}

// Flat tasks for table
const flatTasks = computed(() => {
  if (!project.value) return []
  const rows: any[] = []
  for (const p of project.value.phases) {
    rows.push({ _isPhase: true, display: { name: `阶段${p.phase_number}：${p.name}` } })
    for (const t of p.tasks) rows.push({ _isPhase: false, _taskId: t.id, display: { name: t.name, task_number: t.task_number, assignee: t.assignee || '', planned_start: t.planned_start, planned_end: t.planned_end, progress: t.progress, status: t.status } })
  }
  return rows
})

const renderedHtml = computed(() => {
  let text = docContent.value; if (!text) return ''
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.*$)/gm, '<h3>$1</h3>').replace(/^## (.*$)/gm, '<h2>$1</h2>').replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')
})

function spanMethod({ rowIndex }: any) { return flatTasks.value[rowIndex]?._isPhase ? { rowspan: 1, colspan: 0 } : { rowspan: 1, colspan: 1 } }

// ---- CRUD ----
async function saveProject() { await api.put(`/projects/${projectId.value}`, { customer_name: editCustomer.value, stage: editStage.value, start_date: editStartDate.value }) }
async function saveField(row: any, f: string) { await updateTask(projectId.value, row._taskId, { [f]: row.display[f] || '' }) }
async function saveStatus(row: any, s: string) { await updateTask(projectId.value, row._taskId, { status: s, progress: s === 'completed' ? 100 : 0 }); store.fetchProject(projectId.value) }
async function quickComplete(row: any) { await updateTask(projectId.value, row._taskId, { status: 'completed', progress: 100 }); store.fetchProject(projectId.value) }
async function quickUncomplete(row: any) { await updateTask(projectId.value, row._taskId, { status: 'pending', progress: 0 }); store.fetchProject(projectId.value) }
async function addTask() { await api.post(`/projects/${projectId.value}/tasks`); store.fetchProject(projectId.value) }
async function deleteTask(row: any) { await api.delete(`/projects/${projectId.value}/tasks/${row._taskId}`); store.fetchProject(projectId.value) }
function refreshProject() { store.fetchProject(projectId.value); loadStakeholders(); loadRisks(); loadIssues(); }

// Stakeholders
async function loadStakeholders() { const r = await api.get(`/projects/${projectId.value}/stakeholders`); stakeholders.value = r.data.items || [] }
async function addStakeholder() { await api.post(`/projects/${projectId.value}/stakeholders`, { name: '新联系人' }); loadStakeholders() }
async function saveStakeholder(row: any) { await api.put(`/projects/${projectId.value}/stakeholders/${row.id}`, row) }
async function deleteStakeholder(row: any) { await api.delete(`/projects/${projectId.value}/stakeholders/${row.id}`); loadStakeholders() }
// Risks
async function loadRisks() { const r = await api.get(`/projects/${projectId.value}/risks`); risks.value = r.data.items || [] }
async function addRisk() { await api.post(`/projects/${projectId.value}/risks`, { description: '新风险' }); loadRisks() }
async function saveRisk(row: any) { await api.put(`/projects/${projectId.value}/risks/${row.id}`, row) }
async function deleteRisk(row: any) { await api.delete(`/projects/${projectId.value}/risks/${row.id}`); loadRisks() }
// Issues
async function loadIssues() { const r = await api.get(`/projects/${projectId.value}/issues`); issues.value = r.data.items || [] }
async function addIssue() { await api.post(`/projects/${projectId.value}/issues`, { description: '新问题' }); loadIssues() }
async function saveIssue(row: any) { await api.put(`/projects/${projectId.value}/issues/${row.id}`, row) }
async function deleteIssue(row: any) { await api.delete(`/projects/${projectId.value}/issues/${row.id}`); loadIssues() }
// Docs
async function loadMilestones() { const r = await api.get(`/projects/${projectId.value}/milestones`); milestones.value = r.data.items || [] }
async function addMilestone() { await api.post(`/projects/${projectId.value}/milestones`, { name: '新里程碑' }); loadMilestones() }
async function saveMilestone(row: any) { await api.put(`/projects/${projectId.value}/milestones/${row.id}`, row) }
async function deleteMilestone(row: any) { await api.delete(`/projects/${projectId.value}/milestones/${row.id}`); loadMilestones() }
async function loadAcceptance() { const r = await api.get(`/projects/${projectId.value}/acceptance`); acceptanceItems.value = r.data.items || [] }
async function addAcceptance() { await api.post(`/projects/${projectId.value}/acceptance`, { item: '新验收项' }); loadAcceptance() }
async function saveAcceptance(row: any) { await api.put(`/projects/${projectId.value}/acceptance/${row.id}`, row) }
async function deleteAcceptance(row: any) { await api.delete(`/projects/${projectId.value}/acceptance/${row.id}`); loadAcceptance() }
async function loadTraining() { const r = await api.get(`/projects/${projectId.value}/training`); trainingItems.value = r.data.items || [] }
async function addTraining() { await api.post(`/projects/${projectId.value}/training`, { content: '新培训' }); loadTraining() }
async function saveTraining(row: any) { await api.put(`/projects/${projectId.value}/training/${row.id}`, row) }
async function deleteTraining(row: any) { await api.delete(`/projects/${projectId.value}/training/${row.id}`); loadTraining() }
async function downloadPackage() {
  packaging.value = true
  try { const r = await api.get(`/projects/${projectId.value}/export/package`, { responseType: 'blob' }); const url = window.URL.createObjectURL(new Blob([r.data])); const a = document.createElement('a'); a.href = url; a.download = `项目交付包.zip`; document.body.appendChild(a); a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(url) }
  catch { ElMessage.error('打包失败') }
  finally { packaging.value = false }
}
async function loadDocTree() { const r = await api.get(`/projects/${projectId.value}/docs/tree`); docTree.value = r.data.items || [] }
async function onDocClick(data: any) {
  if (data.type !== 'file') return
  const r = await api.get(`/projects/${projectId.value}/docs/read`, { params: { path: data.path } })
  currentDoc.value = r.data; docContent.value = r.data.content || ''; docEditing.value = false
}
async function saveDoc() { await api.post(`/projects/${projectId.value}/docs/save`, { path: currentDoc.value.path, content: docContent.value }); ElMessage.success('已保存'); docEditing.value = false }
function downloadDoc() { window.open(`/api/projects/${projectId.value}/docs/download?path=${encodeURIComponent(currentDoc.value.path)}`) }
// Export
async function exportExcel() {
  exporting.value = true
  try { const r = await api.get(`/projects/${projectId.value}/export/excel`, { responseType: 'blob' }); const url = window.URL.createObjectURL(new Blob([r.data])); const a = document.createElement('a'); a.href = url; a.download = `project_${projectId.value}.xlsx`; document.body.appendChild(a); a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(url) }
  catch { ElMessage.error('导出失败') }
  finally { exporting.value = false }
}

watch(activeTab, (t) => {
  if (t === 'risk') loadRisks()
  if (t === 'issue') loadIssues()
  if (t === 'milestone') loadMilestones()
  if (t === 'acceptance') loadAcceptance()
  if (t === 'training') loadTraining()
  if (t === 'stakeholder') loadStakeholders()
  if (t === 'doc') loadDocTree()
})

onMounted(() => { store.fetchProject(projectId.value); loadStakeholders(); })
</script>

<style scoped>
.project-meta { color: #86909c; font-size: 13px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.phase-row { font-weight: 600; background: #f7f8fa; padding: 4px 8px; border-radius: 4px; margin: -4px 0; }
.stat-item { text-align: center; min-width: 60px; }
.doc-tab { margin: -16px; }
.doc-tree-panel { width: 240px; min-width: 240px; border-right: 1px solid #e5e6e8; display: flex; flex-direction: column; overflow-y: auto; }
.markdown-body, .office-preview { line-height: 1.8; font-size: 14px; }
.markdown-body h1, .office-preview h1 { font-size: 22px; margin: 16px 0 8px; }
.markdown-body h2, .office-preview h2 { font-size: 18px; margin: 14px 0 6px; }
.office-preview table { border-collapse: collapse; width: 100%; font-size: 13px; }
.office-preview td, .office-preview th { border: 1px solid #d0d0d0; padding: 6px 10px; }
.kanban-board { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 16px; }
.kanban-col { flex: 1; min-width: 200px; background: #f5f7fa; border-radius: 8px; padding: 12px; }
.kanban-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.kanban-list { display: flex; flex-direction: column; gap: 8px; min-height: 60px; }
.kanban-card { background: #fff; border: 1px solid #e5e6e8; border-radius: 6px; padding: 10px 12px; cursor: grab; }
.kanban-card:hover { border-color: #409eff; box-shadow: 0 1px 4px rgba(64,158,255,.15); }
.kanban-card:active { cursor: grabbing; }
</style>
