<script setup lang="ts">
import { computed } from 'vue'
import CitationCard from './CitationCard.vue'
import type { Citation } from '@/types'

interface ChatMessageData {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  model?: string | null
  error?: boolean
}

const props = defineProps<{ message: ChatMessageData }>()

const isUser = computed(() => props.message.role === 'user')
const hasCitations = computed(() => props.message.citations && props.message.citations.length > 0)
</script>

<template>
  <div class="chat-message" :class="{ 'is-user': isUser, 'is-assistant': !isUser }">
    <div class="cm-avatar">
      {{ isUser ? 'USER' : 'AI' }}
    </div>
    <div class="cm-body">
      <div class="cm-bubble" :class="{ 'error-bubble': message.error }">
        {{ message.content }}
      </div>
      <div v-if="!isUser && message.model" class="cm-meta">
        模型: {{ message.model }}
      </div>
      <div v-if="!isUser && hasCitations" class="cm-citations">
        <CitationCard
          v-for="(c, i) in message.citations"
          :key="i"
          :citation="c"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-message { display: flex; gap: 12px; margin-bottom: 20px; }
.chat-message.is-user { flex-direction: row-reverse; }
.cm-avatar {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: var(--cyb-bg-2);
  border: 1px solid var(--cyb-border);
  border-radius: var(--cyb-radius-sm);
  font-family: var(--cyb-mono); font-size: 14px; font-weight: 700;
  flex-shrink: 0;
}
.chat-message.is-assistant .cm-avatar {
  color: var(--cyb-accent);
  border-color: var(--cyb-accent-dim);
  background: var(--cyb-accent-dim);
}
.chat-message.is-user .cm-avatar {
  color: var(--cyb-neon);
  border-color: var(--cyb-neon-dim);
  background: var(--cyb-neon-dim);
}
.cm-body { max-width: 70%; }
.chat-message.is-user .cm-body {
  display: flex; flex-direction: column; align-items: flex-end;
}
.cm-bubble {
  background: var(--cyb-bg-2);
  border: 1px solid var(--cyb-border);
  border-radius: var(--cyb-radius);
  padding: 12px 16px;
  font-size: 14px; line-height: 1.7;
  white-space: pre-wrap; word-break: break-word;
  color: var(--cyb-text);
}
.chat-message.is-user .cm-bubble {
  background: var(--cyb-neon-dim);
  border-color: var(--cyb-neon);
  color: var(--cyb-bg-0);
}
.chat-message.is-assistant .cm-bubble {
  border-left: 2px solid var(--cyb-accent);
}
.cm-bubble.error-bubble {
  background: rgba(244, 114, 182, 0.1);
  border-color: var(--cyb-danger);
  color: var(--cyb-danger);
  border-left: 2px solid var(--cyb-danger);
}
.cm-meta {
  font-size: 11px; color: var(--cyb-text-faint); margin-top: 4px;
  font-family: var(--cyb-mono);
}
.cm-citations { margin-top: 8px; }
</style>
