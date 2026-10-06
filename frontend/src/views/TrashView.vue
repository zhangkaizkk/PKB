<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useFilesStore } from '@/stores/files'
import FileList from '@/components/FileList.vue'

const files = useFilesStore()

onMounted(() => {
  files.list(undefined, undefined, 'trashed', 1)
})
</script>

<template>
  <div class="trash-wrap">
    <h2>🗑 回收站（彻底删除不可恢复）</h2>
    <FileList :items="files.items" :loading="files.loading" :total="files.total" :page="files.page" :page-size="files.pageSize" :trashed="true" @refresh="() => files.list(undefined, undefined, 'trashed', files.page)" />
  </div>
</template>

<style scoped>
.trash-wrap { padding: 24px; height: 100%; overflow: auto; }
.trash-wrap h2 { margin: 0 0 20px; font-size: 20px; }
</style>
