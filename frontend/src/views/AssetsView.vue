<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h1 class="page-title">素材管理</h1>
      <el-button type="primary" :icon="Upload" @click="uploadDialogVisible=true">上传素材</el-button>
    </div>

    <!-- Filter tabs -->
    <el-tabs v-model="fileType" @tab-change="loadAssets">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="🖼️ 图片" name="image" />
      <el-tab-pane label="🎬 视频" name="video" />
      <el-tab-pane label="🎵 音频" name="audio" />
    </el-tabs>

    <div class="grid-5" v-if="assets.length" style="margin-top:16px">
      <div class="asset-card" v-for="a in assets" :key="a.id">
        <div class="asset-thumb">
          <img v-if="a.file_type==='image' && a.file_path" :src="a.file_path" alt="" />
          <div v-else class="asset-icon">{{ fileIcon(a.file_type) }}</div>
        </div>
        <div class="asset-info">
          <div class="asset-name" :title="a.file_name">{{ a.file_name }}</div>
          <div class="asset-size">{{ formatSize(a.file_size) }}</div>
        </div>
        <el-button size="small" type="danger" circle :icon="Delete"
          class="asset-del" @click="deleteAsset(a)" />
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">📦</div>
      <div class="empty-text">还没有素材，上传你的第一个素材吧</div>
      <el-button type="primary" @click="uploadDialogVisible=true">上传素材</el-button>
    </div>

    <!-- Upload Dialog -->
    <el-dialog v-model="uploadDialogVisible" title="上传素材" width="440px">
      <el-upload drag action="" :http-request="handleUpload" :before-upload="beforeUpload"
        multiple accept="image/*,video/*,audio/*" :show-file-list="true" :limit="5">
        <el-icon style="font-size:48px;color:var(--color-primary)"><Upload /></el-icon>
        <div style="margin-top:12px;font-size:14px">拖拽文件到此处，或点击上传</div>
        <div style="font-size:12px;color:#94a3b8;margin-top:6px">支持图片、视频、音频，单文件最大50MB</div>
      </el-upload>
      <template #footer>
        <el-button @click="uploadDialogVisible=false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { assetsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Delete } from '@element-plus/icons-vue'

const assets = ref([])
const fileType = ref('')
const uploadDialogVisible = ref(false)

function fileIcon(type) { return { image: '🖼️', video: '🎬', audio: '🎵' }[type] || '📄' }
function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024*1024) return `${(bytes/1024).toFixed(1)}KB`
  return `${(bytes/1024/1024).toFixed(1)}MB`
}

async function loadAssets() {
  try { assets.value = await assetsApi.list({ file_type: fileType.value || undefined }) }
  catch (e) { ElMessage.error(e.message) }
}

function beforeUpload(file) {
  if (file.size > 50*1024*1024) { ElMessage.error('文件超过50MB限制'); return false }
  return true
}

async function handleUpload({ file }) {
  const fd = new FormData()
  fd.append('file', file)
  try {
    await assetsApi.upload(fd)
    ElMessage.success(`${file.name} 上传成功`)
    await loadAssets()
  } catch (e) { ElMessage.error(e.message) }
}

async function deleteAsset(a) {
  try {
    await ElMessageBox.confirm('删除此素材？', '删除确认', { type: 'warning' })
    await assetsApi.delete(a.id)
    ElMessage.success('已删除')
    await loadAssets()
  } catch {}
}

onMounted(loadAssets)
</script>

<style scoped>
.asset-card {
  background: #fff;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-border);
  transition: all 0.2s;
  position: relative;
}
.asset-card:hover { box-shadow: var(--shadow-md); }
.asset-card:hover .asset-del { opacity: 1; }
.asset-thumb {
  height: 120px;
  background: #f1f3f9;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.asset-thumb img { width: 100%; height: 100%; object-fit: cover; }
.asset-icon { font-size: 40px; }
.asset-info { padding: 10px 12px; }
.asset-name { font-size: 12px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.asset-size { font-size: 11px; color: var(--color-text-secondary); margin-top: 2px; }
.asset-del {
  position: absolute;
  top: 6px;
  right: 6px;
  opacity: 0;
  transition: opacity 0.2s;
  box-shadow: var(--shadow-md);
}
</style>
