/**
 * 翻译状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getTranslateList,
  getTranslateProgress,
  type TranslateTask
} from '@/api/translate'
import { message } from 'ant-design-vue'

export const useTranslateStore = defineStore('translate', () => {
  // 状态
  const tasks = ref<TranslateTask[]>([])
  const currentTask = ref<TranslateTask | null>(null)
  const loading = ref(false)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)

  /**
   * 获取翻译列表
   */
  const fetchTasks = async (params?: { page?: number; page_size?: number; status?: string }) => {
    try {
      loading.value = true
      const res = await getTranslateList({
        page: params?.page || page.value,
        page_size: params?.page_size || pageSize.value,
        status: params?.status
      })

      tasks.value = res.data.items
      total.value = res.data.total
      page.value = res.data.page
    } catch (error) {
      console.error('获取翻译列表失败:', error)
      message.error('获取翻译列表失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取翻译进度
   */
  const fetchProgress = async (taskId: number) => {
    try {
      const res = await getTranslateProgress(taskId)
      return res.data
    } catch (error) {
      console.error('获取翻译进度失败:', error)
      return null
    }
  }

  /**
   * 设置当前任务
   */
  const setCurrentTask = (task: TranslateTask | null) => {
    currentTask.value = task
  }

  /**
   * 添加任务
   */
  const addTask = (task: TranslateTask) => {
    tasks.value.unshift(task)
    total.value += 1
  }

  /**
   * 更新任务
   */
  const updateTask = (taskId: number, updates: Partial<TranslateTask>) => {
    const index = tasks.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
      tasks.value[index] = { ...tasks.value[index], ...updates }
    }

    if (currentTask.value?.id === taskId) {
      currentTask.value = { ...currentTask.value, ...updates }
    }
  }

  /**
   * 删除任务
   */
  const removeTask = (taskId: number) => {
    const index = tasks.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
      tasks.value.splice(index, 1)
      total.value -= 1
    }

    if (currentTask.value?.id === taskId) {
      currentTask.value = null
    }
  }

  return {
    // 状态
    tasks,
    currentTask,
    loading,
    total,
    page,
    pageSize,
    // 方法
    fetchTasks,
    fetchProgress,
    setCurrentTask,
    addTask,
    updateTask,
    removeTask
  }
})
