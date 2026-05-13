<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { User, Coin, Key, Timer } from '@element-plus/icons-vue'

interface Agent {
  agent_id: string
  name: string | null
  permissions: string
  last_active: string | null
  memory_count: number
  api_key_preview: string
}

const agents = ref<Agent[]>([])
const loading = ref(true)

async function fetchAgents() {
  try {
    const response = await axios.get('/admin/api/agents')
    agents.value = response.data
  } catch (error) {
    ElMessage.error('获取Agent列表失败')
  } finally {
    loading.value = false
  }
}

function formatTime(time: string | null): string {
  if (!time) return '从未活跃'
  return new Date(time).toLocaleString()
}

onMounted(() => {
  fetchAgents()
})
</script>

<template>
  <div class="agents">
    <div class="page-header">
      <h2 class="page-title">Agent 管理</h2>
    </div>
    
    <el-card shadow="hover">
      <el-table :data="agents" v-loading="loading" style="width: 100%;">
        <el-table-column prop="agent_id" label="Agent ID" min-width="150">
          <template #default="{ row }">
            <div class="agent-id">
              <el-icon><User /></el-icon>
              <span>{{ row.agent_id }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="name" label="名称" min-width="120">
          <template #default="{ row }">
            {{ row.name || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="permissions" label="权限" width="120">
          <template #default="{ row }">
            <el-tag :type="row.permissions === 'admin' ? 'danger' : row.permissions === 'read_write' ? 'success' : 'info'">
              {{ row.permissions === 'admin' ? '管理员' : row.permissions === 'read_write' ? '读写' : '只读' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="memory_count" label="记忆数量" width="120" align="center">
          <template #default="{ row }">
            <div class="stat-cell">
              <el-icon><Coin /></el-icon>
              <span>{{ row.memory_count }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="api_key_preview" label="API Key" min-width="150">
          <template #default="{ row }">
            <code class="key-preview">{{ row.api_key_preview }}</code>
          </template>
        </el-table-column>
        
        <el-table-column prop="last_active" label="最后活跃" width="180">
          <template #default="{ row }">
            <div class="time-cell">
              <el-icon><Timer /></el-icon>
              <span>{{ formatTime(row.last_active) }}</span>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="agents.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无Agent接入" />
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

.agent-id {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.time-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.key-preview {
  font-family: monospace;
  background-color: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
}

.empty-state {
  padding: 40px 0;
}
</style>
