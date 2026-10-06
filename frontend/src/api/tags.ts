import http from './http'
import type { Tag } from '@/types'

export const tagsApi = {
  list() {
    return http.get<Tag[]>('/tags')
  },
  create(data: { name: string; color?: string }) {
    return http.post<Tag>('/tags', data)
  },
  update(id: number, data: { name?: string; color?: string | null }) {
    return http.patch<Tag>(`/tags/${id}`, data)
  },
  remove(id: number) {
    return http.delete(`/tags/${id}`)
  },
}
