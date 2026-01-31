<template>
  <div class="translate-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">AI-FormatTranslator</h1>
      <p class="page-subtitle">智能 AI 文档翻译系统 - 支持多种格式，完美保留原文排版</p>
    </div>

    <!-- 步骤引导 -->
    <a-card class="steps-card" :bordered="false">
      <a-steps :current="currentStep" size="small">
        <a-step title="上传文件">
          <template #icon>
            <CloudUploadOutlined />
          </template>
        </a-step>
        <a-step title="配置参数">
          <template #icon>
            <SettingOutlined />
          </template>
        </a-step>
        <a-step title="开始翻译">
          <template #icon>
            <PlayCircleOutlined />
          </template>
        </a-step>
        <a-step title="下载结果">
          <template #icon>
            <DownloadOutlined />
          </template>
        </a-step>
      </a-steps>
    </a-card>

    <a-row :gutter="[24, 24]">
      <!-- 左侧：上传和配置 -->
      <a-col :xs="24" :lg="12">
        <!-- 文件上传区域 -->
        <a-card class="upload-card" :bordered="false">
          <template #title>
            <span class="card-title">
              <CloudUploadOutlined />
              上传文档
            </span>
          </template>

          <!-- 未上传时显示拖拽区域 -->
          <div v-if="!uploadedFileId" class="upload-area">
            <a-upload-dragger
              :file-list="fileList"
              :before-upload="beforeUpload"
              accept=".docx,.pdf,.xlsx,.pptx,.md,.txt"
              :max-count="1"
              class="upload-dragger"
            >
              <div class="upload-content">
                <div class="upload-icon-wrapper">
                  <CloudUploadOutlined class="upload-icon" />
                </div>
                <p class="upload-text">点击或拖拽文件到此区域</p>
                <p class="upload-hint">
                  <a-space>
                    <FileTextOutlined />Word
                    <FilePdfOutlined />PDF
                    <FileExcelOutlined />Excel
                    <FilePptOutlined />PPT
                    <FileMarkdownOutlined />Markdown
                    <FileTextOutlined />TXT
                  </a-space>
                </p>
                <p class="upload-limit">单个文件最大支持 100MB</p>
              </div>
            </a-upload-dragger>
          </div>

          <!-- 已上传时显示文件信息卡片 -->
          <div v-else class="file-info-card">
            <div class="file-info-header">
              <div class="file-icon">
                <FileTextOutlined v-if="fileList[0]?.name?.endsWith('.docx')" />
                <FilePdfOutlined v-else-if="fileList[0]?.name?.endsWith('.pdf')" />
                <FileExcelOutlined v-else-if="fileList[0]?.name?.endsWith('.xlsx')" />
                <FilePptOutlined v-else-if="fileList[0]?.name?.endsWith('.pptx')" />
                <FileMarkdownOutlined v-else-if="fileList[0]?.name?.endsWith('.md')" />
                <FileTextOutlined v-else />
              </div>
              <div class="file-details">
                <div class="file-name">{{ fileList[0]?.name }}</div>
                <div class="file-meta">
                  <a-tag size="small" color="success">已上传</a-tag>
                  <span class="file-size">{{ formatFileSize(fileList[0]?.size) }}</span>
                </div>
              </div>
              <a-button 
                type="text" 
                danger 
                size="small"
                @click="handleRemove"
                class="remove-btn"
              >
                <DeleteOutlined />
              </a-button>
            </div>
          </div>
        </a-card>

        <!-- 翻译配置 -->
        <a-card class="config-card" :bordered="false" v-if="uploadedFileId">
          <template #title>
            <span class="card-title">
              <SettingOutlined />
              翻译配置
            </span>
          </template>

          <a-form :model="config" layout="vertical" class="config-form">
            <!-- 语言选择 -->
            <div class="form-section">
              <div class="section-title">
                <GlobalOutlined />
                语言设置
              </div>
              <a-row :gutter="16">
                <a-col :span="12">
                  <a-form-item label="源语言">
                    <a-select 
                      v-model:value="config.source_lang" 
                      placeholder="选择源语言"
                      size="large"
                    >
                      <a-select-option value="auto">
                        <span class="lang-option">
                          <RocketOutlined />
                          自动检测
                        </span>
                      </a-select-option>
                      <a-select-option value="en">🇺🇸 英语</a-select-option>
                      <a-select-option value="zh">🇨🇳 中文</a-select-option>
                      <a-select-option value="ja">🇯🇵 日语</a-select-option>
                      <a-select-option value="ko">🇰🇷 韩语</a-select-option>
                      <a-select-option value="fr">🇫🇷 法语</a-select-option>
                      <a-select-option value="de">🇩🇪 德语</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>

                <a-col :span="12">
                  <a-form-item label="目标语言">
                    <a-select 
                      v-model:value="config.target_lang" 
                      placeholder="选择目标语言"
                      size="large"
                    >
                      <a-select-option value="zh">🇨🇳 中文</a-select-option>
                      <a-select-option value="en">🇺🇸 英语</a-select-option>
                      <a-select-option value="ja">🇯🇵 日语</a-select-option>
                      <a-select-option value="ko">🇰🇷 韩语</a-select-option>
                      <a-select-option value="fr">🇫🇷 法语</a-select-option>
                      <a-select-option value="de">🇩🇪 德语</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>
            </div>

            <!-- 显示模式选择 -->
            <div class="form-section">
              <div class="section-title">
                <EyeOutlined />
                译文显示样式
              </div>
              <a-form-item>
                <div class="display-mode-options">
                  <div 
                    class="mode-option"
                    :class="{ active: config.display_mode === 1 }"
                    @click="config.display_mode = 1"
                  >
                    <div class="mode-icon">
                      <SwapOutlined />
                    </div>
                    <div class="mode-content">
                      <div class="mode-title">替换模式</div>
                      <div class="mode-desc">仅保留译文，替换原文</div>
                    </div>
                    <CheckCircleFilled v-if="config.display_mode === 1" class="mode-check" />
                  </div>

                  <div 
                    class="mode-option"
                    :class="{ active: config.display_mode === 2 }"
                    @click="config.display_mode = 2"
                  >
                    <div class="mode-icon parallel">
                      <ColumnWidthOutlined />
                    </div>
                    <div class="mode-content">
                      <div class="mode-title">对照模式</div>
                      <div class="mode-desc">原文在上，译文在下</div>
                    </div>
                    <CheckCircleFilled v-if="config.display_mode === 2" class="mode-check" />
                  </div>
                </div>

                <!-- 对照模式预览 -->
                <div v-if="config.display_mode === 2" class="mode-preview">
                  <div class="preview-title">
                    <InfoCircleOutlined />
                    效果预览
                  </div>
                  <div class="preview-content">
                    <div class="preview-original">This is a sample text for translation.</div>
                    <div class="preview-translated">这是一个用于翻译的示例文本。</div>
                  </div>
                  <div class="preview-hint">
                    <a-tag color="blue">译文将显示为蓝色虚线下划线样式</a-tag>
                  </div>
                </div>
              </a-form-item>
            </div>

            <!-- 高级设置 -->
            <div class="form-section">
              <div class="section-title">
                <ToolOutlined />
                高级设置
                <a-tag color="orange" size="small" class="beta-tag">BETA</a-tag>
              </div>
              
              <a-form-item label="AI 模型">
                <a-select v-model:value="config.model_name" size="large">
                  <a-select-option value="deepseek-chat">
                    <span class="model-option">
                      <ThunderboltOutlined />
                      DeepSeek Chat
                      <a-tag color="blue" size="small">推荐</a-tag>
                    </span>
                  </a-select-option>
                </a-select>
              </a-form-item>

              <a-form-item label="翻译线程数">
                <div class="thread-slider-wrapper">
                  <a-slider 
                    v-model:value="config.thread_count" 
                    :min="1" 
                    :max="10"
                    :marks="{ 1: '1', 5: '5', 10: '10' }"
                  />
                  <div class="thread-info">
                    <span class="thread-count">{{ config.thread_count }}</span>
                    <span class="thread-label">个线程</span>
                    <a-tooltip title="线程数越多翻译速度越快，但可能增加 API 费用">
                      <QuestionCircleOutlined class="thread-help" />
                    </a-tooltip>
                  </div>
                </div>
              </a-form-item>
            </div>

            <!-- 开始翻译按钮 -->
            <a-form-item class="submit-section">
              <a-button
                type="primary"
                size="large"
                block
                :loading="starting"
                :disabled="!uploadedFileId"
                @click="handleStartTranslate"
                class="start-btn"
              >
                <PlayCircleOutlined />
                {{ starting ? '正在启动翻译...' : '开始翻译' }}
              </a-button>
              <div class="submit-hint">
                <SafetyOutlined />
                翻译过程安全加密，文档仅用于翻译，不会存储
              </div>
            </a-form-item>
          </a-form>
        </a-card>

        <!-- 使用提示 -->
        <a-card class="tips-card" :bordered="false" v-if="uploadedFileId">
          <template #title>
            <span class="card-title">
              <BulbOutlined />
              使用提示
            </span>
          </template>
          <div class="tips-list">
            <div class="tip-item">
              <div class="tip-icon">1</div>
              <div class="tip-content">
                <div class="tip-title">支持的格式</div>
                <div class="tip-desc">Word、PDF、Excel、PPT、Markdown、TXT</div>
              </div>
            </div>
            <div class="tip-item">
              <div class="tip-icon">2</div>
              <div class="tip-content">
                <div class="tip-title">两种显示模式</div>
                <div class="tip-desc">替换模式仅显示译文，对照模式同时显示原文和译文</div>
              </div>
            </div>
            <div class="tip-item">
              <div class="tip-icon">3</div>
              <div class="tip-content">
                <div class="tip-title">PDF 文件说明</div>
                <div class="tip-desc">PDF 翻译后会转换为 Word 格式，便于编辑和查看</div>
              </div>
            </div>
            <div class="tip-item">
              <div class="tip-icon">4</div>
              <div class="tip-content">
                <div class="tip-title">格式保持</div>
                <div class="tip-desc">翻译后的文档会保留原有的格式、样式和排版</div>
              </div>
            </div>
          </div>
        </a-card>
      </a-col>

      <!-- 右侧：当前任务进度 -->
      <a-col :xs="24" :lg="12">
        <a-card class="task-card" :bordered="false">
          <template #title>
            <span class="card-title">
              <DashboardOutlined />
              翻译进度
            </span>
          </template>

          <div v-if="currentTask" class="task-progress">
            <!-- 任务状态头部 -->
            <div class="task-header">
              <div class="task-status-icon" :class="currentTask.status">
                <LoadingOutlined v-if="currentTask.status === 'processing'" spin />
                <CheckCircleFilled v-else-if="currentTask.status === 'completed'" />
                <CloseCircleFilled v-else-if="currentTask.status === 'failed'" />
                <ClockCircleFilled v-else />
              </div>
              <div class="task-status-info">
                <div class="task-status-text">{{ getStatusText(currentTask.status) }}</div>
                <div class="task-progress-text">{{ currentTask.progress }}%</div>
              </div>
            </div>

            <!-- 进度条 -->
            <div class="progress-wrapper">
              <a-progress
                :percent="currentTask.progress"
                :status="currentTask.status === 'completed' ? 'success' : currentTask.status === 'failed' ? 'exception' : 'active'"
                :stroke-color="{
                  '0%': '#1890ff',
                  '100%': '#52c41a'
                }"
                :stroke-width="12"
                class="progress-bar"
              />
            </div>

            <!-- 任务详情 -->
            <div class="task-details">
              <div class="detail-item">
                <span class="detail-label">文件名</span>
                <span class="detail-value" :title="currentTask.file_name">{{ currentTask.file_name }}</span>
              </div>
              <div class="detail-row">
                <div class="detail-item">
                  <span class="detail-label">目标语言</span>
                  <span class="detail-value">{{ getLangName(currentTask.target_lang) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">AI 模型</span>
                  <span class="detail-value">{{ currentTask.model_name }}</span>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="task-actions" v-if="currentTask.status === 'completed'">
              <a-space direction="vertical" style="width: 100%">
                <a-button type="primary" size="large" block @click="handleDownload" class="download-btn">
                  <DownloadOutlined />
                  下载翻译结果
                </a-button>
                <a-button size="large" block @click="handleReset" class="reset-btn">
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
                class="error-alert"
              />
              <a-button size="large" block @click="handleReset" style="margin-top: 16px">
                <ReloadOutlined />
                重新翻译
              </a-button>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="empty-state">
            <div class="empty-icon">
              <InboxOutlined />
            </div>
            <div class="empty-title">暂无翻译任务</div>
            <div class="empty-desc">上传文件并配置参数后，点击"开始翻译"按钮开始</div>
          </div>
        </a-card>

      </a-col>
    </a-row>

    <!-- 底部：最近任务列表 -->
    <a-card class="recent-tasks" :bordered="false">
      <template #title>
        <span class="card-title">
          <HistoryOutlined />
          最近任务
          <a-tag color="blue" class="task-count" v-if="recentTasks.length > 0">
            {{ recentTasks.length }}
          </a-tag>
        </span>
      </template>
      
      <a-table
        :columns="columns"
        :data-source="recentTasks"
        :loading="loading"
        :pagination="{ pageSize: 5 }"
        row-key="id"
        class="tasks-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-badge 
              :status="getBadgeStatus(record.status)" 
              :text="getStatusText(record.status)"
              class="status-badge"
            />
          </template>

          <template v-if="column.key === 'progress'">
            <div class="progress-cell">
              <a-progress
                :percent="record.progress"
                size="small"
                :status="record.status === 'completed' ? 'success' : record.status === 'failed' ? 'exception' : undefined"
                :show-info="false"
              />
              <span class="progress-text">{{ record.progress }}%</span>
            </div>
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button
                v-if="record.status === 'completed'"
                type="primary"
                size="small"
                @click="handleDownloadById(record.id)"
              >
                <DownloadOutlined />
              </a-button>
              <a-button
                type="default"
                size="small"
                @click="handleViewDetail(record)"
              >
                <EyeOutlined />
              </a-button>
              <a-popconfirm
                title="确定删除此任务？"
                @confirm="handleDelete(record.id)"
              >
                <a-button type="default" size="small" danger>
                  <DeleteOutlined />
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import {
  CloudUploadOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  ReloadOutlined,
  EyeOutlined,
  InboxOutlined,
  SettingOutlined,
  GlobalOutlined,
  ThunderboltOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  FilePptOutlined,
  FileMarkdownOutlined,
  DeleteOutlined,
  CheckCircleFilled,
  CloseCircleFilled,
  ClockCircleFilled,
  LoadingOutlined,
  DashboardOutlined,
  BulbOutlined,
  HistoryOutlined,
  SwapOutlined,
  ColumnWidthOutlined,
  RocketOutlined,
  ToolOutlined,
  QuestionCircleOutlined,
  SafetyOutlined,
  InfoCircleOutlined
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
  target_lang: 'zh',
  model_name: 'deepseek-chat',
  thread_count: 5,
  display_mode: 1  // 1=替换模式, 2=对照模式, 3=表格对照...
})

const starting = ref(false)
const loading = ref(false)

// 当前任务
const currentTask = ref<TranslateTask | null>(null)

// 最近任务
const recentTasks = ref<TranslateTask[]>([])

// 进度定时器
let progressTimer: NodeJS.Timeout | null = null

// 计算当前步骤
const currentStep = computed(() => {
  if (!uploadedFileId.value) return 0
  if (!currentTask.value) return 1
  if (currentTask.value.status === 'processing') return 2
  if (currentTask.value.status === 'completed') return 3
  return 1
})

// 表格列
const columns = [
  { title: '文件名', dataIndex: 'file_name', key: 'file_name', ellipsis: true },
  { title: '目标语言', dataIndex: 'target_lang', key: 'target_lang', width: 90 },
  { title: '状态', key: 'status', width: 100 },
  { title: '进度', key: 'progress', width: 120 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 140, align: 'center' }
]

// 格式化文件大小
const formatFileSize = (size: number) => {
  if (!size) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let index = 0
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024
    index++
  }
  return `${size.toFixed(2)} ${units[index]}`
}

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
      size: file.size,
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
  fileList.value = []
  currentTask.value = null
  message.info('文件已移除')
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

  // 立即查询一次进度
  setTimeout(async () => {
    if (currentTask.value) {
      const progress = await translateStore.fetchProgress(currentTask.value.id)
      if (progress) {
        currentTask.value.status = progress.status
        currentTask.value.progress = progress.progress
        currentTask.value.translated_segments = progress.translated_segments
        currentTask.value.total_segments = progress.total_segments
        currentTask.value.error_message = progress.error_message
        
        if (progress.status === 'completed') {
          message.success('翻译完成！')
        }
      }
    }
  }, 500)

  // 然后每1秒轮询一次
  progressTimer = setInterval(async () => {
    if (!currentTask.value) return

    const progress = await translateStore.fetchProgress(currentTask.value.id)
    if (progress) {
      currentTask.value.status = progress.status
      currentTask.value.progress = progress.progress
      currentTask.value.translated_segments = progress.translated_segments
      currentTask.value.total_segments = progress.total_segments
      currentTask.value.error_message = progress.error_message

      if (progress.status === 'completed') {
        stopProgressPolling()
        fetchRecentTasks()
        message.success('翻译完成！')
      } else if (progress.status === 'failed') {
        stopProgressPolling()
        fetchRecentTasks()
        message.error('翻译失败：' + progress.error_message)
      }
    }
  }, 1000)
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
    message.success('开始下载')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

