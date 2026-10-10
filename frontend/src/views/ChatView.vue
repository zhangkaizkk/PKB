<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { NAlert, NSpin, NButton, NTag, NCollapse, NCollapseItem, useMessage } from 'naive-ui'
import ChatWindow from '@/components/ChatWindow.vue'
import { ragApi } from '@/api/rag'
import type { RagConfigResponse, RagStatsResponse, RagIndexedDocument } from '@/types'

const message = useMessage()
const config = ref<RagConfigResponse | null>(null)
const stats = ref<RagStatsResponse | null>(null)
const indexedDocs = ref<RagIndexedDocument[]>([])
const loading = ref(true)

// 重建索引状态
const reindexing = ref(false)
const reindexProgress = ref('') // 按钮上显示的进度文本
let _pollTimer: ReturnType<typeof setInterval> | null = null

async function loadData() {
  try {
    loading.value = true
    const [configRes, statsRes, docsRes] = await Promise.all([
      ragApi.config(),
      ragApi.stats(),
      ragApi.indexedDocuments(),
    ])
    config.value = configRes.data
    stats.value = statsRes.data
    indexedDocs.value = docsRes.data.documents
  } catch (err: any) {
    message.error('加载 RAG 配置失败')
  } finally {
    loading.value = false
  }
}

async function onReindex() {
  try {
    reindexing.value = true
    reindexProgress.value = '提交中…'
    const res = await ragApi.reindexAll()
    const taskId = res.data.task_id

    // 开始轮询进度
    _pollTimer = setInterval(async () => {
      try {
        const statusRes = await ragApi.reindexStatus(taskId)
        const s = statusRes.data
        reindexProgress.value = `已处理 ${s.done}/${s.total}（${s.progress}%）`

        if (!s.running) {
          // 任务结束
          stopPolling()

          if (s.failed > 0) {
            message.warning(
              `${s.message}；前 ${Math.min(5, s.failed_details.length)} 条失败：\n` +
                s.failed_details.slice(0, 5).join('\n'),
            )
          } else {
            message.success(s.message)
          }

          reindexing.value = false
          reindexProgress.value = ''
          await loadData()
        }
      } catch (err: any) {
        // 单轮询失败不致命，等下一轮
        console.warn('reindex status poll failed:', err)
      }
    }, 1500)
  } catch (err: any) {
    message.error(err?.response?.data?.detail || '重建索引失败')
    reindexing.value = false
    reindexProgress.value = ''
  }
}

function stopPolling() {
  if (_pollTimer) {
    clearInterval(_pollTimer)
    _pollTimer = null
  }
}

function fmtTime(iso: string | null) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString()
}

function downloadUrl(publicId: string) {
  const base = (import.meta as any).env.VITE_API_BASE_URL || '/api'
  return `${base}/files/${publicId}/download`
}

onMounted(loadData)
onUnmounted(stopPolling)
</script>

