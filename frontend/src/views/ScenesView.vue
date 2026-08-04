<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h1 class="page-title">场景库</h1>
      <el-button type="primary" :icon="Plus" @click="createDialogVisible=true">添加场景</el-button>
    </div>

    <div class="grid-4" v-if="scenes.length">
      <div class="scene-card" v-for="s in scenes" :key="s.id">
        <div class="scene-cover" :style="{ background: sceneGradient(s) }">
          <div class="scene-cover-icon">{{ sceneIcon(s.scene_type) }}</div>
          <div class="scene-time-badge">{{ s.time_of_day || '未知时段' }}</div>
        </div>
        <div class="scene-body">
          <div class="scene-name">{{ s.name }}</div>
          <div class="scene-meta">
            <el-tag size="small" v-if="s.scene_type">{{ s.scene_type }}</el-tag>
            <el-tag size="small" type="info" v-if="s.weather">{{ s.weather }}</el-tag>
          </div>
          <div class="scene-desc">{{ s.description }}</div>
        </div>
        <div class="scene-footer">
          <el-button text size="small" @click="editScene(s)">编辑</el-button>
          <el-button text size="small" type="danger" @click="deleteScene(s)">删除</el-button>
        </div>
      </div>
      <div class="scene-card add-card" @click="createDialogVisible=true">
        <div style="font-size:36px;margin-bottom:8px">🌄</div>
        <div style="font-size:14px;color:var(--color-text-secondary)">添加新场景</div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">🌄</div>
      <div class="empty-text">还没有场景，添加你的第一个场景吧</div>
      <el-button type="primary" @click="createDialogVisible=true">添加场景</el-button>
    </div>

    <el-dialog v-model="createDialogVisible" :title="editingScene ? '编辑场景' : '添加场景'" width="460px">
      <el-form :model="sceneForm" label-position="top">
        <el-form-item label="场景名称 *">
          <el-input v-model="sceneForm.name" placeholder="如：豪华酒店宴会厅" />
        </el-form-item>
        <el-form-item label="场景类型">
          <el-select v-model="sceneForm.scene_type" style="width:100%">
            <el-option v-for="t in sceneTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="时段">
          <el-radio-group v-model="sceneForm.time_of_day">
            <el-radio-button v-for="t in timesOfDay" :key="t" :value="t">{{ t }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="天气">
          <el-input v-model="sceneForm.weather" placeholder="如：晴天、暴雨、霓虹雨夜" />
        </el-form-item>
        <el-form-item label="场景描述">
          <el-input v-model="sceneForm.description" type="textarea" :rows="3" maxlength="300" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveScene">
          {{ editingScene ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { scenesApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const scenes = ref([])
const createDialogVisible = ref(false)
const saving = ref(false)
const editingScene = ref(null)

const sceneTypes = ['室内', '室外', '自然', '城市', '宫廷', '太空', '末世废墟']
const timesOfDay = ['白天', '夜晚', '黄昏', '清晨']

const defaultForm = () => ({ name: '', scene_type: '', time_of_day: '白天', weather: '', description: '' })
const sceneForm = ref(defaultForm())

const GRADIENTS = [
  'linear-gradient(135deg,#667eea,#764ba2)',
  'linear-gradient(135deg,#f093fb,#f5576c)',
  'linear-gradient(135deg,#4facfe,#00f2fe)',
  'linear-gradient(135deg,#43e97b,#38f9d7)',
  'linear-gradient(135deg,#fa709a,#fee140)',
]
function sceneGradient(s) { return GRADIENTS[s.id % GRADIENTS.length] }
function sceneIcon(type) {
  return { '室内': '🏠', '室外': '🌆', '自然': '🌲', '城市': '🏙️', '宫廷': '🏯', '太空': '🚀', '末世废墟': '🏚️' }[type] || '🌄'
}

async function loadScenes() {
  try { scenes.value = await scenesApi.list({}) } catch (e) { ElMessage.error(e.message) }
}

function editScene(s) {
  editingScene.value = s
  sceneForm.value = { name: s.name, scene_type: s.scene_type || '', time_of_day: s.time_of_day || '白天', weather: s.weather || '', description: s.description || '' }
  createDialogVisible.value = true
}

async function saveScene() {
  if (!sceneForm.value.name.trim()) { ElMessage.warning('请输入场景名称'); return }
  saving.value = true
  try {
    if (editingScene.value) {
      await scenesApi.update(editingScene.value.id, sceneForm.value)
      ElMessage.success('场景已更新')
    } else {
      await scenesApi.create(sceneForm.value)
      ElMessage.success('场景已创建')
    }
    createDialogVisible.value = false
    editingScene.value = null
    sceneForm.value = defaultForm()
    await loadScenes()
  } catch (e) { ElMessage.error(e.message) } finally { saving.value = false }
}

async function deleteScene(s) {
  try {
    await ElMessageBox.confirm(`删除场景"${s.name}"？`, '删除确认', { type: 'warning' })
    await scenesApi.delete(s.id)
    ElMessage.success('已删除')
    await loadScenes()
  } catch {}
}

onMounted(loadScenes)
</script>

<style scoped>
.scene-card {
  background: #fff;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all 0.25s;
}
.scene-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.scene-cover {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.scene-cover-icon { font-size: 36px; }
.scene-time-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0,0,0,0.4);
  color: #fff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 12px;
  backdrop-filter: blur(4px);
}
.scene-body { padding: 14px; }
.scene-name { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.scene-meta { display: flex; gap: 6px; margin-bottom: 6px; }
.scene-desc { font-size: 12px; color: var(--color-text-secondary); line-height: 1.4; }
.scene-footer {
  display: flex;
  justify-content: flex-end;
  padding: 0 10px 10px;
  gap: 4px;
  border-top: 1px solid var(--color-border);
}
.add-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  border: 2px dashed var(--color-border);
}
.add-card:hover { border-color: var(--color-primary); }
</style>
