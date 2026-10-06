import { defineStore } from 'pinia'
import { ref } from 'vue'
import { filesApi } from '@/api/files'
import { useFilesStore } from './files'

export interface UploadTask {
  id: string
  name: string
  size: number
  status: 'pending' | 'uploading' | 'done' | 'error' | 'duplicate'
  progress: number
  error?: string
}

export const useUploadStore = defineStore('upload', () => {
  const queue = ref<UploadTask[]>([])
  const MAX_CONCURRENT = 3
  const _active = ref(0)
  let _refreshTimer: ReturnType<typeof setTimeout> | null = null

  /** 延迟刷新 files 列表，多文件并发时合并成一次请求 */
  function _scheduleRefresh() {
    if (_refreshTimer) return
    _refreshTimer = setTimeout(() => {
      _refreshTimer = null
      const files = useFilesStore()
      files.list()
    }, 400)
  }

  function enqueue(file: File) {
    const task: UploadTask = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      name: file.name,
      size: file.size,
      status: 'pending',
      progress: 0,
    }
    queue.value.push(task)
    _kick(file, task)
  }

  function _kick(file: File, task: UploadTask) {
    if (_active.value >= MAX_CONCURRENT) return
    _active.value++
    task.status = 'uploading'
    task.progress = 5  // 起步值：避免快传场景下进度条一直停 0

    const form = new FormData()
    form.append('files', file)

    filesApi
      .upload(form, (p) => {
        if (p > task.progress) task.progress = p  // 单调递增，避免 then() 里的 100 被后续事件覆盖
      })
      .then((res) => {
        const item = res.data.items[0]
        if (!item) {
          Object.assign(task, { status: 'error' as const, error: '服务器无响应' })
        } else if (item.status === 'duplicate') {
          Object.assign(task, { status: 'duplicate' as const, progress: 100 })
          _scheduleRefresh()
        } else if (item.status === 'created') {
          Object.assign(task, { status: 'done' as const, progress: 100 })
          _scheduleRefresh()
        } else {
          Object.assign(task, { status: 'error' as const, error: item.error || '上传失败' })
        }
      })
      .catch((err) => {
        Object.assign(task, { status: 'error' as const, error: err?.message || '网络错误' })
      })
      .finally(() => {
        _active.value--
      })
  }

  function removeDone() {
    queue.value = queue.value.filter((q) => q.status === 'uploading' || q.status === 'pending')
  }

  return { queue, enqueue, removeDone }
})
