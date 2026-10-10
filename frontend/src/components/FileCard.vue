<script setup lang="ts">
import { h } from 'vue'
import { NButton, NTag, NPopconfirm, NDropdown } from 'naive-ui'
import {
  Download,
  Eye,
  Pencil,
  Trash,
  Refresh,
  Close,
  Document,
  Image,
  Film,
  Code,
  DocumentText,
  FolderOutline,
} from '@vicons/ionicons5'
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
  if (mime.includes('excel') || mime.includes('spreadsheet') || mime.includes('xlsx'))
    return Document
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
  const newName = window.prompt('新名称', props.item.original_name)
  if (!newName || newName === props.item.original_name) return
  try {
    await filesApi.patch(props.item.public_id, { original_name: newName })
    message.success('重命名成功')
    emit('refresh')
  } catch (err: any) {
    message.error(err?.response?.data?.detail || '重命名失败')
  }
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
function ocrTag(item: FileItem) {
  const map: Record<
    string,
    { type: 'default' | 'success' | 'warning' | 'error' | 'info'; label: string }
  > = {
    done: { type: 'success', label: 'OCR 完成' },
    processing: { type: 'info', label: 'OCR 中' },
    failed: { type: 'error', label: 'OCR 失败' },
    pending: { type: 'warning', label: '待 OCR' },
    skipped: { type: 'default', label: '' },
  }
  return map[item.ocr_status] || map.skipped
}
</script>

<template>
  <div class="file-card">
    <div class="fc-icon">
      <n-icon :component="iconFor(item.mime_type)" :size="28" />
    </div>
    <div class="fc-info">
      <div class="fc-name" :title="item.original_name">
        {{ item.title }}
        <n-tag
          v-if="ocrTag(item).label"
          :type="ocrTag(item).type"
          size="tiny"
          round
          style="margin-left: 6px; vertical-align: middle"
          >{{ ocrTag(item).label }}</n-tag
        >
        <n-tag
          v-if="item.indexed_at"
          type="success"
          size="tiny"
          round
          style="margin-left: 4px; vertical-align: middle"
          >已索引</n-tag
        >
      </div>
      <div class="fc-meta">{{ fmtSize(item.size_bytes) }} · {{ fmtDate(item.updated_at) }}</div>
      <div v-if="item.tags.length" class="fc-tags">
        <n-tag
          v-for="t in item.tags"
          :key="t.id"
          size="tiny"
          round
          :bordered="t.color === null"
          :type="t.color ? undefined : 'default'"
          :color="(t.color as any) || undefined"
          >{{ t.name }}</n-tag
        >
      </div>
    </div>
    <div class="fc-actions">
      <n-button size="tiny" quaternary @click="onPreview"
        ><n-icon :component="Eye" /> 预览</n-button
      >
      <n-button size="tiny" quaternary @click="onDownload"
        ><n-icon :component="Download" /> 下载</n-button
      >
      <n-button v-if="!trashed" size="tiny" quaternary @click="onRename"
        ><n-icon :component="Pencil" /> 重命名</n-button
      >
      <n-button v-if="!trashed" size="tiny" quaternary type="warning" @click="onSoftDelete"
        ><n-icon :component="Trash" /> 删除</n-button
      >
      <n-button v-if="trashed" size="tiny" quaternary @click="onRestore"
        ><n-icon :component="Refresh" /> 恢复</n-button
      >
      <n-button v-if="trashed" size="tiny" quaternary type="error" @click="onPurge"
        ><n-icon :component="Close" /> 彻底删除</n-button
      >
    </div>
  </div>
</template>

<style scoped>
.file-card {
  display: grid;
  grid-template-columns: 44px 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 12px 16px;
  border: 1px solid var(--cyb-border);
  border-radius: var(--cyb-radius);
  background: var(--cyb-bg-2);
  transition:
    border-color var(--cyb-transition),
    box-shadow var(--cyb-transition);
}
.file-card:hover {
  border-color: var(--cyb-neon);
  box-shadow: 0 0 0 1px var(--cyb-neon-dim);
}
.fc-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--cyb-neon-dim);
  border-radius: var(--cyb-radius-sm);
  color: var(--cyb-neon);
}
.fc-info {
  overflow: hidden;
}
.fc-name {
  font-weight: 500;
  font-size: 14px;
  color: var(--cyb-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.fc-meta {
  color: var(--cyb-text-faint);
  font-size: 12px;
  margin-top: 2px;
  font-family: var(--cyb-mono);
}
.fc-tags {
  display: flex;
  gap: 4px;
  margin-top: 4px;
  flex-wrap: wrap;
}
.fc-actions {
  display: flex;
  gap: 2px;
  flex-wrap: wrap;
}
.fc-actions :deep(.n-button--quaternary) {
  color: var(--cyb-text-dim) !important;
  border-radius: var(--cyb-radius-sm) !important;
}
.fc-actions :deep(.n-button--quaternary:hover) {
  color: var(--cyb-neon) !important;
  background: var(--cyb-neon-dim) !important;
}
</style>
