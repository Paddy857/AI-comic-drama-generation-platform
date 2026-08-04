<template>
  <div class="workspace-layout fade-in-up">
    <!-- Left: Shot List -->
    <div class="ws-left">
      <div class="ws-panel-header">
        <span>页面分镜</span>
        <el-button size="small" :icon="Plus" circle @click="addShot" title="添加分镜" />
      </div>
      <div class="shot-list">
        <div v-for="(shot, idx) in shots" :key="shot.id"
          class="shot-thumb" :class="{ active: selectedShotId === shot.id }"
          @click="selectedShotId = shot.id">
          <div class="shot-number">{{ idx + 1 }}</div>
          <div class="shot-preview">
            <img v-if="shot.image_url" :src="shot.image_url" alt="分镜图" class="shot-img" />
            <div v-else class="shot-placeholder">
              <el-icon><Picture /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Center: Canvas -->
    <div class="ws-center">
      <div class="canvas-toolbar">
        <el-tag v-if="project" type="info" size="small">{{ project.title }}</el-tag>
        <el-tag v-if="selectedShot" size="small">{{ selectedShot.shot_type || '分镜' }}</el-tag>
      </div>
      <div class="canvas-area">
        <div v-if="selectedShot" class="shot-content">
          <div class="shot-canvas-img" v-if="selectedShot.image_url">
            <img :src="selectedShot.image_url" alt="分镜" style="max-width:100%;max-height:100%;object-fit:contain" />
          </div>
          <div v-else class="canvas-empty">
            <div style="font-size:48px;margin-bottom:16px">🎨</div>
            <div style="font-size:16px;color:#94a3b8;margin-bottom:20px">漫画画布</div>
            <div style="font-size:13px;color:#cbd5e1">从左侧选择分镜，或拖拽角色到画布</div>
          </div>
          <!-- Script overlay -->
          <div class="shot-script-bar" v-if="selectedShot.script_content">
            <el-input v-model="selectedShot.script_content" type="textarea" :rows="2"
              placeholder="分镜脚本/对白" @change="updateShot(selectedShot)" />
          </div>
        </div>
        <div v-else class="canvas-empty">
          <div style="font-size:48px;margin-bottom:16px">🎬</div>
          <div style="font-size:20px;font-weight:700;color:#94a3b8">漫画画布</div>
          <div style="font-size:13px;color:#cbd5e1;margin-top:12px">从左侧选择分镜，或拖拽角色到画布</div>
        </div>
      </div>
    </div>

    <!-- Right: Properties Panel -->
    <div class="ws-right">
      <div class="ws-panel-header">属性面板</div>
      <div class="ws-panel-body" v-if="selectedShot">
        <div class="prop-section">
          <div class="prop-label">图层</div>
          <div class="layer-item" v-for="layer in ['主角_图层', '背景_图层', '对话气泡']" :key="layer">
            <el-checkbox>{{ layer }}</el-checkbox>
          </div>
        </div>
        <el-divider />
        <div class="prop-section">
          <div class="prop-label">景别</div>
          <el-select v-model="selectedShot.shot_type" size="small" style="width:100%" @change="updateShot(selectedShot)">
            <el-option v-for="t in shotTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </div>
        <div class="prop-section">
          <div class="prop-label">运镜</div>
          <el-select v-model="selectedShot.camera_move" size="small" style="width:100%" @change="updateShot(selectedShot)">
            <el-option v-for="t in cameraMoves" :key="t" :label="t" :value="t" />
          </el-select>
        </div>
        <div class="prop-section">
          <div class="prop-label">时长(秒)</div>
          <el-input-number v-model="selectedShot.duration_sec" size="small"
            :min="1" :max="60" style="width:100%" @change="updateShot(selectedShot)" />
        </div>
        <div class="prop-section">
          <div class="prop-label">情绪</div>
          <el-input v-model="selectedShot.mood" size="small" placeholder="如：压抑铺垫" @change="updateShot(selectedShot)" />
        </div>
        <div class="prop-section">
          <div class="prop-label">情绪强度</div>
          <el-slider v-model="selectedShot.mood_intensity" :min="1" :max="10" @change="updateShot(selectedShot)" />
        </div>
        <el-divider />
        <div class="prop-section">
          <div class="prop-label">快捷角色</div>
          <div class="char-quick-list">
            <div v-for="c in characters.slice(0,4)" :key="c.id" class="char-quick-item">
              <div class="char-mini-avatar">{{ c.name[0] }}</div>
              <span>{{ c.name }}</span>
            </div>
          </div>
        </div>
        <el-button size="small" type="danger" style="width:100%;margin-top:12px"
          @click="deleteShot(selectedShot)" :icon="Delete">删除此分镜</el-button>
      </div>
      <div v-else class="ws-panel-body" style="color:#94a3b8;text-align:center;padding:40px 16px">
        选中分镜后在这里编辑属性
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi, shotsApi, charactersApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Plus, Picture, Delete } from '@element-plus/icons-vue'

