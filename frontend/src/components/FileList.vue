<script setup lang="ts">
import { NSpin, NPagination, NEmpty } from 'naive-ui'
import FileCard from './FileCard.vue'
import { useFilesStore } from '@/stores/files'
import type { FileItem } from '@/types'

const props = defineProps<{
  items: FileItem[]
  loading: boolean
  total: number
  page: number
  pageSize: number
  trashed?: boolean
}>()
const emit = defineEmits<{
  refresh: []
  'refresh:tags': []
  openPreview: [item: FileItem]
  pageChange: [p: number]
}>()

const files = useFilesStore()

function onPreview(item: FileItem) {
  files.openPreview(item)
  emit('openPreview', item)
}
</script>

<template>
  <div class="file-list">
    <n-spin :show="loading">
      <template v-if="items.length === 0 && !loading">
        <n-empty description="暂无文件" />
      </template>
      <div v-else class="file-items">
        <FileCard
          v-for="item in items"
          :key="item.public_id"
          :item="item"
          :trashed="trashed"
          @refresh="emit('refresh')"
          @refresh:tags="emit('refresh:tags')"
          @open-preview="onPreview"
        />
      </div>
    </n-spin>
    <div v-if="total > pageSize" class="pagination">
      <n-pagination
        :current="page"
        :page-size="pageSize"
        :item-count="total"
        show-size-picker
        :page-sizes="[10, 20, 50]"
        @update:page="(p) => emit('pageChange', p)"
        @update:page-size="() => emit('pageChange', 1)"
      />
    </div>
  </div>
</template>

<style scoped>
.file-list { margin-top: 8px; }
.file-items { display: flex; flex-direction: column; gap: 10px; }
.pagination { margin-top: 16px; display: flex; justify-content: center; }
</style>
