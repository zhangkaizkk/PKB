<script setup lang="ts">
import { computed, ref, onMounted, h, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFilesStore } from '@/stores/files'
import { useUploadStore } from '@/stores/upload'
import { useMessage, NButton, NInput, NAvatar, NDropdown, NLayout, NLayoutSider, NLayoutHeader, NLayoutContent, NMenu, NTag } from 'naive-ui'
import { FolderOutline, Trash } from '@vicons/ionicons5'
import DropZone from '@/components/DropZone.vue'
import UploadQueue from '@/components/UploadQueue.vue'
import FileList from '@/components/FileList.vue'
import PreviewDrawer from '@/components/PreviewDrawer.vue'
import { tagsApi } from '@/api/tags'
import type { Tag } from '@/types'

const auth = useAuthStore()
const files = useFilesStore()
const upload = useUploadStore()
const router = useRouter()
const route = useRoute()
const message = useMessage()

const tags = ref<Tag[]>([])
const selectedTagId = ref<number | undefined>()
const searchQ = ref('')

// 根据当前路由高亮对应菜单项
const menuValue = computed(() => (route.name === 'trash' ? 'trash' : 'files'))

async function refreshTags() {
  const r = await tagsApi.list()
  tags.value = r.data
}

async function refreshList() {
  const status = route.name === 'trash' ? 'trashed' : 'active'
  await files.list(searchQ.value || undefined, selectedTagId.value, status, 1)
}

function onTagSelect(id: number | undefined) {
  selectedTagId.value = id
  refreshList()
}

function onSearch(q: string) {
  searchQ.value = q
  refreshList()
}

// 点击左侧菜单 → 切换路由
function onMenuSelect(key: string) {
  if (key === menuValue.value) return
  if (key === 'trash') router.push('/trash')
  else router.push('/')
}

// 路由变化时刷新列表（比如从 Home 点"回收站"切到 /trash）
watch(
  () => route.name,
  () => {
    selectedTagId.value = undefined
    searchQ.value = ''
    refreshList()
  },
)

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
        @update:value="onMenuSelect"
      />
      <div v-if="menuValue === 'files'" class="tags-section">
        <div class="tags-list">
          <n-tag v-if="!selectedTagId" round type="info" size="small" style="cursor: pointer" @click="onTagSelect(undefined)">全部</n-tag>
        </div>
      </div>
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered class="top-bar">
        <div class="top-left">
          <n-input
            v-model:value="searchQ"
            placeholder="搜索文件名 / 标题 / 内容"
            clearable
            size="large"
            style="width: 400px"
            @keyup.enter="onSearch(searchQ)"
            @update:value="(v: string) => { if (!v) onSearch('') }"
          >
            <template #prefix>🔍</template>
          </n-input>
          <n-button size="large" type="primary" style="margin-left: 8px" @click="onSearch(searchQ)">搜索</n-button>
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
        <!-- 全部文件：显示拖拽区 + 上传队列 -->
        <template v-if="menuValue === 'files'">
          <DropZone @files="(fs) => fs.forEach(f => upload.enqueue(f))" />
          <UploadQueue v-if="upload.queue.length" />
        </template>

        <!-- 子路由渲染出口 -->
        <router-view
          v-slot="{ Component }"
        >
          <component :is="Component" :trashed="menuValue === 'trash'" />
        </router-view>
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
