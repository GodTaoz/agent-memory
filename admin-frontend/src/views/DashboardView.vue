<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  Connection,
  Coin,
  User,
  Key,
  TrendCharts,
  Timer,
} from '@element-plus/icons-vue'

interface SystemStats {
  redis_connected: boolean
  redis_memory_used: string
  redis_keys_count: number
  total_memories: number
  total_agents: number
  total_api_keys: number
  uptime_seconds: number
  requests_today: number
  avg_response_time_ms: number
}

const stats = ref<SystemStats | null>(null)
const loading = ref(true)

async function fetchStats() {
  try {
    const response = await axios.get('/admin/api/stats')
    stats.value = response.data
  } catch (error) {
    ElMessage.error('获取系统状态失败')
  } finally {
    loading.value = false
  }
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (days > 0) return `${days}天${hours}小时`
  if (hours > 0) return `${hours}小时${minutes}分钟`
  return `${minutes}分钟`
}

onMounted(() => {
  fetchStats()
})
</script>

<template>
  <div class="dashboard">
    <h2 class="page-title">仪表盘</h2>
    
    <div v-loading="loading" class="stats-grid">
      <!-- Status Cards -->
      <el-card class="stat-card card-hover" shadow="hover">
        <div class="stat-icon" style="background-color: rgba(103, 194, 58, 0.1);">
          <el-icon :size="24" color="#67c23a"><Connection /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">Redis 状态</div>
          <div class="stat-value">
            <span class="status-dot" :class="stats?.redis_connected ? 'success' : 'danger'" />
            {{ stats?.redis_connected ? '已连接' : '未连接' }}
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card card-hover" shadow="hover">
        <div class="stat-icon" style="background-color: rgba(64, 158, 255, 0.1);">
          <el-icon :size="24" color="#409eff"><Coin /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">总记忆数</div>
          <div class="stat-value">{{ stats?.total_memories || 0 }}</div>
        </div>
      </el-card>
      
      <el-card class="stat-card card-hover" shadow="hover">
        <div class="stat-icon" style="background-color: rgba(230, 162, 60, 0.1);">
          <el-icon :size="24" color="#e6a23c"><User /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">活跃 Agent</div>
          <div class="stat-value">{{ stats?.total_agents || 0 }}</div>
        </div>
      </el-card>
      
      <el-card class="stat-card card-hover" shadow="hover">
        <div class="stat-icon" style="background-color: rgba(144, 147, 153, 0.1);">
          <el-icon :size="24" color="#909399"><Key /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">API Keys</div>
          <div class="stat-value">{{ stats?.total_api_keys || 0 }}</div>
        </div>
      </el-card>
      
      <el-card class="stat-card card-hover" shadow="hover">
        <div class="stat-icon" style="background-color: rgba(92, 124, 250, 0.1);">
          <el-icon :size="24" color="#5c7cfa"><TrendCharts /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">今日请求</div>
          <div class="stat-value">{{ stats?.requests_today || 0 }}</div>
        </div>
      </el-card>
      
      <el-card class="stat-card card-hover" shadow="hover">
        <div class="stat-icon" style="background-color: rgba(103, 194, 58, 0.1);">
          <el-icon :size="24" color="#67c23a"><Timer /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">平均响应</div>
          <div class="stat-value">{{ stats?.avg_response_time_ms || 0 }}ms</div>
        </div>
      </el-card>
    </div>
    
    <!-- System Info -->
    <el-row :gutter="20" style="margin-top: 24px;">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>系统信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="运行时间">
              {{ stats ? formatUptime(stats.uptime_seconds) : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Redis 内存">
              {{ stats?.redis_memory_used || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="Redis Keys">
              {{ stats?.redis_keys_count || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/api-keys')">
              管理 API Keys
            </el-button>
            <el-button @click="$router.push('/memories')">
              查看记忆
            </el-button>
            <el-button @click="$router.push('/logs')">
              查看日志
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 0;
}

.page-title {
  margin-bottom: 24px;
  font-size: 24px;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-actions .el-button {
  width: 100%;
}
</style>
