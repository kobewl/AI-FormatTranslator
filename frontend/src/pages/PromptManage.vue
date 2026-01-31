<template>
  <div class="prompt-page">
    <a-card title="提示词管理" class="prompt-card">
      <!-- 工具栏 -->
      <div class="toolbar">
        <a-space>
          <a-select
            v-model:value="categoryFilter"
            style="width: 150px"
            placeholder="筛选分类"
            allowClear
            @change="handleFilterChange"
          >
            <a-select-option value="">全部分类</a-select-option>
            <a-select-option value="general">通用</a-select-option>
            <a-select-option value="technical">技术</a-select-option>
            <a-select-option value="academic">学术</a-select-option>
            <a-select-option value="literary">文学</a-select-option>
          </a-select>

          <a-button type="primary" @click="handleCreate">
            <PlusOutlined />
            新建提示词
          </a-button>

          <a-button @click="handleRefresh">
            <ReloadOutlined />
            刷新
          </a-button>
        </a-space>
      </div>

      <!-- 提示词列表 -->
      <a-table
        :columns="columns"
        :data-source="prompts"
        :loading="loading"
        :pagination="{
          current: page,
          pageSize: pageSize,
          total: total,
          showTotal: (total) => `共 ${total} 条`
        }"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="prompt-name">
              <BulbOutlined style="margin-right: 8px; color: #faad14;" />
              <span>{{ record.name }}</span>
              <a-tag v-if="record.is_default" color="blue" style="margin-left: 8px;">默认</a-tag>
            </div>
          </template>

          <template v-if="column.key === 'category'">
            <a-tag>{{ getCategoryName(record.category) }}</a-tag>
          </template>

          <template v-if="column.key === 'language'">
            {{ getLangName(record.language) }}
          </template>

          <template v-if="column.key === 'use_count'">
            {{ record.use_count }} 次
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="handleView(record)">
                <EyeOutlined />
                查看
              </a-button>
              <a-button size="small" @click="handleEdit(record)">
                <EditOutlined />
                编辑
              </a-button>
              <a-popconfirm
                v-if="!record.is_default"
                title="确定删除此提示词？"
                @confirm="handleDelete(record)"
              >
                <a-button size="small" danger>
                  <DeleteOutlined />
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 编辑模态框 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑提示词' : '新建提示词'"
      width="700px"
      @ok="handleSubmit"
      :confirm-loading="submitting"
    >
      <a-form :model="formData" layout="vertical">
        <a-form-item label="名称" required>
          <a-input v-model:value="formData.name" placeholder="请输入提示词名称" />
        </a-form-item>

        <a-form-item label="描述">
          <a-textarea v-model:value="formData.description" :rows="2" placeholder="请输入描述" />
        </a-form-item>

        <a-form-item label="分类" required>
          <a-select v-model:value="formData.category">
            <a-select-option value="general">通用</a-select-option>
            <a-select-option value="technical">技术</a-select-option>
            <a-select-option value="academic">学术</a-select-option>
            <a-select-option value="literary">文学</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="适用语言" required>
          <a-select v-model:value="formData.language">
            <a-select-option value="en">英语</a-select-option>
            <a-select-option value="zh">中文</a-select-option>
            <a-select-option value="ja">日语</a-select-option>
            <a-select-option value="ko">韩语</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="提示词内容" required>
          <a-textarea
            v-model:value="formData.content"
            :rows="8"
            placeholder="请输入提示词内容，可以使用 {target_lang} 等变量"
          />
          <div class="form-tip">
            <p>可用变量：</p>
            <p>{target_lang} - 目标语言</p>
            <p>{source_lang} - 源语言</p>
          </div>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 查看模态框 -->
    <a-modal
      v-model:open="viewVisible"
      title="提示词详情"
      width="700px"
      :footer="null"
    >
      <div v-if="currentPrompt" class="prompt-detail">
        <a-descriptions bordered :column="1">
          <a-descriptions-item label="名称">
            {{ currentPrompt.name }}
          </a-descriptions-item>
          <a-descriptions-item label="描述">
            {{ currentPrompt.description || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="分类">
            <a-tag>{{ getCategoryName(currentPrompt.category) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="适用语言">
            {{ getLangName(currentPrompt.language) }}
          </a-descriptions-item>
          <a-descriptions-item label="使用次数">
            {{ currentPrompt.use_count }} 次
          </a-descriptions-item>
          <a-descriptions-item label="提示词内容">
            <div class="prompt-content">{{ currentPrompt.content }}</div>
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ formatDateTime(currentPrompt.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="更新时间">
            {{ formatDateTime(currentPrompt.updated_at) }}
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  PlusOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  BulbOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { http } from '@/api'

// 数据
const prompts = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const categoryFilter = ref('')

// 模态框
const modalVisible = ref(false)
const viewVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)

// 表单数据
const formData = ref({
  name: '',
  description: '',
  category: 'general',
  language: 'en',
  content: ''
})

// 当前查看的提示词
const currentPrompt = ref<any>(null)

// 表格列
const columns = [
  { title: '名称', key: 'name', ellipsis: true },
  { title: '分类', key: 'category', width: 120 },
  { title: '语言', key: 'language', width: 100 },
  { title: '使用次数', key: 'use_count', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 200 }
]

// 获取提示词列表
const fetchPrompts = async () => {
  loading.value = true
  try {
    const res = await http.get('/prompt/list', {
      params: {
        page: page.value,
        page_size: pageSize.value,
        category: categoryFilter.value || undefined
      }
    })
    
    // 调试：打印完整响应
    console.log('后端响应:', res.data)
    
    // 兼容两种后端返回格式：
    // 格式1: { success: true, data: { items: [...], total: 4 } }
    // 格式2: { items: [...], total: 4, page: 1, ... }
    if (res.data?.success && res.data?.data) {
      // 格式1：有包装层
      prompts.value = res.data.data.items || []
      total.value = res.data.data.total || 0
    } else if (Array.isArray(res.data?.items)) {
      // 格式2：直接返回分页数据
      prompts.value = res.data.items
      total.value = res.data.total || 0
    } else {
      // 数据格式错误
      prompts.value = []
      total.value = 0
      message.warning('暂无提示词数据')
    }
  } catch (error: any) {
    console.error('获取提示词列表失败:', error)
    console.error('错误响应:', error.response?.data)
    message.error(error.response?.data?.message || '获取提示词列表失败')
    prompts.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 表格变化
const handleTableChange = (pagination: any) => {
  page.value = pagination.current
  pageSize.value = pagination.pageSize
  fetchPrompts()
}

// 筛选变化
const handleFilterChange = () => {
  page.value = 1
  fetchPrompts()
}

// 刷新
const handleRefresh = () => {
  fetchPrompts()
  message.success('刷新成功')
}

// 新建
const handleCreate = () => {
  isEdit.value = false
  formData.value = {
    name: '',
    description: '',
    category: 'general',
    language: 'en',
    content: ''
  }
  modalVisible.value = true
}

// 编辑
const handleEdit = (record: any) => {
  isEdit.value = true
  formData.value = {
    name: record.name,
    description: record.description || '',
    category: record.category,
    language: record.language,
    content: record.content
  }
  currentPrompt.value = record
  modalVisible.value = true
}

// 提交
const handleSubmit = async () => {
  if (!formData.value.name || !formData.value.content) {
    message.error('请填写名称和内容')
    return
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await http.put(`/prompt/${currentPrompt.value.id}`, formData.value)
      message.success('更新成功')
    } else {
      await http.post('/prompt/create', formData.value)
      message.success('创建成功')
    }

    modalVisible.value = false
    fetchPrompts()
  } catch (error: any) {
    console.error(isEdit.value ? '更新失败:' : '创建失败:', error)
    message.error(error.response?.data?.message || (isEdit.value ? '更新失败' : '创建失败'))
  } finally {
    submitting.value = false
  }
}

// 查看
const handleView = (record: any) => {
  currentPrompt.value = record
  viewVisible.value = true
}

// 删除
const handleDelete = async (record: any) => {
  try {
    await http.delete(`/prompt/${record.id}`)
    message.success('删除成功')
    fetchPrompts()
  } catch (error: any) {
    console.error('删除失败:', error)
    message.error(error.response?.data?.message || '删除失败')
  }
}

// 获取分类名称
const getCategoryName = (category: string) => {
  const names: Record<string, string> = {
    general: '通用',
    technical: '技术',
    academic: '学术',
    literary: '文学'
  }
  return names[category] || category
}

// 获取语言名称
const getLangName = (code: string) => {
  const names: Record<string, string> = {
    en: '英语',
    zh: '中文',
    ja: '日语',
    ko: '韩语'
  }
  return names[code] || code
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  fetchPrompts()
})
</script>

<style scoped>
.prompt-page {
  max-width: 1400px;
  margin: 0 auto;
}

.prompt-card {
  min-height: calc(100vh - 200px);
}

.toolbar {
  margin-bottom: 16px;
}

.prompt-name {
  display: flex;
  align-items: center;
}

.form-tip {
  margin-top: 8px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.form-tip p {
  margin: 4px 0;
}

.prompt-detail {
  padding: 16px 0;
}

.prompt-content {
  white-space: pre-wrap;
  word-break: break-word;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
}
</style>
