<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useThemeStore } from '../stores/theme'
import { useAuthStore } from '../stores/auth'
import {
  Odometer,
  Key,
  Coin,
  User,
  Document,
  Setting,
  Sunny,
  Moon,
  Monitor,
  Fold,
  Expand,
  SwitchButton,
} from '@element-plus/icons-vue'

const router = useRouter()
const themeStore = useThemeStore()
const authStore = useAuthStore()

const isCollapsed = ref(false)

const activeMenu = computed(() => router.currentRoute.value.path)

const themeIcon = computed(() => {
  if (themeStore.mode === 'light') return Sunny
  if (themeStore.mode === 'dark') return Moon
  return Monitor
})

const themeLabel = computed(() => {
  if (themeStore.mode === 'light') return '亮色模式'
  if (themeStore.mode === 'dark') return '暗色模式'
  return '跟随系统'
})

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

function cycleTheme() {
  if (themeStore.mode === 'light') {
    themeStore.setTheme('dark')
  } else if (themeStore.mode === 'dark') {
    themeStore.setTheme('system')
  } else {
    themeStore.setTheme('light')
  }
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="admin-layout">
    <!-- Sidebar -->
    <el-aside :width="isCollapsed ? '64px' : '240px'" class="sidebar">
      <div class="logo" :class="{ collapsed: isCollapsed }">
        <span v-if="!isCollapsed" class="gradient-accent">Agent Memory</span>
        <span v-else class="gradient-accent">AM</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        
        <el-menu-item index="/api-keys">
          <el-icon><Key /></el-icon>
          <template #title>API Keys</template>
        </el-menu-item>
        
        <el-menu-item index="/memories">
          <el-icon><Coin /></el-icon>
          <template #title>记忆管理</template>
        </el-menu-item>
        
        <el-menu-item index="/agents">
          <el-icon><User /></el-icon>
          <template #title>Agent管理</template>
        </el-menu-item>
        
        <el-menu-item index="/logs">
          <el-icon><Document /></el-icon>
          <template #title>操作日志</template>
        </el-menu-item>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- Main Content -->
    <el-container class="main-container">
      <!-- Header -->
      <el-header class="header">
        <div class="header-left">
          <el-button :icon="isCollapsed ? Expand : Fold" @click="toggleCollapse" />
        </div>
        
        <div class="header-right">
          <el-tooltip :content="themeLabel" placement="bottom">
            <el-button :icon="themeIcon" @click="cycleTheme" />
          </el-tooltip>
          
          <el-dropdown trigger="click">
            <el-button>
              <el-icon><User /></el-icon>
              <span style="margin-left: 8px;">管理员</span>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/settings')">
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- Content -->
      <el-main class="content">
        <slot />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-layout {
  height: 100vh;
}

.sidebar {
  background-color: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  transition: width var(--transition-speed);
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
  border-bottom: 1px solid var(--border-color);
}

.logo.collapsed {
  font-size: 16px;
}

.sidebar-menu {
  border-right: none;
  height: calc(100vh - 60px);
}

.main-container {
  background-color: var(--bg-secondary);
}

.header {
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.content {
  padding: 24px;
}
</style>
