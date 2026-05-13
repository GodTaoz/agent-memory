<script setup lang="ts">
import { ref } from 'vue'
import { useThemeStore } from '../stores/theme'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Lock, Sunny, Moon, Monitor } from '@element-plus/icons-vue'

const themeStore = useThemeStore()
const authStore = useAuthStore()

const showPasswordDialog = ref(false)
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

async function changePassword() {
  if (!passwordForm.value.oldPassword || !passwordForm.value.newPassword) {
    ElMessage.warning('请填写完整')
    return
  }
  
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    ElMessage.error('两次密码不一致')
    return
  }
  
  if (passwordForm.value.newPassword.length < 6) {
    ElMessage.error('密码长度不能少于6位')
    return
  }
  
  try {
    const success = await authStore.changePassword(
      passwordForm.value.oldPassword,
      passwordForm.value.newPassword
    )
    
    if (success) {
      ElMessage.success('密码修改成功，请重新登录')
      showPasswordDialog.value = false
      passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
      await authStore.logout()
    } else {
      ElMessage.error('旧密码错误')
    }
  } catch (error) {
    ElMessage.error('修改失败')
  }
}

function setTheme(mode: 'light' | 'dark' | 'system') {
  themeStore.setTheme(mode)
  ElMessage.success(`已切换到${mode === 'light' ? '亮色' : mode === 'dark' ? '暗色' : '系统'}模式`)
}
</script>

<template>
  <div class="settings">
    <h2 class="page-title">系统设置</h2>
    
    <el-row :gutter="24">
      <!-- Theme Settings -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>主题设置</span>
          </template>
          
          <div class="theme-options">
            <div
              class="theme-option"
              :class="{ active: themeStore.mode === 'light' }"
              @click="setTheme('light')"
            >
              <el-icon :size="32"><Sunny /></el-icon>
              <span>亮色模式</span>
            </div>
            
            <div
              class="theme-option"
              :class="{ active: themeStore.mode === 'dark' }"
              @click="setTheme('dark')"
            >
              <el-icon :size="32"><Moon /></el-icon>
              <span>暗色模式</span>
            </div>
            
            <div
              class="theme-option"
              :class="{ active: themeStore.mode === 'system' }"
              @click="setTheme('system')"
            >
              <el-icon :size="32"><Monitor /></el-icon>
              <span>跟随系统</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- Security Settings -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>安全设置</span>
          </template>
          
          <div class="security-actions">
            <el-button type="primary" :icon="Lock" @click="showPasswordDialog = true">
              修改密码
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- About -->
    <el-card shadow="hover" style="margin-top: 24px;">
      <template #header>
        <span>关于</span>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="项目名称">Agent Memory</el-descriptions-item>
        <el-descriptions-item label="版本">1.0.0</el-descriptions-item>
        <el-descriptions-item label="作者">GodTaoz</el-descriptions-item>
        <el-descriptions-item label="协议">MIT</el-descriptions-item>
        <el-descriptions-item label="GitHub">
          <a href="https://github.com/GodTaoz/agent-memory" target="_blank">
            https://github.com/GodTaoz/agent-memory
          </a>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
    
    <!-- Password Dialog -->
    <el-dialog v-model="showPasswordDialog" title="修改密码" width="400px">
      <el-form :model="passwordForm" label-width="100px">
        <el-form-item label="旧密码" required>
          <el-input v-model="passwordForm.oldPassword" type="password" show-password />
        </el-form-item>
        
        <el-form-item label="新密码" required>
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        
        <el-form-item label="确认密码" required>
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="changePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
}

.theme-options {
  display: flex;
  gap: 20px;
}

.theme-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-speed);
}

.theme-option:hover {
  border-color: var(--accent-color);
  background-color: rgba(92, 124, 250, 0.05);
}

.theme-option.active {
  border-color: var(--accent-color);
  background-color: rgba(92, 124, 250, 0.1);
  color: var(--accent-color);
}

.security-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

a {
  color: var(--accent-color);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
