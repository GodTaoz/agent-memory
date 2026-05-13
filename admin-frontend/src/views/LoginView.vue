<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!password.value) {
    ElMessage.warning('请输入密码')
    return
  }
  
  loading.value = true
  
  try {
    const success = await authStore.login(password.value)
    
    if (success) {
      ElMessage.success('登录成功')
      router.push('/dashboard')
    } else {
      ElMessage.error('密码错误')
    }
  } catch (error) {
    ElMessage.error('登录失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container gradient-bg">
    <el-card class="login-card" shadow="always">
      <template #header>
        <div class="login-header">
          <h1 class="gradient-accent">Agent Memory</h1>
          <p>管理面板</p>
        </div>
      </template>
      
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="请输入管理员密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            style="width: 100%;"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>默认密码: admin123</p>
        <p>首次登录后请及时修改密码</p>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 400px;
  border-radius: var(--radius-lg);
}

.login-header {
  text-align: center;
}

.login-header h1 {
  font-size: 28px;
  margin-bottom: 8px;
}

.login-header p {
  color: var(--text-secondary);
  font-size: 14px;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 12px;
  color: var(--text-muted);
}

.login-footer p {
  margin: 4px 0;
}
</style>
