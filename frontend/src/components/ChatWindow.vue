<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { NInput, NButton, NSpin, NEmpty, NTag } from 'naive-ui'
import ChatMessage from './ChatMessage.vue'
import { Send } from '@vicons/ionicons5'
import { ragApi } from '@/api/rag'
import type { Citation, RagAskResponse } from '@/types'

interface ChatMessageData {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  model?: string | null
  error?: boolean
}

const props = defineProps<{
  localOnly?: boolean
}>()

const messages = ref<ChatMessageData[]>([])
const input = ref('')
const loading = ref(false)
const scrollRef = ref<HTMLElement | null>(null)

async function send() {
  const q = input.value.trim()
  if (!q || loading.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: q })
  input.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const res = await ragApi.ask({ question: q, local_only: props.localOnly })
    messages.value.push({
      role: 'assistant',
      content: res.data.answer,
      citations: res.data.citations,
      model: res.data.chat_model || res.data.embed_model,
    })
  } catch (err: any) {
    messages.value.push({
      role: 'assistant',
      content: `请求失败: ${err?.response?.data?.detail || err?.message || '未知错误'}`,
      error: true,
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  })
}

function clearChat() {
  messages.value = []
}

watch(messages, scrollToBottom, { deep: true })
</script>

<template>
  <div class="chat-window">
    <div ref="scrollRef" class="cw-messages">
      <div v-if="messages.length === 0" class="cw-empty">
        <n-empty description="在下方输入问题，开始与知识库对话">
          <template #extra>
            <div class="cw-suggestions">
              <n-tag
                round
                type="info"
                size="small"
                class="suggestion"
                @click="input = '我上传了哪些文档？'"
              >
                我上传了哪些文档？
              </n-tag>
              <n-tag
                round
                type="info"
                size="small"
                class="suggestion"
                @click="input = '最近的文件是什么？'"
              >
                最近的文件是什么？
              </n-tag>
            </div>
          </template>
        </n-empty>
      </div>
      <ChatMessage v-for="(msg, i) in messages" :key="i" :message="msg" />
      <div v-if="loading" class="cw-loading">
        <n-spin size="small" /> <span style="margin-left: 8px">思考中...</span>
      </div>
    </div>

    <div class="cw-input">
      <n-input
        v-model:value="input"
        type="textarea"
        placeholder="输入问题，按 Enter 发送，Shift+Enter 换行"
        :autosize="{ minRows: 1, maxRows: 4 }"
        :disabled="loading"
        @keydown.enter.prevent.exact="send"
      />
      <div class="cw-actions">
        <n-button size="small" quaternary :disabled="messages.length === 0" @click="clearChat">
          清空对话
        </n-button>
        <n-button type="primary" size="small" :disabled="loading || !input.trim()" @click="send">
          <template #icon
            ><n-icon><Send /></n-icon
          ></template>
          发送
        </n-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--cyb-bg-0);
}
.cw-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.cw-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}
.cw-suggestions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 12px;
}
.suggestion {
  cursor: pointer;
  background: var(--cyb-bg-2) !important;
  border: 1px solid var(--cyb-border) !important;
  color: var(--cyb-text-dim) !important;
  font-family: var(--cyb-mono);
  font-size: 12px;
  transition:
    border-color var(--cyb-transition),
    color var(--cyb-transition);
}
.suggestion:hover {
  border-color: var(--cyb-neon) !important;
  color: var(--cyb-neon) !important;
}
.cw-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--cyb-text-faint);
  margin: 20px 0;
  font-size: 13px;
  font-family: var(--cyb-mono);
}
.cw-input {
  border-top: 1px solid var(--cyb-border);
  padding: 16px 20px;
  background: var(--cyb-bg-1);
}
.cw-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}
.cw-actions :deep(.n-button--quaternary) {
  color: var(--cyb-text-dim) !important;
  border-radius: var(--cyb-radius-sm) !important;
}
.cw-actions :deep(.n-button--quaternary:hover) {
  color: var(--cyb-text) !important;
  background: var(--cyb-bg-3) !important;
}
</style>
