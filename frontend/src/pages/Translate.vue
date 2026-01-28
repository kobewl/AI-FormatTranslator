<template>
  <div class="translate-page">
    <a-row :gutter="[24, 24]">
      <!-- 左侧：上传和配置 -->
      <a-col :xs="24" :lg="12">
        <a-card title="上传文档" class="upload-card">
          <a-upload-dragger
            :file-list="fileList"
            :before-upload="beforeUpload"
            @remove="handleRemove"
            accept=".docx,.pdf,.xlsx,.pptx,.md,.txt"
            :max-count="1"
          >
            <p class="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">
              支持 Word、PDF、Excel、PPT、Markdown、TXT 格式，最大 100MB
            </p>
          </a-upload-dragger>

          <!-- 翻译配置 -->
          <a-divider>翻译配置</a-divider>

          <a-form :model="config" layout="vertical">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="源语言">
                  <a-select v-model:value="config.source_lang" placeholder="选择源语言">
                    <a-select-option value="auto">自动检测</a-select-option>
                    <a-select-option value="en">英语</a-select-option>
                    <a-select-option value="zh">中文</a-select-option>
                    <a-select-option value="ja">日语</a-select-option>
                    <a-select-option value="ko">韩语</a-select-option>
                    <a-select-option value="fr">法语</a-select-option>
                    <a-select-option value="de">德语</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>

              <a-col :span="12">
                <a-form-item label="目标语言">
                  <a-select v-model:value="config.target_lang" placeholder="选择目标语言">
                    <a-select-option value="zh">中文</a-select-option>
                    <a-select-option value="en">英语</a-select-option>
                    <a-select-option value="ja">日语</a-select-option>
                    <a-select-option value="ko">韩语</a-select-option>
                    <a-select-option value="fr">法语</a-select-option>
                    <a-select-option value="de">德语</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="AI 模型">
              <a-select v-model:value="config.model_name">
                <a-select-option value="deepseek-chat">DeepSeek Chat</a-select-option>
              </a-select>
            </a-form-item>

            <a-form-item label="线程数">
              <a-slider v-model:value="config.thread_count" :min="1" :max="10" />
              <div class="thread-info">{{ config.thread_count }} 个线程</div>
            </a-form-item>

            <a-button
              type="primary"
              size="large"
              block
              :loading="starting"
              :disabled="!uploadedFileId"
              @click="handleStartTranslate"
            >
              <PlayCircleOutlined />
              开始翻译
            </a-button>
          </a-form>
        </a-card>
      </a-col>

      <!-- 右侧：当前任务进度 -->
      <a-col :xs="24" :lg="12">
        <a-card title="当前任务" class="task-card">
          <div v-if="currentTask" class="task-progress">
            <a-descriptions :column="2" bordered>
              <a-descriptions-item label="文件名" :span="2">
                {{ currentTask.file_name }}
              </a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag :color="getStatusColor(currentTask.status)">
                  {{ getStatusText(currentTask.status) }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="进度">
                {{ currentTask.progress }}%
              </a-descriptions-item>
              <a-descriptions-item label="目标语言">
                {{ getLangName(currentTask.target_lang) }}
              </a-descriptions-item>
              <a-descriptions-item label="AI 模型">
                {{ currentTask.model_name }}
              </a-descriptions-item>
            </a-descriptions>

            <a-divider />

            <!-- 进度条 -->
            <a-progress
              :percent="currentTask.progress"
              :status="currentTask.status === 'completed' ? 'success' : currentTask.status === 'failed' ? 'exception' : 'active'"
              :stroke-color="{
                '0%': '#108ee9',
                '100%': '#87d068'
              }"
            />

            <div class="task-actions" v-if="currentTask.status === 'completed'">
              <a-space>
                <a-button type="primary" @click="handleDownload">
                  <DownloadOutlined />
                  下载结果
                </a-button>
                <a-button @click="handleReset">
                  <ReloadOutlined />
                  翻译新文件
                </a-button>
              </a-space>
            </div>

            <div v-if="currentTask.status === 'failed'" class="error-message">
              <a-alert
                message="翻译失败"
                :description="currentTask.error_message"
                type="error"
                show-icon
              />
            </div>
          </div>

          <a-empty v-else description="暂无翻译任务" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 底部：最近任务列表 -->
    <a-card title="最近任务" class="recent-tasks">
      <a-table
        :columns="columns"
        :data-source="recentTasks"
        :loading="loading"
        :pagination="{ pageSize: 5 }"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
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

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button
                v-if="record.status === 'completed'"
                type="link"
                size="small"
                @click="handleDownloadById(record.id)"
              >
                下载
              </a-button>
              <a-button
                type="link"
                size="small"
                @click="handleViewDetail(record)"
              >
                详情
              </a-button>
              <a-popconfirm
                title="确定删除此任务？"
                @confirm="handleDelete(record.id)"
              >
                <a-button type="link" size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import {
  InboxOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import type { UploadProps } from 'ant-design-vue'
import { uploadFile, startTranslate, downloadTranslateResult, deleteTranslate, type TranslateTask } from '@/api/translate'
import { useTranslateStore } from '@/store'

const translateStore = useTranslateStore()

// 文件上传
const fileList = ref<any[]>([])
const uploadedFileId = ref<number | null>(null)

// 翻译配置
const config = ref({
  source_lang: 'auto',
  target_lang: 'en',
  model_name: 'deepseek-chat',
  thread_count: 5
})

const starting = ref(false)
const loading = ref(false)

// 当前任务
const currentTask = ref<TranslateTask | null>(null)

// 最近任务
const recentTasks = ref<TranslateTask[]>([])

// 进度定时器
let progressTimer: NodeJS.Timeout | null = null

// 表格列
const columns = [
  { title: '文件名', dataIndex: 'file_name', key: 'file_name', ellipsis: true },
  { title: '目标语言', dataIndex: 'target_lang', key: 'target_lang', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '进度', key: 'progress', width: 150 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 150 }
]

// 文件上传前
const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  const isValidType = ['docx', 'pdf', 'xlsx', 'pptx', 'md', 'txt'].includes(
    file.name.split('.').pop()?.toLowerCase() || ''
  )
  if (!isValidType) {
    message.error('不支持的文件格式')
    return false
  }

  const isLt100M = file.size / 1024 / 1024 < 100
  if (!isLt100M) {
    message.error('文件大小不能超过 100MB')
    return false
  }

  // 上传文件
  handleUpload(file)
  return false
}

