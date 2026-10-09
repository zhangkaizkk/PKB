<script setup lang="ts">
import { computed } from 'vue'
import { NDrawer, NDrawerContent, NScrollbar } from 'naive-ui'
import { useFilesStore } from '@/stores/files'

const files = useFilesStore()
const item = computed(() => files.currentPreview)

// 必须用可写 computed：v-model:show 需要能写入 false，才能触发 closePreview
const visible = computed({
  get: () => !!files.currentPreview,
  set: (v: boolean) => { if (!v) files.closePreview() },
})
</script>

<template>
  <n-drawer v-model:show="visible" :width="640" placement="right">
    <n-drawer-content :title="item?.title || '预览'" closable>
      <template v-if="item">
        <div class="meta">
          <div><b>文件名：</b>{{ item.original_name }}</div>
          <div><b>类型：</b>{{ item.mime_type }}</div>
          <div><b>大小：</b>{{ (item.size_bytes / 1024 / 1024).toFixed(2) }} MB</div>
          <div><b>上传时间：</b>{{ new Date(item.created_at).toLocaleString() }}</div>
        </div>
        <n-scrollbar class="preview-area">
          <!-- TXT / MD 文本预览 — 内容从 store 异步加载 -->
          <div
            v-if="item.mime_type.startsWith('text/') || item.original_name.endsWith('.md')"
          >
            <div v-if="files.previewLoading" class="loading">加载中...</div>
            <div v-else-if="files.previewError" class="error">{{ files.previewError }}</div>
            <pre v-else class="text-preview">{{ files.previewContent || '（文件为空）' }}</pre>
          </div>
          <!-- 图片 / PDF 内嵌 -->
          <img v-else-if="item.mime_type.startsWith('image/')" :src="item.preview_url" class="img-preview" />
          <iframe v-else-if="item.mime_type === 'application/pdf'" :src="item.preview_url" class="pdf-preview" />
          <div v-else class="unsupported">
            该格式暂不支持在线预览，请 <a :href="item.download_url" target="_blank">下载后查看</a>
          </div>
        </n-scrollbar>
      </template>
    </n-drawer-content>
  </n-drawer>
</template>

<style scoped>
.meta {
  background: #fafafa; padding: 12px 16px; border-radius: 8px;
  font-size: 13px; color: #555; line-height: 1.9; margin-bottom: 12px;
}
.preview-area { height: calc(100vh - 260px); }
.text-preview {
  padding: 16px; white-space: pre-wrap; word-break: break-word;
  background: #fff; border: 1px solid #eee; border-radius: 8px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px;
  margin: 0;
}
.img-preview { max-width: 100%; border-radius: 8px; }
.pdf-preview { width: 100%; height: calc(100vh - 260px); border: 1px solid #eee; border-radius: 8px; }
.unsupported { padding: 40px; text-align: center; color: #999; }
.loading, .error {
  padding: 40px; text-align: center; font-size: 14px;
}
.loading { color: #888; }
.error { color: #c62828; }
</style>
