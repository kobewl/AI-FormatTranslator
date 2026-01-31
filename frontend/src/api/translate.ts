/**
 * 翻译相关 API
 */
import { http } from './index'

export interface TranslateTask {
  id: number
  uuid: string
  file_name: string
  file_size: number
  file_type: string
  source_lang: string
  target_lang: string
  model_name: string
  status: string
  progress: number
  created_at: string
  completed_at?: string
}

export interface TranslateRequest {
  file_id: number
  source_lang: string
  target_lang: string
  model_name: string
  thread_count?: number
  prompt_id?: number
  display_mode?: number  // 1=替换模式, 2=对照模式, 3=表格对照...
  domain?: string  // 翻译领域：general/medical/it/legal/finance...
}

/**
 * 上传文件
 */
export const uploadFile = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<any>('/translate/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 启动翻译
 */
export const startTranslate = (data: TranslateRequest) => {
  return http.post<any>('/translate/start', data)
}

/**
 * 获取翻译列表
 */
export const getTranslateList = (params: { page?: number; page_size?: number; status?: string }) => {
  return http.get<any>('/translate/list', { params })
}

/**
 * 获取翻译详情
 */
export const getTranslateDetail = (id: number) => {
  return http.get<any>(`/translate/${id}`)
}

/**
 * 查询翻译进度
 */
export const getTranslateProgress = (id: number) => {
  return http.get<any>(`/translate/${id}/progress`)
}

/**
 * 下载翻译结果（使用 Blob 方式，携带认证信息）
 */
export const downloadTranslateResult = async (id: number) => {
  const response = await http.get(`/translate/${id}/download`, {
    responseType: 'blob'
  })

  // 从响应头中获取文件名
  const contentDisposition = response.headers?.['content-disposition'] || ''
  let filename = `translated_${id}.docx`

  console.log('Content-Disposition:', contentDisposition)

  // 解析 filename*=UTF-8'' 格式
  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;\s]+)/)
  if (utf8Match && utf8Match[1]) {
    // URL 解码
    filename = decodeURIComponent(utf8Match[1])
    console.log('解析后的文件名 (UTF-8):', filename)
  } else {
    // 尝试解析 filename= 格式
    const normalMatch = contentDisposition.match(/filename=([^;\s]+)/)
    if (normalMatch && normalMatch[1]) {
      // 去除引号
      filename = normalMatch[1].replace(/['"]/g, '')
      console.log('解析后的文件名 (普通):', filename)
    }
  }

  console.log('最终文件名:', filename)

  // 创建下载链接
  const blob = new Blob([response.data])
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)

  return { success: true }
}

/**
 * 删除翻译任务
 */
export const deleteTranslate = (id: number) => {
  return http.delete<any>(`/translate/${id}`)
}

/**
 * 重试翻译任务
 * 基于已完成的任务创建新的翻译任务，使用相同的文件但允许修改翻译参数
 */
export const retryTranslate = (taskId: number, data: TranslateRequest) => {
  return http.post<any>(`/translate/retry?task_id=${taskId}`, data)
}

/**
 * 获取翻译任务的源文件预览
 * 支持 docx/pdf/xlsx/pptx/md/txt 格式
 */
export const getTranslatePreview = (id: number, maxChars?: number) => {
  return http.get<any>(`/translate/${id}/preview`, {
    params: { max_chars: maxChars || 5000 }
  })
}

/**
 * 获取翻译任务的对照预览（原文+译文）
 * 同时提取源文件和翻译结果文件的内容
 */
export const getTranslateParallelPreview = (id: number, maxChars?: number) => {
  return http.get<any>(`/translate/${id}/preview-parallel`, {
    params: { max_chars: maxChars || 5000 }
  })
}
