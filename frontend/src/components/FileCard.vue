<script setup lang="ts">
import { h } from 'vue'
import { NButton, NTag, NPopconfirm, NDropdown } from 'naive-ui'
import { Download, Eye, Pencil, Trash, Refresh, Close, Document, Image, Film, Code, DocumentText, FolderOutline } from '@vicons/ionicons5'
import { useMessage, useDialog } from 'naive-ui'
import { filesApi } from '@/api/files'
import type { FileItem } from '@/types'

const props = defineProps<{ item: FileItem; trashed?: boolean }>()
const emit = defineEmits<{ refresh: []; 'refresh:tags': []; openPreview: [item: FileItem] }>()

const message = useMessage()
const dialog = useDialog()

function fmtSize(b: number) {
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  if (b < 1024 * 1024 * 1024) return `${(b / 1024 / 1024).toFixed(1)} MB`
  return `${(b / 1024 / 1024 / 1024).toFixed(2)} GB`
}

function fmtDate(iso?: string | null) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString()
}

function iconFor(mime: string) {
  if (mime.startsWith('image/')) return Image
  if (mime === 'application/pdf') return DocumentText
  if (mime.startsWith('video/')) return Film
  if (['text/plain', 'text/markdown'].includes(mime)) return Code
  if (mime.includes('msword') || mime.includes('docx')) return Document
  if (mime.includes('excel') || mime.includes('spreadsheet') || mime.includes('xlsx')) return Document
  if (mime.includes('presentation') || mime.includes('pptx')) return Document
  return FolderOutline
}

function onPreview() {
  emit('openPreview', props.item)
}

async function onDownload() {
  try {
    await filesApi.download(props.item.public_id, props.item.original_name)
  } catch (err: any) {
    message.error(err?.response?.data?.detail || '下载失败')
  }
}

async function onRename() {
  try {
    const val = await dialog.warning({
      title: '重命名',
      content: '',
      action: () => {},
      positiveText: '保存',
      negativeText: '取消',
    })
    // NDialog 简化版：直接用 prompt
    const newName = window.prompt('新名称', props.item.original_name)
    if (!newName || newName === props.item.original_name) return
    await filesApi.patch(props.item.public_id, { original_name: newName })
    message.success('已重命名')
    emit('refresh')
  } catch { /* user cancel */ }
}

async function onSoftDelete() {
  await filesApi.softDelete(props.item.public_id)
  message.success('已移入回收站')
  emit('refresh')
}

async function onRestore() {
  await filesApi.restore(props.item.public_id)
  message.success('已恢复')
  emit('refresh')
}

async function onPurge() {
  dialog.warning({
    title: '彻底删除',
    content: `将永久删除 "${props.item.original_name}"，无法恢复。`,
    positiveText: '彻底删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await filesApi.purge(props.item.public_id)
      message.success('已彻底删除')
      emit('refresh')
    },
  })
}
</script>

<template>
  <div class="file-card">
    <div class="fc-icon">
      <n-icon :component="iconFor(item.mime_type)" :size="28" />
    </div>
    <div class="fc-info">
      <div class="fc-name" :title="item.original_name">{{ item.title }}</div>
      <div class="fc-meta">
        {{ fmtSize(item.size_bytes) }} · {{ fmtDate(item.updated_at) }}
      </div>
      <div v-if="item.tags.length" class="fc-tags">
        <n-tag v-for="t in item.tags" :key="t.id" size="tiny" round :bordered="t.color === null" :type="t.color ? undefined : 'default'" :color="(t.color as any) || undefined">{{ t.name }}</n-tag>
      </div>
    </div>
    <div class="fc-actions">
      <n-button size="tiny" quaternary @click="onPreview"><n-icon :component="Eye" /> 预览</n-button>
      <n-button size="tiny" quaternary @click="onDownload"><n-icon :component="Download" /> 下载</n-button>
      <n-button v-if="!trashed" size="tiny" quaternary @click="onRename"><n-icon :component="Pencil" /> 重命名</n-button>
      <n-button v-if="!trashed" size="tiny" quaternary type="warning" @click="onSoftDelete"><n-icon :component="Trash" /> 删除</n-button>
      <n-button v-if="trashed" size="tiny" quaternary @click="onRestore"><n-icon :component="Refresh" /> 恢复</n-button>
      <n-button v-if="trashed" size="tiny" quaternary type="error" @click="onPurge"><n-icon :component="Close" /> 彻底删除</n-button>
    </div>
  </div>
</template>

<style scoped>
.file-card {
  display: grid;
  grid-template-columns: 52px 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid #eee;
  border-radius: 10px;
  background: #fff;
  transition: all .15s;
}
.file-card:hover { border-color: #18a058; box-shadow: 0 2px 12px rgba(0,0,0,.05); }
.fc-icon {
  width: 48px; height: 48px;
  display: flex; align-items: center; justify-content: center;
  background: #f0fdf4;
  border-radius: 10px;
  color: #18a058;
}
.fc-info { overflow: hidden; }
.fc-name { font-weight: 600; font-size: 14px; color: #222; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fc-meta { color: #999; font-size: 12px; margin-top: 2px; }
.fc-tags { display: flex; gap: 4px; margin-top: 4px; flex-wrap: wrap; }
.fc-actions { display: flex; gap: 4px; flex-wrap: wrap; }
</style>