// 上传文件
const handleUpload = async (file: File) => {
  try {
    const res = await uploadFile(file)
    uploadedFileId.value = res.data.id
    fileList.value = [{
      uid: '1',
      name: file.name,
      status: 'done',
      response: res.data
    }]
    message.success('文件上传成功')
  } catch (error) {
    fileList.value = []
    message.error('文件上传失败')
  }
}

// 移除文件
const handleRemove = () => {
  uploadedFileId.value = null
  currentTask.value = null
}

// 开始翻译
const handleStartTranslate = async () => {
  if (!uploadedFileId.value) {
    message.warning('请先上传文件')
    return
  }

  starting.value = true
  try {
    const res = await startTranslate({
      file_id: uploadedFileId.value,
      ...config.value
    })

    currentTask.value = res.data
    message.success('翻译任务已启动')

    // 开始轮询进度
    startProgressPolling()
  } catch (error) {
    message.error('启动翻译失败')
  } finally {
    starting.value = false
  }
}

// 开始轮询进度
const startProgressPolling = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
  }

  progressTimer = setInterval(async () => {
    if (!currentTask.value) return

    const progress = await translateStore.fetchProgress(currentTask.value.id)
    if (progress) {
      currentTask.value = {
        ...currentTask.value,
        ...progress
      }

      // 如果完成或失败，停止轮询
      if (progress.status === 'completed' || progress.status === 'failed') {
        stopProgressPolling()
        // 刷新最近任务列表
        fetchRecentTasks()
      }
    }
  }, 2000)
}

// 停止轮询
const stopProgressPolling = () => {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

// 下载结果
const handleDownload = () => {
  if (currentTask.value) {
    handleDownloadById(currentTask.value.id)
  }
}

const handleDownloadById = async (id: number) => {
  try {
    await downloadTranslateResult(id)
  } catch (error) {
    console.error('下载失败:', error)
  }
}

// 重置
const handleReset = () => {
  uploadedFileId.value = null
  fileList.value = []
  currentTask.value = null
}

// 查看详情
const handleViewDetail = (task: TranslateTask) => {
  currentTask.value = task
  if (task.status === 'processing') {
    startProgressPolling()
  }
}

// 删除任务
const handleDelete = async (id: number) => {
  try {
    await deleteTranslate(id)
    message.success('删除成功')
    fetchRecentTasks()
    if (currentTask.value?.id === id) {
      currentTask.value = null
    }
  } catch (error) {
    message.error('删除失败')
  }
}

// 获取最近任务
const fetchRecentTasks = async () => {
  loading.value = true
  try {
    await translateStore.fetchTasks({ page: 1, page_size: 5 })
    recentTasks.value = translateStore.tasks
  } finally {
    loading.value = false
  }
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

// 获取语言名称
const getLangName = (code: string) => {
  const names: Record<string, string> = {
    zh: '中文',
    en: '英语',
    ja: '日语',
    ko: '韩语',
    fr: '法语',
    de: '德语'
  }
  return names[code] || code
}

onMounted(() => {
  fetchRecentTasks()
})

onUnmounted(() => {
  stopProgressPolling()
})
</script>

<style scoped>
.translate-page {
  max-width: 1400px;
  margin: 0 auto;
}

.upload-card,
.task-card,
.recent-tasks {
  margin-bottom: 24px;
}

.thread-info {
  text-align: right;
  color: #8c8c8c;
  font-size: 12px;
}

.task-progress {
  padding: 16px 0;
}

.task-actions {
  margin-top: 24px;
  text-align: center;
}

.error-message {
  margin-top: 16px;
}
</style>
