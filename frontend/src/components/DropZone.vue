<script setup lang="ts">
import { ref } from 'vue'
import { NUpload, NUploadDragger } from 'naive-ui'

const emit = defineEmits<{ files: [list: File[]] }>()

const isDragging = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

function handleFiles(fileList: FileList | null) {
  if (!fileList || fileList.length === 0) return
  emit('files', Array.from(fileList))
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  handleFiles(e.dataTransfer?.files ?? null)
}
function onDragenter() { isDragging.value = true }
function onDragleave() { isDragging.value = false }
function onClick() { inputRef.value?.click() }
</script>

<template>
  <div
    class="drop-zone"
    :class="{ active: isDragging }"
    @dragover.prevent
    @dragenter.prevent="onDragenter"
    @dragleave.prevent="onDragleave"
    @drop.prevent="onDrop"
  >
    <input ref="inputRef" type="file" multiple hidden @change="(e) => handleFiles((e.target as HTMLInputElement).files)" />
    <div class="dz-inner" @click="onClick">
      <div class="dz-icon">⇪</div>
      <div class="dz-text">
        <span class="dz-accent">拖拽文件</span> 到这里，或 <span class="dz-accent">点击选择</span>
      </div>
      <div class="dz-hint">// 支持多文件 · 单个最大 2GB</div>
    </div>
  </div>
</template>

<style scoped>
.drop-zone {
  border: 1px dashed var(--cyb-border-strong);
  border-radius: var(--cyb-radius);
  padding: 28px 16px;
  text-align: center;
  background: var(--cyb-bg-2);
  transition: border-color var(--cyb-transition), background var(--cyb-transition);
  margin-bottom: 16px;
}
.drop-zone.active {
  border-color: var(--cyb-neon);
  background: var(--cyb-neon-dim);
  box-shadow: var(--cyb-neon-glow);
}
.dz-inner { cursor: pointer; }
.dz-icon {
  font-family: var(--cyb-mono); font-size: 28px;
  color: var(--cyb-neon); margin-bottom: 8px;
}
.dz-text { color: var(--cyb-text-dim); font-size: 14px; }
.dz-accent { color: var(--cyb-neon); font-weight: 500; }
.dz-hint {
  color: var(--cyb-text-faint); font-size: 11px; margin-top: 6px;
  font-family: var(--cyb-mono); letter-spacing: 1px;
}
</style>
