<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Copy } from '@element-plus/icons-vue'

interface ApiKey {
  key_preview: string
  name: string
  permissions: string
  description: string | null
  created_at: string
  last_used: string | null
  usage_count: number
}

const apiKeys = ref<ApiKey[]>([])
const loading = ref(true)
const showCreateDialog = ref(false)

const newKey = ref({
  name: '',
  permissions: 'read',
  description: '',
})

async function fetchApiKeys() {
  try {
    const response = await axios.get('/admin/api/api-keys')
    apiKeys.value = response.data
  } catch (error) {
    ElMessage.error('获取API Keys失败')
  } finally {
    loading.value = false
  }
}

async function createApiKey() {
  try {
    await axios.post('/admin/api/api-keys', newKey.value)
    ElMessage.success('API Key创建成功')
    showCreateDialog.value = false
    newKey.value = { name: '', permissions: 'read', description: '' }
    fetchApiKeys()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

async function deleteApiKey(key: ApiKey) {
  try {
    await ElMessageBox.confirm(
      `确定要删除API Key "${key.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    await axios.delete(`/admin/api/api-keys/${key.key_preview}`)
    ElMessage.success('删除成功')
    fetchApiKeys()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function copyKey(key: string) {
  navigator.clipboard.writeText(key)
  ElMessage.success('已复制到剪贴板')
}

const permissionLabels: Record<string, string> = {
  read: '只读',
  read_write: '读写',
  admin: '管理员',
}

const permissionTypes: Record<string, string> = {
  read: 'info',
  read_write: 'success',
  admin: 'danger',
}

onMounted(() => {
  fetchApiKeys()
})
</script>

<template>
  <div class="api-keys">
    <div class="page-header">
      <h2 class="page-title">API Keys 管理</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
        创建 API Key
      </el-button>
    </div>
    
    <el-card shadow="hover">
      <el-table :data="apiKeys" v-loading="loading" style="width: 100%;">
        <el-table-column prop="name" label="名称" min-width="120" />
        
        <el-table-column prop="key_preview" label="Key预览" min-width="150">
          <template #default="{ row }">
            <code class="key-preview">{{ row.key_preview }}</code>
          </template>
        </el-table-column>
        
        <el-table-column prop="permissions" label="权限" width="100">
          <template #default="{ row }">
            <el-tag :type="permissionTypes[row.permissions] as any">
              {{ permissionLabels[row.permissions] }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="描述" min-width="150" />
        
        <el-table-column prop="created_at" label="创建时间" width="180" />
        
        <el-table-column prop="usage_count" label="使用次数" width="100" align="center" />
        
        <el-table-column label="操作" width="150" align="center">
          <template #default="{ row }">
            <el-button-group>
              <el-button :icon="Copy" @click="copyKey(row.key_preview)" />
              <el-button :icon="Delete" type="danger" @click="deleteApiKey(row)" />
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="apiKeys.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无API Key" />
      </div>
    </el-card>
    
    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="创建 API Key" width="500px">
      <el-form :model="newKey" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="newKey.name" placeholder="例如: 我的Agent" />
        </el-form-item>
        
        <el-form-item label="权限" required>
          <el-select v-model="newKey.permissions" style="width: 100%;">
            <el-option label="只读" value="read" />
            <el-option label="读写" value="read_write" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="newKey.description" type="textarea" placeholder="可选描述" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createApiKey">创建</el-button>
      </template>
    </el-dialog>
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
