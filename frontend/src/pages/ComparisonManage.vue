<template>
  <div class="comparison-page">
    <a-card title="术语对照表管理" class="comparison-card">
      <!-- 工具栏 -->
      <div class="toolbar">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-input-search
              v-model:value="searchKeyword"
              placeholder="搜索术语..."
              @search="handleSearch"
              enter-button
            />
          </a-col>
          <a-col :span="10">
            <a-space>
              <a-select
                v-model:value="sourceLang"
                style="width: 120px"
                placeholder="源语言"
                @change="handleFilterChange"
              >
                <a-select-option value="">全部</a-select-option>
                <a-select-option value="zh">中文</a-select-option>
                <a-select-option value="en">英语</a-select-option>
                <a-select-option value="ja">日语</a-select-option>
              </a-select>

              <a-select
                v-model:value="targetLang"
                style="width: 120px"
                placeholder="目标语言"
                @change="handleFilterChange"
              >
                <a-select-option value="">全部</a-select-option>
                <a-select-option value="zh">中文</a-select-option>
                <a-select-option value="en">英语</a-select-option>
                <a-select-option value="ja">日语</a-select-option>
              </a-select>

              <a-button type="primary" @click="handleCreate">
                <PlusOutlined />
                新建术语
              </a-button>

              <a-button @click="handleRefresh">
                <ReloadOutlined />
                刷新
              </a-button>
            </a-space>
          </a-col>
        </a-row>
      </div>

      <!-- 术语列表 -->
      <a-table
        :columns="columns"
        :data-source="comparisons"
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
          <template v-if="column.key === 'term'">
            <div class="term-display">
              <div class="source-term">{{ record.source_term }}</div>
              <div class="arrow">↓</div>
              <div class="target-term">{{ record.target_term }}</div>
            </div>
          </template>

          <template v-if="column.key === 'languages'">
            <span>
              {{ getLangName(record.source_lang) }} → {{ getLangName(record.target_lang) }}
            </span>
          </template>

          <template v-if="column.key === 'category'">
            <a-tag v-if="record.category">{{ record.category }}</a-tag>
            <span v-else>-</span>
          </template>

          <template v-if="column.key === 'priority'">
            <a-rate v-model="record.priority" disabled :count="5" style="font-size: 14px;" />
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="handleEdit(record)">
                <EditOutlined />
                编辑
              </a-button>
              <a-popconfirm
                title="确定删除此术语？"
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
      :title="isEdit ? '编辑术语' : '新建术语'"
      width="600px"
      @ok="handleSubmit"
      :confirm-loading="submitting"
    >
      <a-form :model="formData" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="源语言" required>
              <a-select v-model:value="formData.source_lang">
                <a-select-option value="zh">中文</a-select-option>
                <a-select-option value="en">英语</a-select-option>
                <a-select-option value="ja">日语</a-select-option>
                <a-select-option value="ko">韩语</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="目标语言" required>
              <a-select v-model:value="formData.target_lang">
                <a-select-option value="zh">中文</a-select-option>
                <a-select-option value="en">英语</a-select-option>
                <a-select-option value="ja">日语</a-select-option>
                <a-select-option value="ko">韩语</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="源术语" required>
          <a-input v-model:value="formData.source_term" placeholder="请输入源术语" />
        </a-form-item>

        <a-form-item label="目标术语" required>
          <a-input v-model:value="formData.target_term" placeholder="请输入目标术语" />
        </a-form-item>

        <a-form-item label="分类">
          <a-input v-model:value="formData.category" placeholder="如：计算机、医学等" />
        </a-form-item>

        <a-form-item label="描述">
          <a-textarea v-model:value="formData.description" :rows="2" placeholder="术语解释" />
        </a-form-item>

        <a-form-item label="使用场景">
          <a-textarea v-model:value="formData.context" :rows="2" placeholder="使用场景说明" />
        </a-form-item>

        <a-form-item label="优先级">
          <a-rate v-model:value="formData.priority" :count="5" />
          <div class="form-tip">数字越大优先级越高</div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  PlusOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import axios from 'axios'

// 数据
const comparisons = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 筛选条件
const searchKeyword = ref('')
const sourceLang = ref('')
const targetLang = ref('')

// 模态框
const modalVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)

