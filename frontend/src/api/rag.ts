import http from './http'
import type {
  RagAskRequest,
  RagAskResponse,
  RagHistoryItem,
  RagIndexedListResponse,
  RagReindexStatus,
  RagReindexTask,
  RagStatsResponse,
  RagConfigResponse,
} from '@/types'

export const ragApi = {
  ask: (payload: RagAskRequest) => http.post<RagAskResponse>('/rag/ask', payload),

  history: (limit = 50) => http.get<RagHistoryItem[]>('/rag/history', { params: { limit } }),

  reindexAll: () => http.post<RagReindexTask>('/rag/reindex'),

  reindexStatus: (taskId: string) =>
    http.get<RagReindexStatus>('/rag/reindex/status', { params: { task_id: taskId } }),

  reindexOne: (publicId: string) => http.post<{ message: string }>(`/rag/reindex/${publicId}`),

  stats: () => http.get<RagStatsResponse>('/rag/stats'),

  config: () => http.get<RagConfigResponse>('/rag/config'),

  indexedDocuments: () => http.get<RagIndexedListResponse>('/rag/indexed-documents'),
}
