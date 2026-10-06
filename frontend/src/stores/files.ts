import { defineStore } from 'pinia'
import { ref } from 'vue'
import { filesApi, type FileListQuery } from '@/api/files'
import type { FileItem, Paginated } from '@/types'

export const useFilesStore = defineStore('files', () => {
  const items = ref<FileItem[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const currentPreview = ref<FileItem | null>(null)

  async function list(q?: string, tagId?: number, status: 'active' | 'trashed' = 'active', p = 1) {
    loading.value = true
    page.value = p
    try {
      const res = await filesApi.list({
        q, tag_id: tagId, status, page: p, page_size: pageSize.value,
      } as FileListQuery)
      const data: Paginated<FileItem> = res.data
      items.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  function openPreview(item: FileItem) {
    currentPreview.value = item
  }

  function closePreview() {
    currentPreview.value = null
  }

  return { items, total, page, pageSize, loading, currentPreview, list, openPreview, closePreview }
})
