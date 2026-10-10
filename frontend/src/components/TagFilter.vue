<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NTag } from 'naive-ui'
import { tagsApi } from '@/api/tags'
import type { Tag } from '@/types'

const emit = defineEmits<{ select: [id: number | undefined] }>()

const tags = ref<Tag[]>([])
const selected = ref<number | undefined>()

onMounted(async () => {
  const r = await tagsApi.list()
  tags.value = r.data
})
</script>

<template>
  <div class="tag-filter">
    <span class="label">筛选：</span>
    <n-tag
      round
      :type="selected === undefined ? 'info' : 'default'"
      size="small"
      style="cursor: pointer"
      @click="
        selected = undefined
        emit('select', undefined)
      "
      >全部</n-tag
    >
    <n-tag
      v-for="t in tags"
      :key="t.id"
      round
      :type="selected === t.id ? 'primary' : 'default'"
      size="small"
      style="cursor: pointer"
      @click="
        selected = selected === t.id ? undefined : t.id
        emit('select', selected)
      "
    >
      {{ t.name }}
    </n-tag>
  </div>
</template>

<style scoped>
.tag-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.label {
  color: #888;
  font-size: 12px;
}
</style>
