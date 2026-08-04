<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h1 class="page-title">项目管理</h1>
      <div style="display:flex;gap:10px">
        <el-button :icon="Filter">筛选</el-button>
        <el-button type="primary" :icon="Plus" @click="createDialogVisible=true">新建项目</el-button>
      </div>
    </div>

    <!-- Status Tabs -->
    <el-tabs v-model="activeStatus" @tab-change="loadProjects" style="margin-bottom:20px">
      <el-tab-pane :label="`全部 ${total}`" name="" />
      <el-tab-pane :label="`创作中 ${countByStatus('in_progress')}`" name="in_progress" />
      <el-tab-pane :label="`已完成 ${countByStatus('completed')}`" name="completed" />
      <el-tab-pane :label="`草稿 ${countByStatus('draft')}`" name="draft" />
    </el-tabs>

    <!-- Projects grid -->
    <div class="grid-4" v-if="projects.length">
      <div class="project-card" v-for="p in projects" :key="p.id">
        <div class="project-cover" :style="{ background: coverGradient(p) }" @click="openWorkspace(p)">
          <span class="project-cover-label">{{ p.title }}</span>
        </div>
        <div class="project-info">
          <div class="project-title">{{ p.title }}</div>
          <div class="project-meta">
            <span class="status-dot" :class="p.status"></span>
            {{ p.current_page }}/{{ p.total_pages }} 页 · {{ relativeTime(p.updated_at) }}
          </div>
        </div>
        <div class="card-actions">
          <el-button text size="small" @click="openWorkspace(p)">打开</el-button>
          <el-button text size="small" type="danger" @click="deleteProject(p)">删除</el-button>
        </div>
      </div>
    </div>

    <div v-else-if="!loading" class="empty-state">
      <div class="empty-icon">📂</div>
      <div class="empty-text">还没有项目，开始创建第一个吧</div>
      <el-button type="primary" @click="createDialogVisible=true">创建项目</el-button>
    </div>

    <!-- Create Dialog -->
    <el-dialog v-model="createDialogVisible" title="新建漫剧项目" width="480px" border-radius="16px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="项目名称 *">
          <el-input v-model="createForm.title" placeholder="给你的漫剧起个名字" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="createForm.category" placeholder="选择题材分类" style="width:100%">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="画风">
          <el-select v-model="createForm.style" placeholder="选择画风" style="width:100%">
            <el-option v-for="s in styles" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3"
            placeholder="简单描述一下这个漫剧的故事背景..." maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="计划总页数">
          <el-input-number v-model="createForm.total_pages" :min="1" :max="200" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建项目</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { projectsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Filter } from '@element-plus/icons-vue'

const router = useRouter()
const projects = ref([])
const allProjects = ref([])
const loading = ref(false)
const creating = ref(false)
const activeStatus = ref('')
const createDialogVisible = ref(false)

const categories = ['都市', '古风', '甜宠', '悬疑', '玄幻', '校园', '末世']
const styles = ['赛博', '古风', '日漫', '水彩', '国漫']

const createForm = ref({ title: '', category: '', style: '', description: '', total_pages: 20 })

const total = computed(() => allProjects.value.length)
function countByStatus(s) { return allProjects.value.filter(p => p.status === s).length }

const GRADIENTS = [
  'linear-gradient(135deg,#667eea,#764ba2)',
  'linear-gradient(135deg,#f093fb,#f5576c)',
  'linear-gradient(135deg,#4facfe,#00f2fe)',
  'linear-gradient(135deg,#43e97b,#38f9d7)',
  'linear-gradient(135deg,#fa709a,#fee140)',
  'linear-gradient(135deg,#a18cd1,#fbc2eb)',
]
function coverGradient(p) { return GRADIENTS[p.id % GRADIENTS.length] }

function relativeTime(dt) {
  if (!dt) return ''
  const diff = Date.now() - new Date(dt).getTime()
  const d = Math.floor(diff / 86400000)
  if (d === 0) return '今天更新'
  if (d === 1) return '昨天更新'
  return `${d}天前更新`
}

function openWorkspace(p) { router.push(`/workspace/${p.id}`) }

async function loadProjects() {
  loading.value = true
  try {
    const params = activeStatus.value ? { status: activeStatus.value } : {}
    projects.value = await projectsApi.list(params)
    if (!activeStatus.value) allProjects.value = projects.value
  } finally { loading.value = false }
}

async function handleCreate() {
  if (!createForm.value.title.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  creating.value = true
  try {
    const p = await projectsApi.create(createForm.value)
    ElMessage.success('项目创建成功！')
    createDialogVisible.value = false
    await loadProjects()
    router.push(`/workspace/${p.id}`)
  } catch (e) {
    ElMessage.error(e.message)
  } finally { creating.value = false }
}

async function deleteProject(p) {
  try {
    await ElMessageBox.confirm(`确定删除项目"${p.title}"吗？此操作不可恢复。`, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    })
    await projectsApi.delete(p.id)
    ElMessage.success('项目已删除')
    await loadProjects()
  } catch {}
}

onMounted(async () => {
  await loadProjects()
  allProjects.value = await projectsApi.list({})
})
</script>

<style scoped>
.project-cover { cursor: pointer; position: relative; }
.project-cover-label {
  position: relative; z-index: 1;
  font-size: 20px; font-weight: 700; color: rgba(255,255,255,0.5); letter-spacing: 1px;
}
.card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  padding: 0 12px 10px;
  border-top: 1px solid var(--color-border);
  margin-top: -2px;
}
</style>
