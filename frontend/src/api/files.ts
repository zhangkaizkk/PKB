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
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded / e.total) * 100))
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

  updateTags(publicId: string, data: TagUpdateRequest) {
    return http.put<FileItem>(`/files/${publicId}/tags`, data)
  },
}
