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
  const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
  if (match && match[1]) {
    filename = match[1].replace(/['"]/g, '')
  }

  // 创建下载链接
  const blob = new Blob([response.data])  // 修复：使用 response.data 而不是 response
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
