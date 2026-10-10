<script setup lang="ts">
import { ref, watch } from 'vue'
import { NInput } from 'naive-ui'
import { Search as SearchIcon } from '@vicons/ionicons5'

const props = defineProps<{ q: string }>()
const emit = defineEmits<{ search: [q: string]; clear: [] }>()

const local = ref(props.q)
watch(
  () => props.q,
  (v) => {
    local.value = v
  },
)

function onEnter() {
  emit('search', local.value.trim())
}
function onClear() {
  emit('clear')
  local.value = ''
}
</script>

<template>
  <n-input
    v-model:value="local"
    placeholder="搜索文件名 / 标题 / 内容"
    clearable
    @keyup.enter="onEnter"
    @clear="onClear"
  >
    <template #prefix>
      <n-icon :component="SearchIcon" />
    </template>
  </n-input>
</template>
