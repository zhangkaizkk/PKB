<script setup lang="ts">
import { computed, ref, onMounted, h, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFilesStore } from '@/stores/files'
import { useUploadStore } from '@/stores/upload'
import { useMessage, NButton, NInput, NAvatar, NDropdown, NLayout, NLayoutSider, NLayoutHeader, NLayoutContent, NMenu, NTag } from 'naive-ui'
import { FolderOutline, Trash, ChatbubbleEllipsesOutline } from '@vicons/ionicons5'
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
const menuValue = computed(() => {
  if (route.name === 'chat') return 'chat'
  if (route.name === 'trash') return 'trash'
  return 'files'
})

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
  else if (key === 'chat') router.push('/chat')
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
      <div class="logo"><span class="logo-tag">PKB</span><span class="logo-sub">_</span></div>
      <n-menu
        :value="menuValue"
        :options="[
          { key: 'files', label: '全部文件', icon: () => h(FolderOutline) },
          { key: 'chat', label: '知识库问答', icon: () => h(ChatbubbleEllipsesOutline) },
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
              <n-avatar class="pkb-admin-avatar" size="small">
                {{ auth.user?.username?.[0]?.toUpperCase() || 'U' }}
              </n-avatar>
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
  height: 64px; display: flex; align-items: center; justify-content: center; gap: 4px;
  font-family: var(--cyb-mono); font-size: 18px; font-weight: 700;
  border-bottom: 1px solid var(--cyb-border);
  letter-spacing: 2px;
}
.logo-tag { color: var(--cyb-neon); text-shadow: var(--cyb-neon-glow); }
.logo-sub {
  color: var(--cyb-neon); animation: blink 1s step-end infinite;
}
@keyframes blink { 50% { opacity: 0; } }

.tags-section { padding: 12px 16px; }
.tags-title { font-size: 12px; color: var(--cyb-text-faint); margin-bottom: 8px; font-family: var(--cyb-mono); }
.tags-list { display: flex; flex-wrap: wrap; gap: 6px; }

.top-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; height: 56px;
}
.top-left { display: flex; align-items: center; gap: 8px; }
.top-right { display: flex; align-items: center; }

.main-content {
  padding: 24px; overflow: auto;
  background: var(--cyb-bg-0);
}

/* 搜索框前缀 emoji 替换 */
.top-left :deep(.n-input__prefix) { font-size: 14px; opacity: 0.7; }

.pkb-admin-avatar {
  background: var(--cyb-neon) !important;
  color: var(--cyb-bg-0) !important;
  font-family: var(--cyb-mono) !important;
  font-weight: 700 !important;
  box-shadow: var(--cyb-neon-glow) !important;
}

/* 用户名下拉按钮 */
.top-right :deep(.n-button--quaternary) {
  color: var(--cyb-text-dim) !important;
  border-radius: var(--cyb-radius-sm) !important;
}
.top-right :deep(.n-button--quaternary:hover) {
  color: var(--cyb-neon) !important;
  background: var(--cyb-neon-dim) !important;
}
</style>