// 表单数据
const formData = ref({
  source_term: '',
  target_term: '',
  source_lang: 'zh',
  target_lang: 'en',
  category: '',
  description: '',
  context: '',
  priority: 0
})

// 表格列
const columns = [
  { title: '术语对照', key: 'term', width: 250 },
  { title: '语言', key: 'languages', width: 150 },
  { title: '分类', key: 'category', width: 120 },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '优先级', key: 'priority', width: 120 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 150 }
]

// 获取术语列表
const fetchComparisons = async (isSearch = false) => {
  loading.value = true
  try {
    // 如果是搜索，使用搜索接口
    if (isSearch && searchKeyword.value) {
      const res = await axios.get('/api/comparison/search', {
        params: {
          keyword: searchKeyword.value,
          source_lang: sourceLang.value || undefined,
          target_lang: targetLang.value || undefined
        }
      })
      comparisons.value = res.data.data.items
      total.value = res.data.data.total
    } else {
      // 普通列表查询
      const res = await axios.get('/api/comparison/list', {
        params: {
          page: page.value,
          page_size: pageSize.value,
          source_lang: sourceLang.value || undefined,
          target_lang: targetLang.value || undefined
        }
      })
      comparisons.value = res.data.data.items
      total.value = res.data.data.total
    }
  } catch (error) {
    message.error('获取术语列表失败')
  } finally {
    loading.value = false
  }
}

// 表格变化
const handleTableChange = (pagination: any) => {
  page.value = pagination.current
  pageSize.value = pagination.pageSize
  fetchComparisons()
}

// 筛选变化
const handleFilterChange = () => {
  page.value = 1
  fetchComparisons()
}

// 搜索
const handleSearch = () => {
  page.value = 1
  fetchComparisons(true)
}

// 刷新
const handleRefresh = () => {
  searchKeyword.value = ''
  fetchComparisons()
  message.success('刷新成功')
}

// 新建
const handleCreate = () => {
  isEdit.value = false
  formData.value = {
    source_term: '',
    target_term: '',
    source_lang: 'zh',
    target_lang: 'en',
    category: '',
    description: '',
    context: '',
    priority: 0
  }
  modalVisible.value = true
}

// 编辑
const handleEdit = (record: any) => {
  isEdit.value = true
  formData.value = {
    source_term: record.source_term,
    target_term: record.target_term,
    source_lang: record.source_lang,
    target_lang: record.target_lang,
    category: record.category || '',
    description: record.description || '',
    context: record.context || '',
    priority: record.priority
  }
  modalVisible.value = true
}

// 提交
const handleSubmit = async () => {
  if (!formData.value.source_term || !formData.value.target_term) {
    message.error('请填写源术语和目标术语')
    return
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await axios.put(`/api/comparison/${currentId.value}`, formData.value)
      message.success('更新成功')
    } else {
      await axios.post('/api/comparison/create', formData.value)
      message.success('创建成功')
    }

    modalVisible.value = false
    fetchComparisons()
  } catch (error) {
    message.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

// 删除
const handleDelete = async (record: any) => {
  try {
    await axios.delete(`/api/comparison/${record.id}`)
    message.success('删除成功')
    fetchComparisons()
  } catch (error) {
    message.error('删除失败')
  }
}

// 获取语言名称
const getLangName = (code: string) => {
  const names: Record<string, string> = {
    zh: '中文',
    en: '英语',
    ja: '日语',
    ko: '韩语'
  }
  return names[code] || code
}

// 当前编辑的术语ID
const currentId = ref<number | null>(null)

// 编辑时保存ID
const handleEditReal = (record: any) => {
  currentId.value = record.id
  handleEdit(record)
}

onMounted(() => {
  fetchComparisons()
})
</script>

<style scoped>
.comparison-page {
  max-width: 1400px;
  margin: 0 auto;
}

.comparison-card {
  min-height: calc(100vh - 200px);
}

.toolbar {
  margin-bottom: 16px;
}

.term-display {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.source-term {
  font-weight: 500;
  color: #1890ff;
}

.arrow {
  text-align: center;
  color: #8c8c8c;
  font-size: 12px;
}

.target-term {
  font-weight: 500;
  color: #52c41a;
}

.form-tip {
  font-size: 12px;
  color: #8c8c8c;
}
</style>
