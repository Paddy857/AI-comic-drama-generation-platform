<template>
  <div class="fade-in-up">
    <div v-if="loading" style="text-align:center;padding:60px">
      <el-icon class="animate-pulse" style="font-size:40px;color:var(--color-primary)"><Loading /></el-icon>
      <div style="margin-top:12px;color:var(--color-text-secondary)">加载模板中...</div>
    </div>

    <div v-else-if="template" class="tw-layout">
      <!-- Left: Variable form -->
      <div class="tw-left">
        <div class="tw-header">
          <el-button :icon="ArrowLeft" text @click="$router.push('/templates')">返回模板中心</el-button>
          <h2 class="tw-title">{{ template.name }}</h2>
          <el-tag type="info" size="small">{{ template.category }}</el-tag>
        </div>

        <!-- Required variables -->
        <div class="var-section">
          <div class="var-section-title">
            <span class="req-dot"></span>
            必填变量（{{ requiredVars.length }}个）
          </div>
          <div v-for="v in requiredVars" :key="v.key" class="var-item">
            <div class="var-label">
              {{ v.label }}
              <span class="req-badge">必须填！</span>
            </div>
            <div class="var-hint">{{ v.hint }}</div>
            <div class="var-input-row">
              <el-input v-if="v.var_type !== 'textarea'"
                v-model="formValues[v.key]"
                :placeholder="v.default_value || `请输入${v.label}`"
                @input="updatePreview" />
              <el-input v-else
                v-model="formValues[v.key]"
                type="textarea" :rows="2"
                :placeholder="v.default_value || `请输入${v.label}`"
                @input="updatePreview" />
              <el-button circle size="small" title="随机示例"
                @click="randomExample(v)" v-if="v.examples?.length">
                🎲
              </el-button>
            </div>
            <div class="var-examples" v-if="v.examples?.length">
              <span>示例：</span>
              <el-tag v-for="ex in v.examples.slice(0,3)" :key="ex" size="small"
                style="cursor:pointer" @click="formValues[v.key]=ex; updatePreview()">
                {{ ex }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- Optional variables -->
        <el-collapse v-model="showOptional">
          <el-collapse-item title="展开可选优化（系统已填默认值）" name="optional">
            <div v-for="v in optionalVars" :key="v.key" class="var-item">
              <div class="var-label">{{ v.label }}</div>
              <el-select v-if="v.var_type === 'select'" v-model="formValues[v.key]" style="width:100%" @change="updatePreview">
                <el-option v-for="opt in v.options" :key="opt" :label="opt" :value="opt" />
              </el-select>
              <el-input v-else v-model="formValues[v.key]" :placeholder="v.default_value" @input="updatePreview" />
            </div>
          </el-collapse-item>
        </el-collapse>

        <!-- AI Fill Button -->
        <el-button type="success" size="large" :loading="aiFilling"
          style="width:100%;border-radius:10px;height:44px;margin:16px 0"
          @click="aiFillVariables" :disabled="!hasRequiredFilled">
          ✨ AI帮我填（剩余可选字段）
        </el-button>

        <!-- Style selector -->
        <div class="var-section">
          <div class="var-section-title">选择画风</div>
          <div class="style-mini-grid">
            <div v-for="s in styles" :key="s.value"
              class="style-mini-btn" :class="{ active: selectedStyle === s.value }"
              @click="selectedStyle = s.value">
              {{ s.icon }} {{ s.label }}
            </div>
          </div>
        </div>

        <!-- Submit -->
        <el-button type="primary" size="large" :loading="submitting"
          style="width:100%;border-radius:10px;height:48px;font-size:15px;font-weight:600;
          background:linear-gradient(135deg,#6366f1,#4f46e5);border:none"
          @click="startGeneration" :disabled="!hasRequiredFilled">
          🚀 开始生成漫剧
        </el-button>
      </div>

      <!-- Right: Preview -->
      <div class="tw-right">
        <div class="preview-header-bar">
          <span class="preview-header-title">模板结构预览（只读）</span>
          <el-tag size="small">{{ template.total_shots }}镜 · {{ Math.floor(template.total_duration_sec/60) }}分钟</el-tag>
        </div>

        <!-- Shot preview list -->
        <div class="shot-preview-list">
          <div v-for="shot in previewShots" :key="shot.shot_no" class="preview-shot-card">
            <div class="shot-header">
              <span class="shot-no">镜头 {{ shot.shot_no }}</span>
              <span class="shot-meta">{{ shot.shot_type }} · {{ shot.camera_move }} · {{ shot.duration_sec }}s</span>
              <el-tag size="small" :type="moodColor(shot.mood_intensity)">{{ shot.mood }}</el-tag>
            </div>
            <div class="shot-rendered-script">{{ renderScript(shot.script_template) }}</div>
          </div>
        </div>

        <!-- Emotion Curve -->
        <div class="emotion-curve-section">
          <div class="curve-title">情绪曲线</div>
          <div class="curve-bars">
            <div v-for="(point, idx) in (template.emotion_curve || [])" :key="idx"
              class="curve-bar-item">
              <div class="curve-bar" :style="{ height: point.intensity * 12 + 'px', background: intensityColor(point.intensity) }"></div>
              <div class="curve-label">{{ point.shot }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Generation Progress Overlay -->
    <el-dialog v-model="progressVisible" title="🎬 正在生成中..." :close-on-click-modal="false"
      :close-on-press-escape="false" width="480px">
      <div class="gen-progress-body">
        <el-progress type="circle" :percentage="currentTask?.progress || 0"
          :width="120" :stroke-width="10" :status="taskStatus" />
        <div class="gen-step-name">{{ currentTask?.current_step || '准备中...' }}</div>
        <div class="gen-steps-list">
          <div v-for="step in STEPS" :key="step" class="gen-step"
            :class="{ done: isStepDone(step), active: isStepActive(step) }">
            {{ isStepDone(step) ? '✅' : isStepActive(step) ? '⏳' : '⬜' }} {{ step }}
          </div>
        </div>
        <div class="gen-tip">💡 模板加持，比自由创作快40%！</div>
      </div>
      <template #footer v-if="currentTask?.status === 'done'">
        <el-button type="primary" @click="progressVisible=false; router.push(`/ai-generate?task_id=${currentTask.id}`)">查看成品 🎉</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { templatesApi, generateApi } from '@/api'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const template = ref(null)
const loading = ref(true)
const aiFilling = ref(false)
const submitting = ref(false)
const progressVisible = ref(false)
const currentTask = ref(null)
const formValues = ref({})
const selectedStyle = ref('ancient')
const showOptional = ref([])
let pollInterval = null

const STEPS = ['变量注入模板', '剧本自动合成', '角色图生成', '分镜批量绘图', '配音合成+渲染']

const styles = [
  { value: 'ancient', label: '古风', icon: '🏯' },
  { value: 'cyber', label: '赛博', icon: '🤖' },
  { value: 'japanese', label: '日漫', icon: '🌸' },
  { value: 'watercolor', label: '水彩', icon: '🎨' },
]

const requiredVars = computed(() => (template.value?.variables || []).filter(v => v.is_required))
const optionalVars = computed(() => (template.value?.variables || []).filter(v => !v.is_required))
const hasRequiredFilled = computed(() =>
  requiredVars.value.every(v => formValues.value[v.key]?.trim())
)

const taskStatus = computed(() => {
  if (currentTask.value?.status === 'done') return 'success'
  if (currentTask.value?.status === 'failed') return 'exception'
  return ''
})

const previewShots = computed(() => template.value?.fixed_shots || [])

function renderScript(tmpl) {
  if (!tmpl) return ''
  return tmpl.replace(/\$\{(\w+)\}/g, (_, key) => {
    const val = formValues.value[key]
    if (val) return `【${val}】`
    const varDef = (template.value?.variables || []).find(v => v.key === key)
    return varDef?.default_value ? `[${varDef.default_value}]` : `[${key}]`
  })
}

function moodColor(intensity) {
  if (intensity >= 9) return 'danger'
  if (intensity >= 7) return 'warning'
  if (intensity >= 5) return 'primary'
  return 'info'
}

function intensityColor(intensity) {
  if (intensity >= 9) return 'linear-gradient(to top,#ef4444,#f97316)'
  if (intensity >= 7) return 'linear-gradient(to top,#f59e0b,#fbbf24)'
  if (intensity >= 5) return 'linear-gradient(to top,#6366f1,#818cf8)'
  return 'linear-gradient(to top,#3b82f6,#60a5fa)'
}

function updatePreview() {} // Reactive via computed

function randomExample(v) {
  if (v.examples?.length) {
    formValues.value[v.key] = v.examples[Math.floor(Math.random() * v.examples.length)]
  }
}

async function aiFillVariables() {
  aiFilling.value = true
  try {
    const res = await generateApi.aiFill({ required_vars: formValues.value })
    const generated = res.generated_vars || {}
    for (const [key, val] of Object.entries(generated)) {
      if (!formValues.value[key] || formValues.value[key] === '') {
        formValues.value[key] = val
      }
    }
    showOptional.value = ['optional']
    ElMessage.success('AI已帮你填充可选变量！')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    aiFilling.value = false
  }
}

function isStepDone(step) {
  if (currentTask.value?.status === 'done') return true
  const cur = currentTask.value?.current_step
  return STEPS.indexOf(step) < STEPS.indexOf(cur)
}
function isStepActive(step) { return currentTask.value?.current_step === step }

async function startGeneration() {
  submitting.value = true
  try {
    const task = await generateApi.create({
      template_id: template.value.id,
      task_name: template.value.name,
      task_type: 'from_template',
      style: selectedStyle.value,
      variables_snapshot: { ...formValues.value },
    })
    currentTask.value = task
    progressVisible.value = true
    pollInterval = setInterval(async () => {
      try {
        const t = await generateApi.taskDetail(task.id)
        currentTask.value = t
        if (t.status === 'done' || t.status === 'failed') {
          clearInterval(pollInterval)
          if (t.status === 'done') ElMessage.success('🎉 生成完成！')
          else ElMessage.error('生成失败：' + t.error_msg)
        }
      } catch {}
    }, 2000)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const t = await templatesApi.get(route.params.id)
    template.value = t
    // Init defaults：预填后端下发的默认值，避免按钮初始禁用
    for (const v of (t.variables || [])) {
      formValues.value[v.key] = v.default_value || ''
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => { if (pollInterval) clearInterval(pollInterval) })
</script>

<style scoped>
.tw-layout {
  display: flex;
  gap: 24px;
  height: calc(100vh - 140px);
}

.tw-left {
  width: 420px;
  min-width: 420px;
  overflow-y: auto;
  padding-right: 4px;
}

.tw-header { margin-bottom: 20px; }
.tw-title { font-size: 20px; font-weight: 700; margin: 8px 0; }

.var-section { margin-bottom: 16px; }
.var-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--color-text-primary);
}

.req-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--color-danger);
}

.var-item {
  background: #fff;
  border-radius: 10px;
  padding: 14px;
  border: 1px solid var(--color-border);
  margin-bottom: 10px;
}

.var-label {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.req-badge {
  font-size: 10px;
  background: #fee2e2;
  color: #ef4444;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.var-hint { font-size: 11px; color: var(--color-text-secondary); margin-bottom: 8px; }
.var-input-row { display: flex; gap: 6px; align-items: flex-start; }
.var-examples { margin-top: 8px; display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--color-text-muted); }

.style-mini-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.style-mini-btn {
  border: 2px solid var(--color-border);
  border-radius: 8px;
  padding: 8px 4px;
  text-align: center;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}
.style-mini-btn.active {
  border-color: var(--color-primary);
  background: rgba(99,102,241,0.08);
  color: var(--color-primary);
  font-weight: 600;
}

.tw-right {
  flex: 1;
  background: #fff;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.preview-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
  font-weight: 700;
}

.preview-header-title { font-size: 15px; }

.shot-preview-list { padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.preview-shot-card {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 12px;
  transition: border-color 0.2s;
}
.preview-shot-card:hover { border-color: var(--color-primary-light); }
.shot-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.shot-no { font-size: 13px; font-weight: 700; color: var(--color-primary); }
.shot-meta { font-size: 11px; color: var(--color-text-secondary); flex: 1; }
.shot-rendered-script { font-size: 13px; line-height: 1.6; color: var(--color-text-primary); }

.emotion-curve-section { padding: 16px 20px; border-top: 1px solid var(--color-border); }
.curve-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; }
.curve-bars { display: flex; align-items: flex-end; gap: 8px; height: 140px; }
.curve-bar-item { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; }
.curve-bar { width: 100%; min-height: 8px; border-radius: 4px 4px 0 0; transition: height 0.3s ease; }
.curve-label { font-size: 10px; color: var(--color-text-secondary); text-align: center; white-space: nowrap; }

.gen-progress-body { text-align: center; padding: 20px; }
.gen-step-name { font-size: 15px; font-weight: 600; margin: 16px 0 10px; }
.gen-steps-list { text-align: left; max-width: 260px; margin: 0 auto 16px; }
.gen-step { font-size: 13px; padding: 4px 0; }
.gen-step.done { color: var(--color-success); }
.gen-step.active { color: var(--color-primary); font-weight: 600; }
.gen-tip {
  font-size: 12px;
  color: var(--color-text-secondary);
  background: #f8f9fc;
  border-radius: 8px;
  padding: 8px 16px;
}
</style>
