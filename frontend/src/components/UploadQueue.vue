<script setup lang="ts">
import { computed } from 'vue'
import { NProgress, NButton } from 'naive-ui'
import { useUploadStore } from '@/stores/upload'

const upload = useUploadStore()

const tasks = computed(() => upload.queue.filter((t) => t.status !== 'pending'))

function fmtSize(b: number) {
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  if (b < 1024 * 1024 * 1024) return `${(b / 1024 / 1024).toFixed(1)} MB`
  return `${(b / 1024 / 1024 / 1024).toFixed(2)} GB`
}
</script>

<template>
  <div v-if="tasks.length" class="upload-queue">
    <div class="uq-header">
      <span>上传队列（{{ tasks.length }}）</span>
      <n-button quaternary size="tiny" @click="upload.removeDone">清除已完成</n-button>
    </div>
    <div v-for="t in tasks" :key="t.id" class="uq-item">
      <div class="uq-name" :title="t.name">{{ t.name }}</div>
      <div class="uq-size">{{ fmtSize(t.size) }}</div>
      <div class="uq-bar">
        <n-progress
          type="line"
          :percentage="
            t.status === 'done' || t.status === 'duplicate'
              ? 100
              : t.status === 'error'
                ? 100
                : Math.max(t.progress, 0)
          "
          :status="
            t.status === 'error'
              ? 'error'
              : t.status === 'done' || t.status === 'duplicate'
                ? 'success'
                : undefined
          "
          :show-indicator="false"
        />
      </div>
      <div class="uq-status" :class="t.status">
        {{
          t.status === 'uploading'
            ? `${t.progress}%`
            : t.status === 'done'
              ? '✓ 已上传'
              : t.status === 'duplicate'
                ? '⚠ 已存在'
                : t.status === 'error'
                  ? `✗ ${t.error || '失败'}`
                  : '等待中'
        }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-queue {
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 16px;
}
.uq-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  color: #666;
  font-size: 13px;
}
.uq-item {
  display: grid;
  grid-template-columns: 1fr 90px 160px auto;
  gap: 10px;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px dashed #f0f0f0;
  font-size: 13px;
}
.uq-item:last-child {
  border-bottom: none;
}
.uq-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.uq-size {
  color: #888;
  font-size: 12px;
  text-align: right;
}
.uq-status {
  font-size: 12px;
  min-width: 80px;
  text-align: right;
}
.uq-status.error {
  color: #d03050;
}
.uq-status.duplicate {
  color: #f0a020;
}
.uq-status.done {
  color: #18a058;
}
</style>