// 重置
const handleReset = () => {
  uploadedFileId.value = null
  fileList.value = []
  currentTask.value = null
  config.value = {
    source_lang: 'auto',
    target_lang: 'zh',
    model_name: 'deepseek-chat',
    thread_count: 5,
    display_mode: 1
  }
  message.info('已重置，可以上传新文件')
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

// 获取 Badge 状态
const getBadgeStatus = (status: string) => {
  const statuses: Record<string, any> = {
    pending: 'default',
    processing: 'processing',
    completed: 'success',
    failed: 'error'
  }
  return statuses[status] || 'default'
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

<style scoped lang="less">
.translate-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

// 页面头部
.page-header {
  text-align: center;
  margin-bottom: 32px;
  
  .page-title {
    font-size: 32px;
    font-weight: 600;
    color: #1f1f1f;
    margin-bottom: 8px;
    background: linear-gradient(135deg, #1890ff 0%, #52c41a 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .page-subtitle {
    font-size: 14px;
    color: #8c8c8c;
  }
}

// 步骤引导
.steps-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  
  :deep(.ant-card-body) {
    padding: 24px;
  }
}

// 卡片标题样式
.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
  
  .anticon {
    color: #1890ff;
    font-size: 18px;
  }
}

// 上传区域
.upload-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  
  :deep(.ant-card-body) {
    padding: 24px;
  }
}