<template>
  <div class="chat-view">
    <div class="cv-header">
      <div class="cv-title">
        <span class="cv-icon">💬</span>
        <span>知识库问答</span>
      </div>
      <div v-if="config" class="cv-meta">
        <n-alert
          v-if="config.local_only"
          type="warning"
          show-icon
          closable
          round
          style="margin-right: 12px"
        >
          当前为本地检索模式，未启用大模型
        </n-alert>
        <span class="meta-text"> Chat: {{ config.chat_model }} </span>
        <span class="meta-text"> Embed: {{ config.embed_model }} </span>
        <n-button
          v-if="stats && stats.unique_documents > 0"
          size="small"
          quaternary
          :loading="reindexing"
          :disabled="reindexing"
          @click="onReindex"
        >
          {{ reindexing ? reindexProgress || '重建中…' : '重建索引' }}
        </n-button>
      </div>
    </div>

    <div v-if="loading" class="cv-loading">
      <n-spin />
    </div>

    <div v-else-if="stats && stats.unique_documents === 0" class="cv-empty">
      <div class="empty-content">
        <p style="font-size: 18px; font-weight: 600; margin-bottom: 8px">还没有可检索的文档</p>
        <p style="color: #999; margin-bottom: 16px">
          请先上传文档，系统会自动索引；或点击下方按钮手动重建
        </p>
        <n-button type="primary" :loading="reindexing" :disabled="reindexing" @click="onReindex">
          {{ reindexing ? reindexProgress || '重建中…' : '手动重建索引' }}
        </n-button>
      </div>
    </div>

    <template v-else>
      <div class="cv-chat">
        <ChatWindow :local-only="config?.local_only" />
      </div>

      <!-- 已索引文档列表 -->
      <div class="cv-indexed">
        <n-collapse :default-expanded-names="['docs']" accordion>
          <n-collapse-item name="docs" class="indexed-panel">
            <template #header>
              <span class="panel-title">
                📚 已建立索引的文档
                <n-tag size="tiny" round type="info">{{ indexedDocs.length }} 篇</n-tag>
                <n-tag size="tiny" round type="success">{{ stats?.total_chunks }} 个分块</n-tag>
              </span>
            </template>
            <div v-if="indexedDocs.length === 0" class="no-docs">暂无已索引文档</div>
            <div v-else class="docs-list">
              <div v-for="doc in indexedDocs" :key="doc.public_id" class="doc-item">
                <div class="doc-info">
                  <div class="doc-title" :title="doc.original_name">{{ doc.title }}</div>
                  <div class="doc-meta">
                    分块 <n-tag size="tiny" round type="primary">{{ doc.chunk_count }}</n-tag> ·
                    索引于 {{ fmtTime(doc.indexed_at) }}
                  </div>
                </div>
                <a :href="downloadUrl(doc.public_id)" target="_blank" class="doc-download">
                  下载
                </a>
              </div>
            </div>
          </n-collapse-item>
        </n-collapse>
      </div>
    </template>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.cv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--cyb-bg-1);
  border-bottom: 1px solid var(--cyb-border);
  flex-shrink: 0;
}
.cv-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 500;
  color: var(--cyb-text);
}
.cv-icon {
  display: none;
}
.cv-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}
.meta-text {
  font-size: 11px;
  color: var(--cyb-text-faint);
  font-family: var(--cyb-mono);
  text-transform: lowercase;
  letter-spacing: 1px;
}
.meta-text::before {
  content: '> ';
  color: var(--cyb-neon);
}
.cv-loading {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}
.cv-empty {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--cyb-bg-0);
}
.empty-content {
  text-align: center;
  padding: 40px 60px;
  background: var(--cyb-bg-2);
  border: 1px dashed var(--cyb-border-strong);
  border-radius: var(--cyb-radius);
}
.empty-content p {
  color: var(--cyb-text-dim);
}
.cv-chat {
  flex: 1;
  overflow: hidden;
}
.cv-indexed {
  flex-shrink: 0;
  border-top: 1px solid var(--cyb-border);
  background: var(--cyb-bg-1);
}
.indexed-panel :deep(.n-collapse) {
  background: transparent !important;
}
.indexed-panel :deep(.n-collapse-item__header) {
  padding: 10px 20px;
  font-weight: 500;
  border-bottom: 1px solid var(--cyb-border);
  font-family: var(--cyb-mono);
  font-size: 12px;
}
.indexed-panel :deep(.n-collapse-item__content) {
  padding: 0 20px 12px;
}
.indexed-panel :deep(.n-collapse-item__content-inner) {
  background: transparent !important;
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.no-docs {
  text-align: center;
  color: var(--cyb-text-faint);
  padding: 16px;
  font-size: 13px;
}
.docs-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--cyb-bg-2);
  border: 1px solid var(--cyb-border);
  border-radius: var(--cyb-radius-sm);
  transition: border-color var(--cyb-transition);
}
.doc-item:hover {
  border-color: var(--cyb-neon);
}
.doc-info {
  overflow: hidden;
}
.doc-title {
  font-weight: 500;
  font-size: 13px;
  color: var(--cyb-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 500px;
}
.doc-meta {
  font-size: 11px;
  color: var(--cyb-text-faint);
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: var(--cyb-mono);
}
.doc-download {
  font-size: 12px;
  color: var(--cyb-neon);
  text-decoration: none;
  white-space: nowrap;
  font-family: var(--cyb-mono);
  padding: 2px 10px;
  border: 1px solid var(--cyb-neon);
  border-radius: var(--cyb-radius-sm);
  transition: all var(--cyb-transition);
}
.doc-download:hover {
  background: var(--cyb-neon);
  color: var(--cyb-bg-0);
}
</style>
