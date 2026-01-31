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
        :scroll="{ x: 1100 }"
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

          <template v-if="column.key === 'model_name'">
            <a-tag size="small" color="blue">{{ getModelShortName(record.model_name) }}</a-tag>
          </template>

          <template v-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>

          <template v-if="column.key === 'action'">
            <a-space :size="4">
              <!-- 主要操作：下载 -->
              <a-button
                v-if="record.status === 'completed'"
                type="primary"
                size="small"
                @click="handleDownload(record)"
                title="下载"
              >
                <DownloadOutlined />
              </a-button>

              <!-- 刷新 -->
              <a-button
                v-if="record.status === 'processing'"
                size="small"
                @click="handleRefreshOne(record)"
                title="刷新进度"
              >
                <SyncOutlined :spin="refreshingId === record.id" />
              </a-button>

              <!-- 更多操作下拉菜单 -->
              <a-dropdown :trigger="['click']">
                <a-button size="small">
                  <MoreOutlined />
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="handlePreview(record)">
                      <FileSearchOutlined />
                      预览文件
                    </a-menu-item>
                    <a-menu-item 
                      v-if="record.status === 'completed' || record.status === 'failed'"
                      @click="handleRetry(record)"
                    >
                      <RedoOutlined />
                      重新翻译
                    </a-menu-item>
                    <a-menu-item @click="handleViewDetail(record)">
                      <EyeOutlined />
                      查看详情
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item danger @click="handleDelete(record)">
                      <DeleteOutlined />
                      删除任务
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 预览对话框 -->
    <PreviewDialog
      v-model:visible="previewVisible"
      :task-id="previewTaskId"
      :file-name="previewFileName"
      :status="previewStatus"
    />

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

    <!-- 重试配置对话框 -->
    <a-modal
      v-model:open="retryVisible"
      title="重新翻译配置"
      width="600px"
      :confirm-loading="retryLoading"
      @ok="handleRetryConfirm"
      @cancel="handleRetryCancel"
      okText="开始翻译"
      cancelText="取消"
    >
      <div v-if="currentRetryTask" class="retry-dialog">
        <a-alert
          type="info"
          :message="`基于文件: ${currentRetryTask.file_name}`"
          show-icon
          style="margin-bottom: 16px"
        />

        <a-form layout="vertical">
          <!-- 源语言 -->
          <a-form-item label="源语言">
            <a-select v-model:value="retryConfig.source_lang" style="width: 100%">
              <a-select-option
                v-for="lang in langOptions"
                :key="lang.value"
                :value="lang.value"
              >
                {{ lang.label }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <!-- 目标语言 -->
          <a-form-item label="目标语言">
            <a-select v-model:value="retryConfig.target_lang" style="width: 100%">
              <a-select-option
                v-for="lang in langOptions.filter(l => l.value !== 'auto')"
                :key="lang.value"
                :value="lang.value"
              >
                {{ lang.label }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <!-- 翻译领域 -->
          <a-form-item label="翻译领域">
            <a-select v-model:value="retryConfig.domain" style="width: 100%">
              <a-select-option
                v-for="domain in domainOptions"
                :key="domain.value"
                :value="domain.value"
              >
                <div style="display: flex; justify-content: space-between; align-items: center">
                  <span>{{ domain.label }}</span>
                  <span style="color: #999; font-size: 12px">{{ domain.desc }}</span>
                </div>
              </a-select-option>
            </a-select>
          </a-form-item>

          <!-- AI 模型 -->
          <a-form-item label="AI 模型">
            <a-select v-model:value="retryConfig.model_name" style="width: 100%">
              <a-select-option
                v-for="model in modelOptions"
                :key="model.value"
                :value="model.value"
              >
                <div style="display: flex; justify-content: space-between; align-items: center">
                  <span>{{ model.label }}</span>
                  <span style="color: #999; font-size: 12px">{{ model.desc }}</span>
                </div>
              </a-select-option>
            </a-select>
          </a-form-item>

          <!-- 线程数 -->
          <a-form-item label="翻译线程数">
            <a-slider
              v-model:value="retryConfig.thread_count"
              :min="1"
              :max="10"
              :marks="{ 1: '1', 5: '5', 10: '10' }"
            />
          </a-form-item>
        </a-form>
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
  FileTextOutlined,
  RedoOutlined,
  FileSearchOutlined,
  MoreOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { getTranslateList, downloadTranslateResult, deleteTranslate, retryTranslate, type TranslateTask, type TranslateRequest } from '@/api/translate'
import PreviewDialog from '@/components/PreviewDialog.vue'

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

// 预览对话框
const previewVisible = ref(false)
const previewTaskId = ref<number | null>(null)
const previewFileName = ref('')
const previewStatus = ref('')

// 重试对话框
const retryVisible = ref(false)
const retryLoading = ref(false)
const currentRetryTask = ref<TranslateTask | null>(null)
const retryConfig = ref<TranslateRequest>({
  file_id: 0,
  source_lang: 'auto',
  target_lang: 'zh',
  model_name: 'deepseek-chat',
  thread_count: 5,
  display_mode: 1,
  domain: 'general'
})

// 语言选项
const langOptions = [
  { value: 'auto', label: '自动检测' },
  { value: 'zh', label: '🇨🇳 中文' },
  { value: 'en', label: '🇺🇸 英语' },
  { value: 'ja', label: '🇯🇵 日语' },
  { value: 'ko', label: '🇰🇷 韩语' },
  { value: 'fr', label: '🇫🇷 法语' },
  { value: 'de', label: '🇩🇪 德语' }
]

// 领域选项
const domainOptions = [
  { value: 'general', label: '通用领域', desc: '适用于大多数文档' },
  { value: 'medical', label: '医疗医学', desc: '病历、医学论文' },
  { value: 'it', label: '计算机IT', desc: '技术文档、代码注释' },
  { value: 'legal', label: '法律法务', desc: '合同、法规文件' },
  { value: 'finance', label: '金融财经', desc: '财务报告、投资文档' },
  { value: 'engineering', label: '工程技术', desc: '工程图纸、规范手册' },
  { value: 'academic', label: '学术科研', desc: '论文、研究报告' },
  { value: 'business', label: '商务商业', desc: '商业计划、市场分析' }
]

// 模型选项
const modelOptions = [
  { value: 'deepseek-chat', label: 'DeepSeek Chat', desc: '速度快，性价比高' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', desc: 'OpenAI 标准模型' },
  { value: 'gpt-4', label: 'GPT-4', desc: '高质量，适合复杂文档' }
]

// 表格列配置
// 注意：文件名列不设置width，让它自适应剩余空间
const columns = [
  { title: '文件名', key: 'file_name', ellipsis: true },
  { title: '语言', key: 'languages', width: 140 },
  { title: '模型', dataIndex: 'model_name', key: 'model_name', width: 110 },
  { title: '状态', key: 'status', width: 90 },
  { title: '进度', key: 'progress', width: 120 },
  { title: '创建时间', key: 'created_at', width: 160 },
  { title: '操作', key: 'action', width: 100, fixed: 'right' }
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

// 打开预览对话框
const handlePreview = (record: TranslateTask) => {
  previewTaskId.value = record.id
  previewFileName.value = record.file_name
  previewStatus.value = record.status
  previewVisible.value = true
}

// 打开重试对话框
const handleRetry = (record: TranslateTask) => {
  currentRetryTask.value = record
  // 预填充原任务的配置
  retryConfig.value = {
    file_id: record.id,
    source_lang: record.source_lang || 'auto',
    target_lang: record.target_lang || 'zh',
    model_name: record.model_name || 'deepseek-chat',
    thread_count: 5,
    display_mode: 1,
    domain: record.domain || 'general'
  }
  retryVisible.value = true
}

// 取消重试
const handleRetryCancel = () => {
  retryVisible.value = false
  currentRetryTask.value = null
}

// 确认重试
const handleRetryConfirm = async () => {
  if (!currentRetryTask.value) return

  retryLoading.value = true
  try {
    const res = await retryTranslate(currentRetryTask.value.id, retryConfig.value)
    message.success('重试任务创建成功')
    retryVisible.value = false
    // 刷新列表
    fetchTasks()
  } catch (error) {
    message.error('创建重试任务失败')
  } finally {
    retryLoading.value = false
  }
}

// 获取领域名称
const getDomainName = (domain: string) => {
  const names: Record<string, string> = {
    general: '通用领域',
    medical: '医疗医学',
    it: '计算机IT',
    legal: '法律法务',
    finance: '金融财经',
    engineering: '工程技术',
    academic: '学术科研',
    business: '商务商业'
  }
  return names[domain] || domain
}

// 获取模型简称
const getModelShortName = (model: string) => {
  const shortNames: Record<string, string> = {
    'deepseek-chat': 'DeepSeek',
    'gpt-3.5-turbo': 'GPT-3.5',
    'gpt-4': 'GPT-4',
    'gpt-4-turbo': 'GPT-4T'
  }
  return shortNames[model] || model
}
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
  white-space: nowrap;
  overflow: hidden;
}

.file-info span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: calc(100% - 60px);
}

.task-detail {
  padding: 16px 0;
}

.retry-dialog {
  padding: 8px 0;
}

/* 表格文件名列自适应 */
:deep(.ant-table-cell) {
  white-space: nowrap;
}

:deep(.ant-table-cell:first-child) {
  width: auto;
  min-width: 200px;
  max-width: none;
}
</style>