.upload-area {
  .upload-dragger {
    border-radius: 8px;
    border: 2px dashed #d9d9d9;
    background: #fafafa;
    transition: all 0.3s;
    
    &:hover {
      border-color: #1890ff;
      background: #e6f7ff;
    }
  }
  
  .upload-content {
    padding: 32px 0;
    text-align: center;
  }
  
  .upload-icon-wrapper {
    width: 64px;
    height: 64px;
    margin: 0 auto 16px;
    background: linear-gradient(135deg, #e6f7ff 0%, #f6ffed 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .upload-icon {
    font-size: 28px;
    color: #1890ff;
  }
  
  .upload-text {
    font-size: 16px;
    font-weight: 500;
    color: #262626;
    margin-bottom: 8px;
  }
  
  .upload-hint {
    font-size: 14px;
    color: #8c8c8c;
    margin-bottom: 8px;
    
    :deep(.ant-space-item) {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }
  
  .upload-limit {
    font-size: 12px;
    color: #bfbfbf;
  }
}

// 文件信息卡片
.file-info-card {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;
  padding: 16px;
  
  .file-info-header {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .file-icon {
    width: 48px;
    height: 48px;
    background: #fff;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: #52c41a;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }
  
  .file-details {
    flex: 1;
    min-width: 0;
  }
  
  .file-name {
    font-size: 14px;
    font-weight: 500;
    color: #262626;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .file-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #8c8c8c;
  }
  
  .remove-btn {
    opacity: 0.6;
    transition: opacity 0.3s;
    
    &:hover {
      opacity: 1;
    }
  }
}

// 配置卡片
.config-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  
  :deep(.ant-card-body) {
    padding: 24px;
  }
}

.config-form {
  .form-section {
    margin-bottom: 24px;
    padding-bottom: 24px;
    border-bottom: 1px solid #f0f0f0;
    
    &:last-of-type {
      border-bottom: none;
      margin-bottom: 0;
      padding-bottom: 0;
    }
  }
  
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 500;
    color: #262626;
    margin-bottom: 16px;
    
    .anticon {
      color: #1890ff;
    }
  }
  
  .beta-tag {
    margin-left: 8px;
  }
}

// 语言选项
.lang-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

// 模型选项
.model-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

// 显示模式选项
.display-mode-options {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.mode-option {
  flex: 1;
  padding: 16px;
  border: 2px solid #d9d9d9;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  
  &:hover {
    border-color: #1890ff;
  }
  
  &.active {
    border-color: #1890ff;
    background: #e6f7ff;
    
    .mode-icon {
      background: #1890ff;
      color: #fff;
    }
  }
  
  .mode-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #f5f5f5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    color: #8c8c8c;
    margin-bottom: 12px;
    transition: all 0.3s;
    
    &.parallel {
      background: #f0f5ff;
      color: #1890ff;
    }
  }
  
  .mode-content {
    .mode-title {
      font-size: 14px;
      font-weight: 500;
      color: #262626;
      margin-bottom: 4px;
    }
    
    .mode-desc {
      font-size: 12px;
      color: #8c8c8c;
    }
  }
  
  .mode-check {
    position: absolute;
    top: 8px;
    right: 8px;
    color: #1890ff;
    font-size: 16px;
  }
}

// 模式预览
.mode-preview {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;
  padding: 16px;
  
  .preview-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #52c41a;
    margin-bottom: 12px;
    font-weight: 500;
  }
  
  .preview-content {
    background: #fff;
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 12px;
    
    .preview-original {
      font-size: 13px;
      color: #262626;
      margin-bottom: 8px;
      line-height: 1.6;
    }
    
    .preview-translated {
      font-size: 13px;
      color: #1890ff;
      text-decoration: underline;
      text-decoration-style: dashed;
      line-height: 1.6;
    }
  }
  
  .preview-hint {
    text-align: center;
  }
}

// 线程滑块
.thread-slider-wrapper {
  .thread-info {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    margin-top: 8px;
    font-size: 13px;
    color: #8c8c8c;
    
    .thread-count {
      font-size: 16px;
      font-weight: 600;
      color: #1890ff;
    }
    
    .thread-help {
      margin-left: 8px;
      cursor: help;
      color: #bfbfbf;
      
      &:hover {
        color: #1890ff;
      }
    }
  }
}

// 提交区域
.submit-section {
  margin-top: 32px;
  margin-bottom: 0 !important;
  
  .start-btn {
    height: 48px;
    font-size: 16px;
    font-weight: 500;
    border-radius: 8px;
    
    .anticon {
      font-size: 18px;
    }
  }
  
  .submit-hint {
    text-align: center;
    margin-top: 12px;
    font-size: 12px;
    color: #8c8c8c;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
  }
}

// 任务卡片
.task-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  
  :deep(.ant-card-body) {
    padding: 24px;
  }
}

