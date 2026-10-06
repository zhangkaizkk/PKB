import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'
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
  // reactive 数组：push/pop + 内部元素属性修改都自动触发更新，不需要整体替换引用
  const queue = reactive<UploadTask[]>([])
  const MAX_CONCURRENT = 3
  const _active = ref(0)
  let _refreshTimer: ReturnType<typeof setTimeout> | null = null

  function _scheduleRefresh() {
    if (_refreshTimer) return
    _refreshTimer = setTimeout(() => {
      _refreshTimer = null
      useFilesStore().list()
    }, 400)
  }

  /** 直接修改数组元素属性（reactive 数组天然支持深层属性修改触发更新） */
  function _patchTask(id: string, patch: Partial<UploadTask>) {
    const i = queue.findIndex((t) => t.id === id)
    if (i >= 0) Object.assign(queue[i], patch)
  }

  function enqueue(file: File) {
    queue.push({
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      name: file.name,
      size: file.size,
      status: 'pending',
      progress: 0,
    })
    _kick(file, queue[queue.length - 1].id)
  }

  function _kick(file: File, taskId: string) {
    if (_active.value >= MAX_CONCURRENT) return
    _active.value++
    _patchTask(taskId, { status: 'uploading', progress: 5 })

    const form = new FormData()
    form.append('files', file)

    filesApi
      .upload(form, (p) => {
        const cur = queue.find((t) => t.id === taskId)
        if (cur && p > cur.progress) cur.progress = p
      })
      .then((res) => {
        const item = res.data.items[0]
        if (!item) {
          _patchTask(taskId, { status: 'error', error: '服务器无响应' })
        } else if (item.status === 'duplicate') {
          _patchTask(taskId, { status: 'duplicate', progress: 100 })
          _scheduleRefresh()
        } else if (item.status === 'created') {
          _patchTask(taskId, { status: 'done', progress: 100 })
          _scheduleRefresh()
        } else {
          _patchTask(taskId, { status: 'error', error: item.error || '上传失败' })
        }
      })
      .catch((err) => {
        _patchTask(taskId, { status: 'error', error: err?.message || '网络错误' })
      })
      .finally(() => {
        _active.value--
      })
  }

  function removeDone() {
    // reactive 数组不能直接 filter 赋值，用 splice 原地删除
    for (let i = queue.length - 1; i >= 0; i--) {
      if (queue[i].status !== 'uploading' && queue[i].status !== 'pending') queue.splice(i, 1)
    }
  }

  return { queue, enqueue, removeDone }
})
