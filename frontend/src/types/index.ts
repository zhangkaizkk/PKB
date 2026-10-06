/** 全局类型定义 — 与后端 schema 对齐。 */

export interface User {
  id: number
  username: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface Tag {
  id: number
  name: string
  color: string | null
  created_at?: string
}

export type ExtractStatus = 'pending' | 'done' | 'failed' | 'skipped'

export interface FileItem {
  public_id: string
  original_name: string
  title: string
  mime_type: string
  size_bytes: number
  sha256: string
  extract_status: ExtractStatus
  extract_error: string | null
  tags: Tag[]
  created_at: string
  updated_at: string
  deleted_at: string | null
  preview_url: string
  download_url: string
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface UploadItem {
  status: 'created' | 'duplicate' | 'failed'
  file: FileItem | null
  error: string | null
}

export interface UploadResponse {
  items: UploadItem[]
}

export interface TagUpdateRequest {
  tag_ids: number[]
}