// 空状态
.empty-state {
  text-align: center;
  padding: 48px 0;
  
  .empty-icon {
    width: 80px;
    height: 80px;
    margin: 0 auto 16px;
    background: #f5f5f5;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    color: #bfbfbf;
  }
  
  .empty-title {
    font-size: 16px;
    font-weight: 500;
    color: #262626;
    margin-bottom: 8px;
  }
  
  .empty-desc {
    font-size: 14px;
    color: #8c8c8c;
  }
}

// 任务进度
.task-progress {
  .task-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
  }
  
  .task-status-icon {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    
    &.pending {
      background: #f5f5f5;
      color: #8c8c8c;
    }
    
    &.processing {
      background: #e6f7ff;
      color: #1890ff;
    }
    
    &.completed {
      background: #f6ffed;
      color: #52c41a;
    }
    
    &.failed {
      background: #fff2f0;
      color: #ff4d4f;
    }
  }
  
  .task-status-info {
    flex: 1;
  }
  
  .task-status-text {
    font-size: 18px;
    font-weight: 500;
    color: #262626;
    margin-bottom: 4px;
  }
  
  .task-progress-text {
    font-size: 14px;
    color: #8c8c8c;
  }
  
  .progress-wrapper {
    margin-bottom: 24px;
  }
  
  .progress-bar {
    :deep(.ant-progress-inner) {
      border-radius: 6px;
    }
    
    :deep(.ant-progress-bg) {
      border-radius: 6px;
    }
  }
  
  .task-details {
    background: #f5f5f5;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 24px;
    
    .detail-item {
      margin-bottom: 12px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
    
    .detail-row {
      display: flex;
      gap: 24px;
      
      .detail-item {
        flex: 1;
        margin-bottom: 0;
      }
    }
    
    .detail-label {
      font-size: 12px;
      color: #8c8c8c;
      display: block;
      margin-bottom: 4px;
    }
    
    .detail-value {
      font-size: 14px;
      color: #262626;
      font-weight: 500;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      display: block;
    }
  }
  
  .task-actions {
    .download-btn {
      height: 44px;
      font-size: 15px;
    }
    
    .reset-btn {
      height: 44px;
      font-size: 15px;
    }
  }
}

