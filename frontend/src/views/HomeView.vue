<script setup lang="ts">
import { onMounted } from 'vue'
import { useFilesStore } from '@/stores/files'
import FileList from '@/components/FileList.vue'

const files = useFilesStore()

onMounted(() => {
  // 如果 Layout 父组件已经刷新过就不再刷
  if (files.items.length === 0) {
    files.list(undefined, undefined, 'active', 1)
  }
})
</script>

<template>
  <FileList
    :items="files.items"
    :loading="files.loading"
    :total="files.total"
    :page="files.page"
    :page-size="files.pageSize"
    @refresh="() => files.list(undefined, undefined, 'active', files.page)"
  />
</template>
