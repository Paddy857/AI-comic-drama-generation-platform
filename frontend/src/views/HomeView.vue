<template>
  <div class="fade-in-up">
    <!-- Welcome header -->
    <div class="welcome-banner">
      <div>
        <h2 class="welcome-title">欢迎回来，{{ authStore.user?.nickname || '创作者' }} 👋</h2>
        <p class="welcome-sub">今天是个创作的好日子，你的漫剧项目正在等待继续</p>
      </div>
    </div>

    <!-- Stats row -->
    <div class="grid-4" style="margin-bottom:32px">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-value" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <!-- Recent projects -->
    <div class="section-title">
      <span>最近项目</span>
      <span class="section-link" @click="$router.push('/projects')">查看全部 →</span>
    </div>

    <div class="grid-4" style="margin-bottom:32px" v-if="projects.length">
      <div class="project-card" v-for="p in projects.slice(0,4)" :key="p.id"
        @click="openProject(p)">
        <div class="project-cover" :style="{ background: coverGradient(p) }">
          <span class="project-cover-label">{{ p.title }}</span>
        </div>
        <div class="project-info">
          <div class="project-title">{{ p.title }}</div>
          <div class="project-meta">
            <span class="status-dot" :class="p.status"></span>
            {{ statusLabel(p.status) }} · {{ p.current_page }}/{{ p.total_pages }} 页
          </div>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">
      <div class="empty-icon">📁</div>
      <div class="empty-text">还没有项目，快来创建第一个吧！</div>
      <el-button type="primary" @click="$router.push('/projects')">创建项目</el-button>
    </div>

    <!-- Quick actions -->
    <div class="section-title" style="margin-top:8px"><span>快速操作</span></div>
    <div class="grid-4">
      <div class="quick-action-card" v-for="qa in quickActions" :key="qa.label"
        @click="$router.push(qa.to)">
        <div class="qa-icon" :style="{ background: qa.bg }">{{ qa.icon }}</div>
        <div class="qa-label">{{ qa.label }}</div>
        <div class="qa-desc">{{ qa.desc }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { projectsApi } from '@/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const projects = ref([])
const statsData = ref({ total_projects: 0, monthly_creations: 0, total_ai_generates: 0, total_assets: 0 })

const stats = computed(() => [
  { value: statsData.value.total_projects, label: '项目总数', color: '#1a1a2e' },
  { value: statsData.value.monthly_creations, label: '本月创作', color: '#6366f1' },
  { value: statsData.value.total_ai_generates, label: 'AI 生成次数', color: '#10b981' },
  { value: statsData.value.total_assets, label: '素材数量', color: '#f59e0b' },
])

const quickActions = [
  { icon: '🎬', label: '模板中心', desc: '从100+爆款模板开始', to: '/templates', bg: 'linear-gradient(135deg,#667eea,#764ba2)' },
  { icon: '✨', label: 'AI 生成', desc: '描述想法，AI帮你生成分镜', to: '/ai-generate', bg: 'linear-gradient(135deg,#f093fb,#f5576c)' },
  { icon: '👤', label: '角色库', desc: '管理你的漫剧角色', to: '/characters', bg: 'linear-gradient(135deg,#4facfe,#00f2fe)' },
  { icon: '🗂️', label: '素材管理', desc: '上传和管理素材资产', to: '/assets', bg: 'linear-gradient(135deg,#43e97b,#38f9d7)' },
]

const GRADIENTS = [
  'linear-gradient(135deg,#667eea 0%,#764ba2 100%)',
  'linear-gradient(135deg,#f093fb 0%,#f5576c 100%)',
  'linear-gradient(135deg,#4facfe 0%,#00f2fe 100%)',
  'linear-gradient(135deg,#43e97b 0%,#38f9d7 100%)',
  'linear-gradient(135deg,#fa709a 0%,#fee140 100%)',
  'linear-gradient(135deg,#a18cd1 0%,#fbc2eb 100%)',
]
function coverGradient(p) { return GRADIENTS[p.id % GRADIENTS.length] }

function statusLabel(s) {
  return { draft: '草稿', in_progress: '创作中', review: '待审核', completed: '已完成' }[s] || s
}

function openProject(p) {
  router.push(`/workspace/${p.id}`)
}

onMounted(async () => {
  try {
    await authStore.fetchMe()
    const [ps, st] = await Promise.all([
      projectsApi.list({ limit: 8 }),
      projectsApi.stats(),
    ])
    projects.value = ps
    statsData.value = st
  } catch (e) {
    ElMessage.error(e.message)
  }
})
</script>

<style scoped>
.welcome-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
}
.welcome-title { font-size: 22px; font-weight: 700; margin-bottom: 4px; }
.welcome-sub { font-size: 14px; color: var(--color-text-secondary); }
.project-cover { position: relative; }
.project-cover-label {
  position: relative; z-index: 1;
  font-size: 18px; font-weight: 700; color: rgba(255,255,255,0.5);
  letter-spacing: 1px;
}

.quick-action-card {
  background: #fff;
  border-radius: var(--radius-md);
  padding: 20px;
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all 0.25s ease;
}
.quick-action-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.qa-icon {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; margin-bottom: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.qa-label { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.qa-desc { font-size: 12px; color: var(--color-text-secondary); }
</style>
