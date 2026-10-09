import http from './http'
import type { FileItem, Paginated, TagUpdateRequest, UploadResponse } from '@/types'

export interface FileListQuery {
  q?: string
  tag_id?: number
  status?: 'active' | 'trashed'
  page?: number
  page_size?: number
}

export const filesApi = {
  list(params: FileListQuery = {}) {
    return http.get<Paginated<FileItem>>('/files', { params })
  },

  upload(formData: FormData, onProgress?: (p: number) => void) {
    return http.post<UploadResponse>('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (!onProgress) return
        if (e.total && e.total > 0) {
          onProgress(Math.round((e.loaded / e.total) * 100))
        } else if (e.loaded > 0) {
          // e.total 缺失时，用已上传字节数做一个粗略进度（0~99，留 100 给 then()）
          // 避免直接跳到 100，让 then() 里的 final 赋值驱动完成态切换
          onProgress(Math.min(99, Math.round((e.loaded / 1024 / 1024) * 2)))
        }
      },
    })
  },

  get(publicId: string) {
    return http.get<FileItem>(`/files/${publicId}`)
  },

  patch(publicId: string, data: { title?: string; original_name?: string }) {
    return http.patch<FileItem>(`/files/${publicId}`, data)
  },

  softDelete(publicId: string) {
    return http.delete<FileItem>(`/files/${publicId}`)
  },

  restore(publicId: string) {
    return http.post<FileItem>(`/files/${publicId}/restore`)
  },

  purge(publicId: string) {
    return http.delete(`/files/${publicId}/purge`)
  },

  purgeAll() {
    return http.delete<{ purged_count: number }>('/files/purge-all')
  },

  updateTags(publicId: string, data: TagUpdateRequest) {
    return http.put<FileItem>(`/files/${publicId}/tags`, data)
  },

  /** 带认证下载文件 — 返回 Blob，调用方负责触发浏览器下载 */
  async download(publicId: string, originalName: string) {
    const res = await http.get(`/files/${publicId}/download`, {
      responseType: 'blob',
    })
    const blob = res.data as Blob
    // Content-Disposition 里可能有后端指定的文件名，但我们用前端已知的 originalName 更可靠
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = originalName || `file-${publicId}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(url), 2000)
  },

  /** TXT/MD 预览 — 返回文本内容；图片/PDF 不走此方法，直接用 preview_url */
  previewText(publicId: string) {
    return http.get<{ content: string }>(`/files/${publicId}/preview`)
  },
}
