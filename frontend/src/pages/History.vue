<template>
  <div class="history-page">
    <a-card title="翻译历史" class="history-card">
      <!-- 筛选工具栏 -->
      <div class="toolbar">
        <a-space>
          <a-select
            v-model:value="statusFilter"
            style="width: 150px"
            placeholder="筛选状态"
            allowClear
            @change="handleFilterChange"
          >
            <a-select-option value="">全部</a-select-option>
            <a-select-option value="pending">等待中</a-select-option>
            <a-select-option value="processing">翻译中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
            <a-select-option value="failed">失败</a-select-option>
          </a-select>

          <a-button @click="handleRefresh">
            <ReloadOutlined />
            刷新
          </a-button>
        </a-space>
      </div>

      <!-- 任务列表 -->
      <a-table
        :columns="columns"
        :data-source="tasks"
        :loading="loading"
        :pagination="{
          current: page,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`
        }"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'file_name'">
            <div class="file-info">
              <FileTextOutlined style="margin-right: 8px;" />
              <span>{{ record.file_name }}</span>
              <a-tag style="margin-left: 8px;">{{ record.file_type.toUpperCase() }}</a-tag>
            </div>
          </template>

          <template v-if="column.key === 'languages'">
            <span>
              {{ getLangName(record.source_lang) }} → {{ getLangName(record.target_lang) }}
            </span>
          </template>

          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>

          <template v-if="column.key === 'progress'">
            <a-progress
              :percent="record.progress"
              size="small"
              :status="record.status === 'completed' ? 'success' : record.status === 'failed' ? 'exception' : undefined"
            />
          </template>

          <template v-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button
                v-if="record.status === 'completed'"
                type="primary"
                size="small"
                @click="handleDownload(record)"
              >
                <DownloadOutlined />
                下载
              </a-button>

              <a-button
                v-if="record.status === 'processing'"
                size="small"
                @click="handleRefreshOne(record)"
              >
                <SyncOutlined :spin="refreshingId === record.id" />
                刷新
              </a-button>

              <a-button
                size="small"
                @click="handleViewDetail(record)"
              >
                <EyeOutlined />
                详情
              </a-button>

              <a-popconfirm
                title="确定删除此任务？"
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

    <!-- 详情模态框 -->
    <a-modal
      v-model:open="detailVisible"
      title="翻译任务详情"
      width="800px"
      :footer="null"
    >
      <div v-if="currentDetail" class="task-detail">
        <a-descriptions bordered :column="2">
          <a-descriptions-item label="文件名" :span="2">
            {{ currentDetail.file_name }}
          </a-descriptions-item>
          <a-descriptions-item label="文件大小">
            {{ formatSize(currentDetail.file_size) }}
          </a-descriptions-item>
          <a-descriptions-item label="文件类型">
            {{ currentDetail.file_type.toUpperCase() }}
          </a-descriptions-item>
          <a-descriptions-item label="源语言">
            {{ getLangName(currentDetail.source_lang) }}
          </a-descriptions-item>
          <a-descriptions-item label="目标语言">
            {{ getLangName(currentDetail.target_lang) }}
          </a-descriptions-item>
          <a-descriptions-item label="AI 模型">
            {{ currentDetail.model_name }}
          </a-descriptions-item>
          <a-descriptions-item label="线程数">
            {{ currentDetail.thread_count }}
          </a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="getStatusColor(currentDetail.status)">
              {{ getStatusText(currentDetail.status) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="进度">
            {{ currentDetail.progress }}%
          </a-descriptions-item>
          <a-descriptions-item label="总段数">
            {{ currentDetail.total_segments || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="已翻译">
            {{ currentDetail.translated_segments || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="创建时间" :span="2">
            {{ formatDateTime(currentDetail.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item v-if="currentDetail.started_at" label="开始时间" :span="2">
            {{ formatDateTime(currentDetail.started_at) }}
          </a-descriptions-item>
          <a-descriptions-item v-if="currentDetail.completed_at" label="完成时间" :span="2">
            {{ formatDateTime(currentDetail.completed_at) }}
          </a-descriptions-item>
          <a-descriptions-item v-if="currentDetail.error_message" label="错误信息" :span="2">
            <a-alert :message="currentDetail.error_message" type="error" />
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  ReloadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EyeOutlined,
  SyncOutlined,
  FileTextOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { getTranslateList, downloadTranslateResult, deleteTranslate, type TranslateTask } from '@/api/translate'

// 数据
const tasks = ref<TranslateTask[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const statusFilter = ref('')

// 详情模态框
const detailVisible = ref(false)
const currentDetail = ref<TranslateTask | null>(null)

// 刷新状态
const refreshingId = ref<number | null>(null)

// 表格列
const columns = [
  { title: '文件名', key: 'file_name', ellipsis: true },
  { title: '语言', key: 'languages', width: 150 },
  { title: '模型', dataIndex: 'model_name', key: 'model_name', width: 120 },
  { title: '状态', key: 'status', width: 100 },
  { title: '进度', key: 'progress', width: 150 },
  { title: '创建时间', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 220, fixed: 'right' }
]

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await getTranslateList({
      page: page.value,
      page_size: pageSize.value,
      status: statusFilter.value || undefined
    })

    tasks.value = res.data.items
    total.value = res.data.total
  } catch (error) {
    message.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

// 表格变化
const handleTableChange = (pagination: any) => {
  page.value = pagination.current
  pageSize.value = pagination.pageSize
  fetchTasks()
}

// 筛选变化
const handleFilterChange = () => {
  page.value = 1
  fetchTasks()
}

// 刷新
const handleRefresh = () => {
  fetchTasks()
  message.success('刷新成功')
}

// 刷新单个任务
const handleRefreshOne = async (task: TranslateTask) => {
  refreshingId.value = task.id
  try {
    const res = await getTranslateList({
      page: 1,
      page_size: 1,
      status: task.status
    })

    const updated = res.data.items.find((t: TranslateTask) => t.id === task.id)
    if (updated) {
      const index = tasks.value.findIndex(t => t.id === task.id)
      if (index !== -1) {
        tasks.value[index] = updated
      }
    }

    message.success('刷新成功')
  } finally {
    refreshingId.value = null
  }
}

// 下载
const handleDownload = async (record: TranslateTask) => {
  try {
    await downloadTranslateResult(record.id)
  } catch (error) {
    console.error('下载失败:', error)
  }
}

// 查看详情
const handleViewDetail = (record: TranslateTask) => {
  currentDetail.value = record
  detailVisible.value = true
}

// 删除
const handleDelete = async (record: TranslateTask) => {
  try {
    await deleteTranslate(record.id)
    message.success('删除成功')
    fetchTasks()
  } catch (error) {
    message.error('删除失败')
  }
}

// 格式化文件大小
const formatSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 格式化日期
const formatDate = (dateStr: string): string => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

// 格式化日期时间
const formatDateTime = (dateStr: string): string => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
}

// 获取语言名称
const getLangName = (code: string) => {
  const names: Record<string, string> = {
    auto: '自动检测',
    zh: '中文',
    en: '英语',
    ja: '日语',
    ko: '韩语',
    fr: '法语',
    de: '德语'
  }
  return names[code] || code
}

// 获取状态颜色
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'default',
    processing: 'processing',
    completed: 'success',
    failed: 'error'
  }
  return colors[status] || 'default'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    processing: '翻译中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.history-page {
  max-width: 1400px;
  margin: 0 auto;
}

.history-card {
  min-height: calc(100vh - 200px);
}

.toolbar {
  margin-bottom: 16px;
}

.file-info {
  display: flex;
  align-items: center;
}

.task-detail {
  padding: 16px 0;
}
</style>
