<template>
  <div class="fade-in-up">
    <div style="display:flex;gap:24px;align-items:flex-start">
      <!-- Left: Input Panel -->
      <div class="gen-panel">
        <h2 class="gen-title">AI 漫剧生成</h2>
        <p class="gen-sub">输入你的想法，AI 将为你生成分镜、角色与场景</p>

        <div class="input-card">
          <div class="input-label">描述你的漫剧情节</div>
          <el-input v-model="description" type="textarea" :rows="6"
            placeholder="例如：一个雨夜，赛博朋克风格的街头，主角李星河在霓虹灯下遇到一个神秘少女..."
            maxlength="500" show-word-limit />
        </div>

        <div class="input-card">
          <div class="input-label">选择画风</div>
          <div class="style-grid">
            <div v-for="s in styles" :key="s.value"
              class="style-btn" :class="{ active: selectedStyle === s.value }"
              @click="selectedStyle = s.value">
              <div class="style-icon">{{ s.icon }}</div>
              <div>{{ s.label }}</div>
            </div>
          </div>
        </div>

        <div class="input-card">
          <div class="input-label">选择镜头数量</div>
          <el-radio-group v-model="shotCount">
            <el-radio-button v-for="n in [4, 6, 8, 10]" :key="n" :value="n">{{ n }}镜</el-radio-button>
          </el-radio-group>
        </div>

        <el-button type="primary" size="large" :loading="generating" @click="handleGenerate"
          style="width:100%;border-radius:12px;height:48px;font-size:16px;font-weight:600;margin-top:8px;
          background:linear-gradient(135deg,#6366f1,#4f46e5);border:none">
          <el-icon><MagicStick /></el-icon>
          {{ generating ? '生成中...' : '开始生成' }}
        </el-button>

        <!-- Progress -->
        <div v-if="generating || currentTask" class="progress-card">
          <div class="progress-header">
            <span>{{ currentTask?.current_step || '准备中...' }}</span>
            <span class="progress-pct">{{ currentTask?.progress || 0 }}%</span>
          </div>
          <el-progress :percentage="currentTask?.progress || 0" :status="progressStatus"
            :stroke-width="8" />
          <div class="progress-steps">
            <div v-for="step in STEPS" :key="step" class="step-item"
              :class="{ done: isStepDone(step), active: isStepActive(step) }">
              <el-icon v-if="isStepDone(step)"><Check /></el-icon>
              <el-icon v-else-if="isStepActive(step)" class="animate-pulse"><Loading /></el-icon>
              <div v-else class="step-dot"></div>
              <span>{{ step }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Preview -->
      <div class="preview-panel">
        <div class="preview-header">
          <span class="preview-title">生成预览</span>
          <el-tag v-if="generatedShots.length" type="success" size="small">
            已生成 {{ generatedShots.length }} 张分镜
          </el-tag>
        </div>

        <div v-if="currentTask?.video_url" class="preview-video">
          <video :src="currentTask.video_url" controls preload="metadata"></video>
        </div>

        <div class="preview-grid" v-if="generatedShots.length">
          <div v-for="(shot, idx) in generatedShots" :key="shot.id || idx" class="preview-shot">
            <div class="preview-shot-img">
              <img v-if="shot.image_url" :src="shot.image_url" alt="分镜" />
              <div v-else class="preview-shot-placeholder">分镜 {{ shot.shot_no }}</div>
            </div>
            <div class="preview-shot-script">{{ shot.script_content || '...' }}</div>
          </div>
        </div>
        <div v-else class="preview-empty-grid">
          <div v-for="n in shotCount" :key="n" class="preview-empty-cell">分镜 {{ n }}</div>
        </div>

        <!-- History -->
        <div class="history-section">
          <div class="history-title">生成历史</div>
          <div v-for="task in history" :key="task.id" class="history-item" @click="viewTask(task)">
            <div class="history-thumb"></div>
            <div>
              <div class="history-name">{{ task.task_name || '生成任务' }}</div>
              <div class="history-time">{{ relativeTime(task.completed_at) }}</div>
            </div>
          </div>
          <div v-if="!history.length" style="color:#94a3b8;font-size:13px;text-align:center;padding:20px">
            暂无历史记录
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { generateApi } from '@/api'
import { ElMessage } from 'element-plus'
import { MagicStick, Check, Loading } from '@element-plus/icons-vue'

const route = useRoute()

const description = ref('')
const selectedStyle = ref('cyber')
const shotCount = ref(4)
const generating = ref(false)
const currentTask = ref(null)
const generatedShots = ref([])
const history = ref([])
let pollInterval = null

const STEPS = ['变量注入模板', '剧本自动合成', '角色图生成', '分镜批量绘图', '配音合成+渲染']
const STEP_IDX = Object.fromEntries(STEPS.map((s, i) => [s, i]))

const styles = [
  { value: 'cyber', label: '赛博', icon: '🤖' },
  { value: 'ancient', label: '古风', icon: '🏯' },
  { value: 'japanese', label: '日漫', icon: '🌸' },
  { value: 'watercolor', label: '水彩', icon: '🎨' },
]

const progressStatus = computed(() => {
  if (!currentTask.value) return ''
  if (currentTask.value.status === 'done') return 'success'
  if (currentTask.value.status === 'failed') return 'exception'
  return ''
})

function isStepDone(step) {
  if (!currentTask.value) return false
  const cur = currentTask.value.current_step
  if (currentTask.value.status === 'done') return true
  const curIdx = STEPS.indexOf(cur)
  return STEPS.indexOf(step) < curIdx
}

function isStepActive(step) {
  return currentTask.value?.current_step === step
}

function relativeTime(dt) {
  if (!dt) return ''
  const diff = Date.now() - new Date(dt).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return '刚刚'
  if (m < 60) return `${m}分钟前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}小时前`
  return `${Math.floor(h / 24)}天前`
}

async function handleGenerate() {
  if (!description.value.trim()) {
    ElMessage.warning('请输入漫剧情节描述')
    return
  }
  generating.value = true
  generatedShots.value = []
  try {
    const task = await generateApi.create({
      task_name: description.value.slice(0, 30) + (description.value.length > 30 ? '...' : ''),
      task_type: 'free_style',
      style: selectedStyle.value,
      description: description.value,
      variables_snapshot: { description: description.value, shotCount: shotCount.value },
    })
    currentTask.value = task
    startPolling(task.id)
  } catch (e) {
    ElMessage.error(e.message)
    generating.value = false
  }
}

function startPolling(taskId) {
  pollInterval = setInterval(async () => {
    try {
      const task = await generateApi.taskDetail(taskId)
      currentTask.value = task
      if (task.shots?.length) generatedShots.value = task.shots
      if (task.status === 'done') {
        generating.value = false
        clearInterval(pollInterval)
        ElMessage.success('生成完成！')
        await loadHistory()
      } else if (task.status === 'failed') {
        generating.value = false
        clearInterval(pollInterval)
        ElMessage.error('生成失败：' + (task.error_msg || '未知错误'))
      }
    } catch {}
  }, 2000)
}

async function viewTask(task) {
  try {
    const detail = await generateApi.taskDetail(task.id)
    currentTask.value = detail
    generatedShots.value = detail.shots || []
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function loadHistory() {
  try {
    history.value = await generateApi.history()
  } catch {}
}

onMounted(async () => {
  await loadHistory()
  // 支持从模板工作台"查看成品"跳转进入：?task_id=xx 自动加载结果
  const taskId = Number(route.query.task_id)
  if (taskId && history.value.some(t => t.id === taskId)) {
    viewTask({ id: taskId })
  }
})
onUnmounted(() => { if (pollInterval) clearInterval(pollInterval) })
</script>

<style scoped>
.gen-panel {
  width: 420px;
  min-width: 420px;
}

.gen-title { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
.gen-sub { font-size: 13px; color: var(--color-text-secondary); margin-bottom: 20px; }

.input-card {
  background: #fff;
  border-radius: var(--radius-md);
  padding: 18px;
  border: 1px solid var(--color-border);
  margin-bottom: 14px;
}

.input-label {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--color-text-primary);
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.style-btn {
  border: 2px solid var(--color-border);
  border-radius: 10px;
  padding: 10px 6px;
  text-align: center;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.style-btn.active {
  border-color: var(--color-primary);
  background: rgba(99,102,241,0.08);
  color: var(--color-primary);
  font-weight: 600;
}

.style-icon { font-size: 20px; margin-bottom: 4px; }

.progress-card {
  background: #fff;
  border-radius: var(--radius-md);
  padding: 16px;
  border: 1px solid var(--color-border);
  margin-top: 14px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 10px;
}

.progress-pct { color: var(--color-primary); }

.progress-steps {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.step-item.done { color: var(--color-success); }
.step-item.active { color: var(--color-primary); font-weight: 600; }

.step-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid currentColor;
  flex-shrink: 0;
}

.preview-panel {
  flex: 1;
  background: #fff;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.preview-title { font-size: 16px; font-weight: 700; }

.preview-video {
  margin: 12px 0;
  border-radius: 10px;
  overflow: hidden;
  background: #0f172a;
  aspect-ratio: 9/16;
  max-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-video video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.preview-empty-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.preview-empty-cell {
  height: 160px;
  background: #f1f3f9;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #94a3b8;
}

.preview-shot {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.preview-shot-img {
  height: 140px;
  background: #f1f3f9;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-shot-img img { width: 100%; height: 100%; object-fit: cover; }

.preview-shot-placeholder {
  font-size: 13px;
  color: #94a3b8;
}

.preview-shot-script {
  padding: 8px 10px;
  font-size: 11px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  max-height: 52px;
  overflow: hidden;
}

.history-section { border-top: 1px solid var(--color-border); padding-top: 14px; }
.history-title { font-size: 14px; font-weight: 600; margin-bottom: 10px; }
.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.history-item:hover { background: #f8f9fc; }
.history-thumb {
  width: 44px; height: 44px;
  border-radius: 8px;
  background: linear-gradient(135deg,#667eea,#764ba2);
  flex-shrink: 0;
}
.history-name { font-size: 13px; font-weight: 500; margin-bottom: 2px; }
.history-time { font-size: 11px; color: var(--color-text-muted); }
</style>
