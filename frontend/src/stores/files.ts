import { defineStore } from 'pinia'
import { ref } from 'vue'
import { filesApi, type FileListQuery } from '@/api/files'
import type { FileItem, Paginated } from '@/types'

// 需要 fetch 文本内容的文件类型
const TEXT_EXTS = ['.txt', '.md', '.markdown']
const isText = (item: FileItem) =>
  (item.mime_type || '').startsWith('text/') ||
  TEXT_EXTS.some((e) => (item.original_name || '').toLowerCase().endsWith(e))

export const useFilesStore = defineStore('files', () => {
  const items = ref<FileItem[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const currentPreview = ref<FileItem | null>(null)

  // TXT/MD 预览内容
  const previewContent = ref('')
  const previewLoading = ref(false)
  const previewError = ref('')

  async function list(
    q?: string,
    tagId?: number,
    status: 'active' | 'trashed' = 'active',
    p = 1,
    size?: number,
  ) {
    loading.value = true
    page.value = p
    if (size !== undefined) pageSize.value = size
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

  async function openPreview(item: FileItem) {
    // 先清旧内容
    previewContent.value = ''
    previewError.value = ''
    currentPreview.value = item

    // 只有 TXT/MD 需要 fetch 内容；图片/PDF 直接用 preview_url
    if (isText(item)) {
      previewLoading.value = true
      try {
        const res = await filesApi.previewText(item.public_id)
        previewContent.value = res.data.content
      } catch (e: any) {
        previewError.value = e?.response?.status === 415
          ? '该格式暂不支持在线预览'
          : '加载预览内容失败'
      } finally {
        previewLoading.value = false
      }
    }
  }

  function closePreview() {
    currentPreview.value = null
    previewContent.value = ''
    previewError.value = ''
  }

  return {
    items, total, page, pageSize, loading,
    currentPreview, previewContent, previewLoading, previewError,
    list, openPreview, closePreview,
  }
})
