<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-icon">🎬</div>
        <span class="logo-text">漫剧工坊</span>
      </div>

      <nav class="sidebar-nav">
        <router-link v-for="item in navItems" :key="item.to"
          :to="item.to" class="nav-item"
          :class="{ active: isActive(item.to) }">
          <el-icon><component :is="item.icon" /></el-icon>
          {{ item.label }}
        </router-link>
      </nav>

      <div class="sidebar-footer" @click="handleLogout">
        <div class="user-avatar">
          <el-icon><User /></el-icon>
        </div>
        <div>
          <div class="user-name">{{ authStore.user?.nickname || '创作者' }}</div>
        </div>
      </div>
    </aside>

    <!-- Main -->
    <div class="main-wrapper">
      <header class="top-bar">
        <el-input v-model="searchKeyword" placeholder="搜索项目、角色或素材..."
          prefix-icon="Search" class="search-box" @keyup.enter="handleSearch" clearable />
        <div class="top-bar-actions">
          <el-button type="primary" @click="$router.push('/projects')" class="btn-primary" style="border-radius:8px">
            <el-icon><Plus /></el-icon> 创建项目
          </el-button>
          <el-badge :value="0" :hidden="true">
            <el-button circle :icon="Bell" />
          </el-badge>
          <el-avatar :size="34"
            style="background: linear-gradient(135deg,#6366f1,#8b5cf6); cursor:pointer; font-weight:600"
            @click="$router.push('/settings')">
            {{ (authStore.user?.nickname || 'U')[0].toUpperCase() }}
          </el-avatar>
        </div>
      </header>

      <main class="page-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox } from 'element-plus'
import { House, Folder, Edit, MagicStick, User, Picture, Box, Setting, Bell, Plus } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const searchKeyword = ref('')

const navItems = [
  { to: '/', label: '首页', icon: 'House' },
  { to: '/projects', label: '项目管理', icon: 'Folder' },
  { to: '/workspace/1', label: '创作工作台', icon: 'Edit' },
  { to: '/ai-generate', label: 'AI 生成', icon: 'MagicStick' },
  { to: '/characters', label: '角色库', icon: 'User' },
  { to: '/scenes', label: '场景库', icon: 'Picture' },
  { to: '/assets', label: '素材管理', icon: 'Box' },
  { to: '/settings', label: '设置', icon: 'Setting' },
]

function isActive(to) {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}

function handleSearch() {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/projects', query: { keyword: searchKeyword.value } })
  }
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '退出登录', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    authStore.logout()
    router.push('/login')
  } catch {}
}
</script>
