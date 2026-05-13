<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Edit, Delete, Download, ArrowDown } from '@element-plus/icons-vue'

interface Memory {
  key: string
  content: string
  tags: string[]
  created_at: string
  updated_at: string
  agent_id: string | null
}

const memories = ref<Memory[]>([])
const loading = ref(true)
const searchQuery = ref('')
const selectedTag = ref('')
const currentPage = ref(1)
const pageSize = ref(50)
const total = ref(0)

const showEditDialog = ref(false)
const editingMemory = ref<Memory | null>(null)
const editForm = ref({
  content: '',
  tags: [] as string[],
})

async function fetchMemories() {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    
    if (selectedTag.value) {
      params.tag = selectedTag.value
    }
    
    const response = await axios.get('/admin/api/memories', { params })
    memories.value = response.data
    total.value = response.data.length // TODO: Get total from API
  } catch (error) {
    ElMessage.error('获取记忆列表失败')
  } finally {
    loading.value = false
  }
}

async function deleteMemory(memory: Memory) {
  try {
    await ElMessageBox.confirm(
      `确定要删除记忆 "${memory.key}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    await axios.delete(`/admin/api/memories/${memory.key}`)
    ElMessage.success('删除成功')
    fetchMemories()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function openEditDialog(memory: Memory) {
  editingMemory.value = memory
  editForm.value = {
    content: memory.content,
    tags: [...memory.tags],
  }
  showEditDialog.value = true
}

async function saveMemory() {
  if (!editingMemory.value) return
  
  try {
    await axios.put(`/admin/api/memories/${editingMemory.value.key}`, editForm.value)
    ElMessage.success('保存成功')
    showEditDialog.value = false
    fetchMemories()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

async function exportJson() {
  try {
    const response = await axios.get('/admin/api/memories/export/json', {
      responseType: 'blob',
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'memories.json')
    document.body.appendChild(link)
    link.click()
    link.remove()
    
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

async function exportCsv() {
  try {
    const response = await axios.get('/admin/api/memories/export/csv', {
      responseType: 'blob',
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'memories.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchMemories()
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchMemories()
}

onMounted(() => {
  fetchMemories()
})
</script>

<template>
  <div class="memories">
    <div class="page-header">
      <h2 class="page-title">记忆管理</h2>
      
      <div class="header-actions">
        <el-dropdown @command="exportJson">
          <el-button :icon="Download">
            导出 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="exportJson">导出 JSON</el-dropdown-item>
              <el-dropdown-item @click="exportCsv">导出 CSV</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- Search Bar -->
    <el-card shadow="hover" style="margin-bottom: 20px;">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-input
            v-model="searchQuery"
            placeholder="搜索记忆内容..."
            :prefix-icon="Search"
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
        </el-col>
        <el-col :span="8">
          <el-input
            v-model="selectedTag"
            placeholder="按标签筛选..."
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
        </el-col>
        <el-col :span="4">
          <el-button type="primary" style="width: 100%;" @click="handleSearch">
            搜索
          </el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- Memory List -->
    <el-card shadow="hover">
      <el-table :data="memories" v-loading="loading" style="width: 100%;">
        <el-table-column prop="key" label="Key" min-width="200">
          <template #default="{ row }">
            <code class="memory-key">{{ row.key }}</code>
          </template>
        </el-table-column>
        
        <el-table-column prop="content" label="内容" min-width="300">
          <template #default="{ row }">
            <div class="memory-content">{{ row.content }}</div>
          </template>
        </el-table-column>
        
        <el-table-column prop="tags" label="标签" min-width="150">
          <template #default="{ row }">
            <el-tag
              v-for="tag in row.tags"
              :key="tag"
              size="small"
              style="margin-right: 4px;"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="agent_id" label="Agent" width="120" />
        
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button-group>
              <el-button :icon="Edit" @click="openEditDialog(row)" />
              <el-button :icon="Delete" type="danger" @click="deleteMemory(row)" />
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="memories.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无记忆数据" />
      </div>
      
      <!-- Pagination -->
      <div v-if="total > pageSize" class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
    
    <!-- Edit Dialog -->
    <el-dialog v-model="showEditDialog" title="编辑记忆" width="600px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="Key">
          <el-input :value="editingMemory?.key" disabled />
        </el-form-item>
        
        <el-form-item label="内容" required>
          <el-input v-model="editForm.content" type="textarea" :rows="6" />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-select
            v-model="editForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入标签后回车"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMemory">保存</el-button>
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

.header-actions {
  display: flex;
  gap: 12px;
}

.memory-key {
  font-family: monospace;
  background-color: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
}

.memory-content {
  max-height: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.empty-state {
  padding: 40px 0;
}
</style>
