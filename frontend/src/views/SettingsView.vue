<template>
  <div class="fade-in-up">
    <div class="page-header">
      <h1 class="page-title">系统设置</h1>
    </div>

    <div style="max-width:640px">
      <el-card class="settings-card">
        <template #header><span style="font-weight:700">个人信息</span></template>
        <el-form :model="profileForm" label-position="top">
          <el-form-item label="昵称">
            <el-input v-model="profileForm.nickname" placeholder="你的显示名称" />
          </el-form-item>
          <el-form-item label="用户名（不可修改）">
            <el-input :value="authStore.user?.username" disabled />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input :value="authStore.user?.email" disabled />
          </el-form-item>
        </el-form>
      </el-card>

      <el-card class="settings-card" style="margin-top:16px">
        <template #header><span style="font-weight:700">账号信息</span></template>
        <div class="info-row">
          <span class="info-label">用户类型</span>
          <el-tag :type="authStore.user?.is_vip ? 'warning' : 'info'">
            {{ authStore.user?.is_vip ? '✨ VIP用户' : '免费用户' }}
          </el-tag>
        </div>
        <div class="info-row">
          <span class="info-label">今日生成次数</span>
          <span>{{ authStore.user?.daily_generate_count || 0 }} / 10</span>
        </div>
        <div class="info-row">
          <span class="info-label">注册时间</span>
          <span>{{ authStore.user?.created_at?.slice(0,10) || '--' }}</span>
        </div>
      </el-card>

      <el-card class="settings-card" style="margin-top:16px">
        <template #header><span style="font-weight:700">关于平台</span></template>
        <div class="info-row">
          <span class="info-label">版本</span>
          <span>v1.0.0</span>
        </div>
        <div class="info-row">
          <span class="info-label">后端 API</span>
          <span>http://localhost:8000/api/docs</span>
        </div>
        <div class="info-row">
          <span class="info-label">技术栈</span>
          <span>Vue3 + Vite + FastAPI + MySQL</span>
        </div>
      </el-card>

      <div style="margin-top:24px;display:flex;gap:12px">
        <el-button type="danger" @click="handleLogout">退出登录</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const profileForm = ref({ nickname: authStore.user?.nickname || '' })

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定退出登录？', '退出', { type: 'warning' })
    authStore.logout()
    router.push('/login')
  } catch {}
}
</script>

<style scoped>
.settings-card :deep(.el-card__header) { border-bottom: 1px solid var(--color-border); padding: 16px 20px; }
.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 14px;
}
.info-row:last-child { border-bottom: none; }
.info-label { color: var(--color-text-secondary); }
</style>
