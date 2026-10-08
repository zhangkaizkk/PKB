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
export type OcrStatus = 'pending' | 'processing' | 'done' | 'failed' | 'skipped'

export interface FileItem {
  public_id: string
  original_name: string
  title: string
  mime_type: string
  size_bytes: number
  sha256: string
  extract_status: ExtractStatus
  extract_error: string | null
  ocr_status: OcrStatus
  ocr_error: string | null
  indexed_at: string | null
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

// ============================
// RAG 相关类型
// ============================
export interface Citation {
  public_id: string | null
  title: string | null
  chunk_index: number | null
  snippet: string | null
  score: number | null
}

export interface RagAskRequest {
  question: string
  top_k_retrieve?: number
  top_k_rerank?: number
  local_only?: boolean
}

export interface RagAskResponse {
  answer: string
  citations: Citation[]
  chat_model: string | null
  embed_model: string | null
  prompt_tokens: number
  completion_tokens: number
  latency_ms: number
}

export interface RagHistoryItem {
  id: number
  question: string
  answer: string
  citations: Citation[] | null
  chat_model: string | null
  embed_model: string | null
  prompt_tokens: number | null
  completion_tokens: number | null
  latency_ms: number | null
  created_at: string
}

export interface RagStatsResponse {
  total_chunks: number
  unique_documents: number
  collection: string
}

export interface RagConfigResponse {
  chat_model: string
  chat_base_url: string
  embed_model: string
  embed_base_url: string
  embed_dim: number
  rerank_mode: string
  local_only: boolean
}

export interface RagIndexedDocument {
  public_id: string
  title: string
  original_name: string
  chunk_count: number
  indexed_at: string | null
}

export interface RagIndexedListResponse {
  documents: RagIndexedDocument[]
}
