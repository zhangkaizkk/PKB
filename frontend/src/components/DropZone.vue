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
      <div class="dz-icon">📤</div>
      <div class="dz-text">拖拽文件到这里，或 <b>点击选择文件</b></div>
      <div class="dz-hint">支持多文件，单个最大 2GB</div>
    </div>
  </div>
</template>

<style scoped>
.drop-zone {
  border: 2px dashed #ccc;
  border-radius: 12px;
  padding: 28px 16px;
  text-align: center;
  background: #fafafa;
  transition: all .2s;
  margin-bottom: 16px;
}
.drop-zone.active {
  border-color: #18a058;
  background: #e8f7ee;
}
.dz-inner { cursor: pointer; }
.dz-icon { font-size: 36px; margin-bottom: 8px; }
.dz-text { color: #333; font-size: 14px; }
.dz-text b { color: #18a058; }
.dz-hint { color: #999; font-size: 12px; margin-top: 4px; }
</style>
