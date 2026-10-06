<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFilesStore } from '@/stores/files'
import { useUploadStore } from '@/stores/upload'
import { useMessage, NButton, NAvatar, NDropdown, NLayout, NLayoutSider, NLayoutHeader, NLayoutContent, NMenu, NTag } from 'naive-ui'
import { FolderOutline, Trash } from '@vicons/ionicons5'
import DropZone from '@/components/DropZone.vue'
import UploadQueue from '@/components/UploadQueue.vue'
import FileList from '@/components/FileList.vue'
import SearchBar from '@/components/SearchBar.vue'
import PreviewDrawer from '@/components/PreviewDrawer.vue'
import { tagsApi } from '@/api/tags'
import type { Tag } from '@/types'

const auth = useAuthStore()
const files = useFilesStore()
const upload = useUploadStore()
const router = useRouter()
const message = useMessage()

const menuValue = ref<string>('files')
const searchQ = ref('')
const selectedTagId = ref<number | undefined>()
const tags = ref<Tag[]>([])

async function refreshTags() {
  const r = await tagsApi.list()
  tags.value = r.data
}

async function refreshList() {
  await files.list(searchQ.value || undefined, selectedTagId.value, 'active', files.page || 1)
}

function onTagSelect(id: number | undefined) {
  selectedTagId.value = id
  files.page = 1
  refreshList()
}

function onSearch(q: string) {
  searchQ.value = q
  files.page = 1
  refreshList()
}

onMounted(async () => {
  await refreshTags()
  await refreshList()
})
</script>

<template>
  <n-layout class="app-layout" has-sider bordered>
    <n-layout-sider bordered collapse-mode="width" :collapsed-width="56" width="220">
      <div class="logo">📚 PKB</div>
      <n-menu
        :value="menuValue"
        :options="[
          { key: 'files', label: '全部文件', icon: () => h(FolderOutline) },
          { key: 'trash', label: '回收站', icon: () => h(Trash) },
        ]"
        @update:value="(v) => { menuValue = v; if (v === 'trash') router.push('/trash'); else router.push('/') }"
      />
      <div class="tags-section">
        <div class="tags-title">标签</div>
        <div class="tags-list">
          <n-tag v-if="!selectedTagId" round type="info" size="small" style="cursor: pointer" @click="onTagSelect(undefined)">全部</n-tag>
          <n-tag
            v-for="t in tags" :key="t.id" round size="small"
            :type="selectedTagId === t.id ? 'primary' : 'default'"
            style="cursor: pointer"
            @click="onTagSelect(selectedTagId === t.id ? undefined : t.id)"
          >{{ t.name }}</n-tag>
        </div>
      </div>
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered class="top-bar">
        <div class="top-left">
          <SearchBar :q="searchQ" @search="onSearch" @clear="onSearch('')" />
        </div>
        <div class="top-right">
          <n-dropdown
            trigger="click"
            :options="[{ key: 'logout', label: '退出登录' }]"
            @select="(k) => { if (k === 'logout') { auth.logout(); router.push('/login') } }"
          >
            <n-button quaternary :show-icon="false">
              <n-avatar size="small">{{ auth.user?.username?.[0]?.toUpperCase() || 'U' }}</n-avatar>
              <span style="margin-left:8px">{{ auth.user?.username }}</span>
            </n-button>
          </n-dropdown>
        </div>
      </n-layout-header>

      <n-layout-content class="main-content">
        <DropZone @files="(fs) => fs.forEach(f => upload.enqueue(f))" />
        <UploadQueue v-if="upload.queue.length" />
        <FileList :items="files.items" :loading="files.loading" :total="files.total" :page="files.page" :page-size="files.pageSize" @refresh="refreshList" />
      </n-layout-content>
    </n-layout>

    <PreviewDrawer />
  </n-layout>
</template>

<style scoped>
.app-layout { height: 100vh; }
.logo {
  height: 56px; display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 700; color: #18a058; border-bottom: 1px solid #eee;
}
.tags-section { padding: 12px 16px; }
.tags-title { font-size: 12px; color: #888; margin-bottom: 8px; }
.tags-list { display: flex; flex-wrap: wrap; gap: 6px; }
.top-bar { display: flex; align-items: center; justify-content: space-between; padding: 0 24px; height: 60px; }
.top-left { width: 420px; }
.main-content { padding: 20px; overflow: auto; }
</style>
