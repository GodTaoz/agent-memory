<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Refresh, Warning, Info, SuccessFilled } from '@element-plus/icons-vue'

interface LogEntry {
  timestamp: string
  level: string
  category?: string
  message: string
  details?: Record<string, any>
  ip_address?: string
}

const logs = ref<LogEntry[]>([])
const loading = ref(true)
const selectedLevel = ref('')
const limit = ref(100)

async function fetchLogs() {
  loading.value = true
  try {
    const params: any = { limit: limit.value }
    if (selectedLevel.value) {
      params.level = selectedLevel.value
    }
    
    const response = await axios.get('/admin/api/logs', { params })
    logs.value = response.data
  } catch (error) {
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

function getLevelIcon(level: string) {
  switch (level.toLowerCase()) {
    case 'error':
      return Warning
    case 'warning':
      return Warning
    case 'info':
      return Info
    case 'success':
      return SuccessFilled
    default:
      return Info
  }
}

function getLevelType(level: string): string {
  switch (level.toLowerCase()) {
    case 'error':
      return 'danger'
    case 'warning':
      return 'warning'
    case 'info':
      return 'info'
    case 'success':
      return 'success'
    default:
      return 'info'
  }
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleString()
}

function formatDetails(details: Record<string, any> | undefined): string {
  if (!details) return '-'
  return JSON.stringify(details, null, 2)
}

onMounted(() => {
  fetchLogs()
})
</script>

<template>
  <div class="logs">
    <div class="page-header">
      <h2 class="page-title">操作日志</h2>
      
      <el-button :icon="Refresh" @click="fetchLogs">
        刷新
      </el-button>
    </div>
    
    <!-- Filter -->
    <el-card shadow="hover" style="margin-bottom: 20px;">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-select v-model="selectedLevel" placeholder="日志级别" clearable @change="fetchLogs" style="width: 100%;">
            <el-option label="全部" value="" />
            <el-option label="Info" value="info" />
            <el-option label="Warning" value="warning" />
            <el-option label="Error" value="error" />
            <el-option label="Success" value="success" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-select v-model="limit" placeholder="显示数量" @change="fetchLogs" style="width: 100%;">
            <el-option :label="50" :value="50" />
            <el-option :label="100" :value="100" />
            <el-option :label="200" :value="200" />
            <el-option :label="500" :value="500" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- Log List -->
    <el-card shadow="hover">
      <el-table :data="logs" v-loading="loading" style="width: 100%;">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level) as any" effect="dark">
              <el-icon style="margin-right: 4px;">
                <component :is="getLevelIcon(row.level)" />
              </el-icon>
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="category" label="分类" width="120" />
        
        <el-table-column prop="message" label="消息" min-width="300" />
        
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        
        <el-table-column label="详情" width="100" type="expand">
          <template #default="{ row }">
            <pre class="log-details">{{ formatDetails(row.details) }}</pre>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="logs.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无日志记录" />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
}

.log-details {
  font-family: monospace;
  background-color: var(--bg-tertiary);
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.empty-state {
  padding: 40px 0;
}
</style>
