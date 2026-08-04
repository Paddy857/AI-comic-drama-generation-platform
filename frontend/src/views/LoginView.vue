<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="bg-orb orb1"></div>
      <div class="bg-orb orb2"></div>
      <div class="bg-orb orb3"></div>
    </div>

    <div class="login-container">
      <div class="login-card fade-in-up">
        <div class="login-header">
          <div class="logo-big">🎬</div>
          <h1 class="login-title">漫剧工坊</h1>
          <p class="login-subtitle">AI 驱动的漫剧全流程制作平台</p>
        </div>

        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" @submit.prevent="handleLogin">
              <el-form-item prop="username">
                <el-input v-model="loginForm.username" placeholder="用户名" prefix-icon="User" size="large" />
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="loginForm.password" type="password" placeholder="密码"
                  prefix-icon="Lock" size="large" show-password @keyup.enter="handleLogin" />
              </el-form-item>
              <el-button type="primary" size="large" :loading="loading" @click="handleLogin"
                style="width:100%; border-radius:10px; height:44px; font-size:15px; font-weight:600;
                background: linear-gradient(135deg,#6366f1,#4f46e5); border:none; margin-top:8px">
                登录
              </el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef">
              <el-form-item prop="username">
                <el-input v-model="registerForm.username" placeholder="用户名（3-20位）" prefix-icon="User" size="large" />
              </el-form-item>
              <el-form-item prop="email">
                <el-input v-model="registerForm.email" placeholder="邮箱" prefix-icon="Message" size="large" />
              </el-form-item>
              <el-form-item prop="nickname">
                <el-input v-model="registerForm.nickname" placeholder="昵称（可选）" prefix-icon="EditPen" size="large" />
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="registerForm.password" type="password" placeholder="密码（6位以上）"
                  prefix-icon="Lock" size="large" show-password />
              </el-form-item>
              <el-button type="primary" size="large" :loading="loading" @click="handleRegister"
                style="width:100%; border-radius:10px; height:44px; font-size:15px; font-weight:600;
                background: linear-gradient(135deg,#6366f1,#4f46e5); border:none; margin-top:8px">
                创建账号
              </el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>

        <div class="demo-hint">
          <el-icon><InfoFilled /></el-icon>
          演示账号：admin / admin123
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref()
const registerFormRef = ref()

const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ username: '', email: '', nickname: '', password: '' })

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名3-20位', trigger: 'blur' },
  ],
  email: [{ required: true, type: 'email', message: '请输入有效邮箱', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
}

async function handleLogin() {
  await loginFormRef.value?.validate()
  loading.value = true
  try {
    await authStore.login(loginForm.value)
    ElMessage.success('登录成功，欢迎回来！')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  await registerFormRef.value?.validate()
  loading.value = true
  try {
    await authStore.register(registerForm.value)
    ElMessage.success('注册成功，开始创作吧！')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-bg { position: absolute; inset: 0; pointer-events: none; }
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.25;
}
.orb1 { width: 400px; height: 400px; background: #6366f1; top: -100px; left: -100px; }
.orb2 { width: 300px; height: 300px; background: #8b5cf6; bottom: -80px; right: -80px; }
.orb3 { width: 200px; height: 200px; background: #3b82f6; top: 50%; left: 60%; }

.login-container { position: relative; z-index: 1; width: 100%; max-width: 420px; padding: 20px; }

.login-card {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 24px;
  padding: 40px;
  box-shadow: 0 24px 64px rgba(0,0,0,0.4);
}

.login-header { text-align: center; margin-bottom: 32px; }
.logo-big { font-size: 48px; margin-bottom: 12px; }
.login-title {
  font-size: 26px;
  font-weight: 800;
  color: #fff;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}
.login-subtitle { font-size: 14px; color: rgba(255,255,255,0.5); }

.login-tabs :deep(.el-tabs__item) { color: rgba(255,255,255,0.6); font-size: 15px; }
.login-tabs :deep(.el-tabs__item.is-active) { color: #818cf8; }
.login-tabs :deep(.el-tabs__active-bar) { background: #818cf8; }
.login-tabs :deep(.el-tabs__nav-wrap::after) { background: rgba(255,255,255,0.1); }
.login-tabs :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.15);
}
.login-tabs :deep(.el-input__inner) { color: #fff; }
.login-tabs :deep(.el-input__inner::placeholder) { color: rgba(255,255,255,0.35); }

.demo-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 20px;
  text-align: center;
  justify-content: center;
  font-size: 12px;
  color: rgba(255,255,255,0.35);
}
</style>