const route = useRoute()
const project = ref(null)
const shots = ref([])
const characters = ref([])
const selectedShotId = ref(null)

const shotTypes = ['大全景', '全景', '中景', '近景', '特写', '仰拍', '俯拍', '过肩']
const cameraMoves = ['固定', '推', '拉', '摇', '跟', '升', '降', '旋转']

const selectedShot = computed(() => shots.value.find(s => s.id === selectedShotId.value) || null)

async function loadData() {
  const id = route.params.id
  try {
    const [proj, shotList, charList] = await Promise.all([
      projectsApi.get(id),
      shotsApi.listByProject(id),
      charactersApi.list({ limit: 20 }),
    ])
    project.value = proj
    shots.value = shotList
    characters.value = charList
    if (shotList.length) selectedShotId.value = shotList[0].id
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function addShot() {
  const id = route.params.id
  try {
    const shot = await shotsApi.create({
      project_id: parseInt(id),
      order: shots.value.length,
      shot_type: '全景',
      camera_move: '固定',
      duration_sec: 5,
    })
    shots.value.push(shot)
    selectedShotId.value = shot.id
  } catch (e) { ElMessage.error(e.message) }
}

async function updateShot(shot) {
  try {
    await shotsApi.update(shot.id, {
      shot_type: shot.shot_type,
      camera_move: shot.camera_move,
      duration_sec: shot.duration_sec,
      script_content: shot.script_content,
      mood: shot.mood,
      mood_intensity: shot.mood_intensity,
    })
  } catch {}
}

async function deleteShot(shot) {
  try {
    await shotsApi.delete(shot.id)
    shots.value = shots.value.filter(s => s.id !== shot.id)
    selectedShotId.value = shots.value[0]?.id || null
    ElMessage.success('分镜已删除')
  } catch (e) { ElMessage.error(e.message) }
}

onMounted(loadData)
</script>

<style scoped>
.workspace-layout {
  display: flex;
  height: calc(100vh - 120px);
  gap: 0;
  margin: -28px -32px;
  background: #f1f3f9;
}

.ws-left {
  width: 200px;
  min-width: 200px;
  background: #fff;
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}

.ws-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid var(--color-border);
  background: #fff;
}

.shot-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shot-thumb {
  border-radius: 8px;
  border: 2px solid transparent;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  background: #f8f9fc;
}

.shot-thumb.active {
  border-color: var(--color-primary);
}

.shot-thumb:hover:not(.active) {
  border-color: var(--color-border);
  box-shadow: var(--shadow-sm);
}

.shot-number {
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  background: #fff;
}

.shot-preview {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef0f5;
}

.shot-img { width: 100%; height: 100%; object-fit: cover; }

.shot-placeholder {
  font-size: 28px;
  color: #c0c4cc;
}

.ws-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.canvas-toolbar {
  height: 44px;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 8px;
}

.canvas-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef0f5;
  position: relative;
  overflow: hidden;
}

.shot-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.shot-canvas-img {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.canvas-empty { text-align: center; }

.shot-script-bar {
  background: rgba(255,255,255,0.95);
  border-top: 1px solid var(--color-border);
  padding: 12px 20px;
}

.ws-right {
  width: 240px;
  min-width: 240px;
  background: #fff;
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}

.ws-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
}

.prop-section { margin-bottom: 14px; }
.prop-label { font-size: 12px; font-weight: 600; color: var(--color-text-secondary); margin-bottom: 6px; }

.layer-item {
  padding: 4px 0;
  font-size: 13px;
}

.char-quick-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.char-quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  border-radius: 8px;
  background: #f8f9fc;
  cursor: pointer;
  font-size: 11px;
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.char-quick-item:hover { background: rgba(99,102,241,0.08); color: var(--color-primary); }

.char-mini-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary-light), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: rgba(255,255,255,0.8);
}
</style>
