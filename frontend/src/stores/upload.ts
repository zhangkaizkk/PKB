import { defineStore } from 'pinia'
import { ref } from 'vue'
import { filesApi } from '@/api/files'

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

    const form = new FormData()
    form.append('files', file)

    filesApi
      .upload(form, (p) => (task.progress = p))
      .then((res) => {
        const item = res.data.items[0]
        if (!item) {
          task.status = 'error'
          task.error = '服务器无响应'
        } else if (item.status === 'duplicate') {
          task.status = 'duplicate'
          task.progress = 100
        } else if (item.status === 'created') {
          task.status = 'done'
          task.progress = 100
        } else {
          task.status = 'error'
          task.error = item.error || '上传失败'
        }
      })
      .catch((err) => {
        task.status = 'error'
        task.error = err?.message || '网络错误'
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
