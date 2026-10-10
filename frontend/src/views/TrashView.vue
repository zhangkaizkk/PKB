<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDialog, useMessage, NButton } from 'naive-ui'
import { filesApi } from '@/api/files'
import { useFilesStore } from '@/stores/files'
import FileList from '@/components/FileList.vue'

const files = useFilesStore()
const dialog = useDialog()
const message = useMessage()
const purging = ref(false)

onMounted(() => {
  if (files.items.length === 0) {
    files.list(undefined, undefined, 'trashed', 1)
  }
})

async function handlePurgeAll() {
  if (files.total === 0) {
    message.info('回收站已经是空的了')
    return
  }

  dialog.warning({
    title: '确认清空回收站',
    content: `即将彻底删除回收站中的全部 ${files.total} 个文件，此操作不可恢复！`,
    positiveText: '全部删除',
    negativeText: '取消',
    positiveButtonProps: { type: 'error' },
    async onPositiveClick() {
      purging.value = true
      try {
        const res = await filesApi.purgeAll()
        message.success(`已彻底删除 ${res.data.purged_count} 个文件`)
        await files.list(undefined, undefined, 'trashed', 1)
      } catch (e: any) {
        message.error(e?.response?.data?.detail ?? '清空失败')
      } finally {
        purging.value = false
      }
    },
  })
}
</script>

<template>
  <div class="trash-wrap">
    <div class="trash-header">
      <h2>🗑 回收站（彻底删除不可恢复）</h2>
      <NButton
        type="error"
        ghost
        :disabled="files.total === 0"
        :loading="purging"
        @click="handlePurgeAll"
      >
        全部删除
      </NButton>
    </div>
    <FileList
      :items="files.items"
      :loading="files.loading"
      :total="files.total"
      :page="files.page"
      :page-size="files.pageSize"
      :trashed="true"
      @refresh="() => files.list(undefined, undefined, 'trashed', files.page)"
      @page-change="(p: number) => files.list(undefined, undefined, 'trashed', p)"
      @page-size-change="(s: number) => files.list(undefined, undefined, 'trashed', 1, s)"
    />
  </div>
</template>

<style scoped>
.trash-wrap {
  padding: 8px;
  height: 100%;
  overflow: auto;
}
.trash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.trash-header h2 {
  margin: 0;
  font-size: 18px;
}
</style>
