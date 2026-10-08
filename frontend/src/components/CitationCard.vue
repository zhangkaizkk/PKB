<script setup lang="ts">
import { NCard, NTag, NButton } from 'naive-ui'
import { DownloadOutline } from '@vicons/ionicons5'
import { h } from 'vue'
import type { Citation } from '@/types'

const props = defineProps<{ citation: Citation }>()

function scoreColor(score: number | null | undefined) {
  if (!score) return 'default'
  if (score >= 0.8) return 'success'
  if (score >= 0.5) return 'info'
  return 'warning'
}

function downloadUrl(publicId: string | null) {
  if (!publicId) return '#'
  const base = (import.meta as any).env.VITE_API_BASE_URL || '/api'
  return `${base}/files/${publicId}/download`
}
</script>

<template>
  <n-card size="small" class="citation-card" :bordered="true">
    <div class="cc-header">
      <span class="cc-title">📄 {{ citation.title || '未知文档' }}</span>
      <n-tag v-if="citation.score !== null && citation.score !== undefined" :type="scoreColor(citation.score)" size="tiny" round>
        相关度 {{ (citation.score * 100).toFixed(0) }}%
      </n-tag>
    </div>
    <div v-if="citation.chunk_index !== null && citation.chunk_index !== undefined" class="cc-chunk">
      分块 #{{ citation.chunk_index + 1 }}
    </div>
    <div v-if="citation.snippet" class="cc-snippet">{{ citation.snippet }}</div>
    <div v-if="citation.public_id" class="cc-footer">
      <a :href="downloadUrl(citation.public_id)" target="_blank">
        <n-button size="tiny" quaternary>
          <template #icon><n-icon><DownloadOutline /></n-icon></template>
          下载文件
        </n-button>
      </a>
    </div>
  </n-card>
</template>

<style scoped>
.citation-card {
  margin-top: 8px;
}
.cc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.cc-title {
  font-weight: 600;
  font-size: 13px;
  color: #333;
}
.cc-chunk {
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
}
.cc-snippet {
  font-size: 12px;
  color: #666;
  line-height: 1.6;
  background: #f9f9f9;
  padding: 8px;
  border-radius: 6px;
  margin: 4px 0;
  max-height: 80px;
  overflow: hidden;
}
.cc-footer {
  margin-top: 4px;
}
</style>