// 错误提示
.error-message {
  .error-alert {
    border-radius: 8px;
  }
}

// 提示卡片
.tips-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  
  :deep(.ant-card-body) {
    padding: 24px;
  }
}

.tips-list {
  .tip-item {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .tip-icon {
    width: 28px;
    height: 28px;
    min-width: 28px;
    background: #e6f7ff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 600;
    color: #1890ff;
  }
  
  .tip-content {
    flex: 1;
  }
  
  .tip-title {
    font-size: 14px;
    font-weight: 500;
    color: #262626;
    margin-bottom: 2px;
  }
  
  .tip-desc {
    font-size: 13px;
    color: #8c8c8c;
    line-height: 1.5;
  }
}

// 最近任务
.recent-tasks {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  
  :deep(.ant-card-body) {
    padding: 24px;
  }
  
  .task-count {
    margin-left: 8px;
  }
}

.tasks-table {
  :deep(.ant-table-thead > tr > th) {
    background: #f5f5f5;
    font-weight: 500;
  }
  
  .progress-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .progress-text {
      font-size: 12px;
      color: #8c8c8c;
      min-width: 36px;
    }
  }
  
  .status-badge {
    :deep(.ant-badge-status-text) {
      font-size: 13px;
    }
  }
}

// 响应式优化
@media (max-width: 768px) {
  .translate-page {
    padding: 16px;
  }
  
  .page-header {
    .page-title {
      font-size: 24px;
    }
  }
  
  .display-mode-options {
    flex-direction: column;
  }
  
  .mode-option {
    flex-direction: row;
    text-align: left;
    padding: 12px;
    
    .mode-icon {
      width: 40px;
      height: 40px;
      margin-bottom: 0;
      margin-right: 12px;
    }
    
    .mode-content {
      flex: 1;
    }
  }
  
  .task-details {
    .detail-row {
      flex-direction: column;
      gap: 12px;
    }
  }
}
</style>
