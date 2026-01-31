<template>
  <a-modal
    :open="visible"
    :title="title"
    width="900px"
    :footer="null"
    @cancel="handleCancel"
    class="preview-modal"
  >
    <div class="preview-container">
      <!-- 工具栏 -->
      <div class="preview-toolbar">
        <a-radio-group v-model:value="viewMode" size="small">
          <a-radio-button value="source">原文预览</a-radio-button>
          <a-radio-button value="parallel" :disabled="!canParallel">对照预览</a-radio-button>
        </a-radio-group>

        <a-space>
          <a-tag v-if="loading" color="processing">
            <SyncOutlined spin />
            加载中...
          </a-tag>
          <a-tag v-else-if="truncated" color="warning">
            <InfoCircleOutlined />
            内容已截断
          </a-tag>
          <span v-if="contentStats" class="stats-text">{{ contentStats }}</span>
        </a-space>
      </div>

      <!-- 内容区域 -->
      <div class="preview-content" v-loading="loading">
        <!-- 原文预览模式 -->
        <div v-if="viewMode === 'source'" class="source-view">
          <div v-if="sourceContent.length === 0" class="empty-content">
            <a-empty description="暂无内容" />
          </div>
          <div v-else class="content-list">
            <div
              v-for="(item, index) in sourceContent"
              :key="`source-${index}`"
              :class="['content-item', `type-${item.type}`]"
            >
              <div v-if="item.location" class="item-location">{{ item.location }}</div>
              <div class="item-text">{{ item.text }}</div>
            </div>
          </div>
        </div>

        <!-- 对照预览模式 -->
        <div v-else-if="viewMode === 'parallel'" class="parallel-view">
          <div v-if="parallelContent.length === 0" class="empty-content">
            <a-empty description="暂无对照内容，请先完成翻译" />
          </div>
          <div v-else class="parallel-list">
            <div
              v-for="(pair, index) in parallelContent"
              :key="`pair-${index}`"
              class="parallel-pair"
            >
              <div v-if="pair.location" class="pair-location">{{ pair.location }}</div>
              <div class="pair-content">
                <div class="source-box">
                  <div class="box-label">原文</div>
                  <div class="box-text">{{ pair.source }}</div>
                </div>
                <div class="arrow-divider">
                  <ArrowRightOutlined />
                </div>
                <div class="translated-box">
                  <div class="box-label">译文</div>
                  <div class="box-text">{{ pair.translated }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  SyncOutlined,
  InfoCircleOutlined,
  ArrowRightOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { getTranslatePreview, getTranslateParallelPreview } from '@/api/translate'

interface PreviewContentItem {
  type: string
  text: string
  index: number | string
  location?: string
  prefix?: string
}

interface Props {
  visible: boolean
  taskId: number | null
  fileName: string
  status: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

// 状态
const loading = ref(false)
const viewMode = ref<'source' | 'parallel'>('source')
const sourceContent = ref<PreviewContentItem[]>([])
const translatedContent = ref<PreviewContentItem[]>([])
const truncated = ref(false)
const format = ref('')
const totalChars = ref(0)

// 计算属性
const title = computed(() => `文件预览 - ${props.fileName}`)

const canParallel = computed(() => {
  return props.status === 'completed' || translatedContent.value.length > 0
})

const contentStats = computed(() => {
  if (sourceContent.value.length === 0) return ''
  const items = sourceContent.value.length
  const chars = totalChars.value
  return `${items} 个片段 · ${chars} 字符`
})

// 对照内容配对
const parallelContent = computed(() => {
  const pairs: Array<{ source: string; translated: string; location?: string }> = []
  const maxLen = Math.max(sourceContent.value.length, translatedContent.value.length)

  for (let i = 0; i < maxLen; i++) {
    const source = sourceContent.value[i]
    const translated = translatedContent.value[i]

    pairs.push({
      source: source?.text || '',
      translated: translated?.text || '',
      location: source?.location || translated?.location
    })
  }

  return pairs
})

// 加载预览内容
const loadPreview = async () => {
  if (!props.taskId) return

  loading.value = true
  try {
    // 加载原文
    const sourceRes = await getTranslatePreview(props.taskId, 5000)
    if (sourceRes.success) {
      sourceContent.value = sourceRes.data.content || []
      truncated.value = sourceRes.data.truncated || false
      format.value = sourceRes.data.format || ''
      totalChars.value = sourceRes.data.total_chars || 0
    }

    // 如果是对照模式且任务已完成，加载译文
    if (viewMode.value === 'parallel' && props.status === 'completed') {
      const parallelRes = await getTranslateParallelPreview(props.taskId, 5000)
      if (parallelRes.success) {
        translatedContent.value = parallelRes.data.translated_content || []
      }
    }
  } catch (error) {
    message.error('加载预览内容失败')
  } finally {
    loading.value = false
  }
}

// 监听 visible 变化
watch(() => props.visible, (newVal) => {
  if (newVal && props.taskId) {
    loadPreview()
  }
})

// 监听 viewMode 变化
watch(viewMode, async (newMode) => {
  if (newMode === 'parallel' && props.status === 'completed' && translatedContent.value.length === 0) {
    loading.value = true
    try {
      const parallelRes = await getTranslateParallelPreview(props.taskId!, 5000)
      if (parallelRes.success) {
        translatedContent.value = parallelRes.data.translated_content || []
      }
    } catch (error) {
      message.error('加载对照内容失败')
    } finally {
      loading.value = false
    }
  }
})

// 关闭对话框
const handleCancel = () => {
  emit('update:visible', false)
  // 重置状态
  viewMode.value = 'source'
  sourceContent.value = []
  translatedContent.value = []
}
</script>

<style scoped>
.preview-modal :deep(.ant-modal-body) {
  padding: 0;
}

.preview-container {
  display: flex;
  flex-direction: column;
  max-height: 70vh;
}

.preview-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.stats-text {
  font-size: 12px;
  color: #666;
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  min-height: 300px;
  max-height: calc(70vh - 60px);
}

/* 原文预览样式 */
.source-view .content-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.content-item {
  padding: 12px 16px;
  background: #f6ffed;
  border-left: 3px solid #52c41a;
  border-radius: 4px;
}

.content-item.type-heading {
  background: #e6f7ff;
  border-left-color: #1890ff;
  font-weight: 500;
}

.content-item.type-table,
.content-item.type-cell {
  background: #fff7e6;
  border-left-color: #faad14;
}

.content-item.type-code {
  background: #f5f5f5;
  border-left-color: #999;
  font-family: monospace;
}

.content-item.type-list {
  background: #f9f0ff;
  border-left-color: #722ed1;
}

.item-location {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.item-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 对照预览样式 */
.parallel-view .parallel-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.parallel-pair {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
}

.pair-location {
  padding: 8px 12px;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  font-size: 12px;
  color: #666;
}

.pair-content {
  display: flex;
  align-items: stretch;
  gap: 0;
}

.source-box,
.translated-box {
  flex: 1;
  padding: 12px;
  min-width: 0;
}

.source-box {
  background: #fff2f0;
}

.translated-box {
  background: #f6ffed;
}

.box-label {
  font-size: 12px;
  font-weight: 500;
  color: #666;
  margin-bottom: 8px;
}

.box-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
}

.arrow-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  background: #fafafa;
  border-left: 1px solid #e8e8e8;
  border-right: 1px solid #e8e8e8;
  color: #999;
}

.empty-content {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

/* 响应式 */
@media (max-width: 768px) {
  .pair-content {
    flex-direction: column;
  }

  .arrow-divider {
    width: 100%;
    height: 40px;
    border-left: none;
    border-right: none;
    border-top: 1px solid #e8e8e8;
    border-bottom: 1px solid #e8e8e8;
  }
}
</style>
