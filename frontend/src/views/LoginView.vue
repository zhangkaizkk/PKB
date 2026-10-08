<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { NInput, NButton, useMessage, NForm, NFormItem } from 'naive-ui'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const message = useMessage()

const form = ref({ username: 'admin', password: 'admin123' })
const loading = ref(false)

async function submit() {
  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    message.success('登录成功')
    const redirect = (route.query.redirect as string) || '/'
    router.replace(redirect)
  } catch (err: any) {
    message.error(err?.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <div class="login-card">
      <div class="login-logo">
        <span class="login-brand">PKB</span><span class="login-cursor">_</span>
      </div>
      <h1>个人知识库</h1>
      <p class="login-sub">knowledge retrieval interface</p>
      <n-form label-placement="top" @submit.prevent="submit">
        <n-form-item label="用户名">
          <n-input v-model:value="form.username" placeholder="admin" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" show-password-on="click" placeholder="admin123" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="submit">
          <span class="btn-label">登录</span>
        </n-button>
      </n-form>
      <p class="tip">默认 <code>admin</code> / <code>admin123</code></p>
    </div>
  </div>
</template>

<style scoped>
.login-wrap {
  display: flex; align-items: center; justify-content: center; height: 100vh;
  background: var(--cyb-bg-0);
  /* 淡网格 */
  background-image:
    linear-gradient(var(--cyb-border) 1px, transparent 1px),
    linear-gradient(90deg, var(--cyb-border) 1px, transparent 1px);
  background-size: 32px 32px;
  background-position: -1px -1px;
}
.login-card {
  width: 380px; padding: 40px 36px 32px;
  background: var(--cyb-bg-2);
  border: 1px solid var(--cyb-border);
  border-radius: var(--cyb-radius);
}
.login-logo {
  text-align: center; margin-bottom: 8px;
  font-family: var(--cyb-mono); letter-spacing: 3px;
}
.login-brand {
  font-size: 28px; font-weight: 700; color: var(--cyb-neon);
  text-shadow: var(--cyb-neon-glow);
}
.login-cursor {
  color: var(--cyb-neon); font-size: 22px;
  animation: blink 1s step-end infinite;
}
@keyframes blink { 50% { opacity: 0; } }

.login-card h1 {
  margin: 0; text-align: center; font-size: 18px; font-weight: 500;
  color: var(--cyb-text); letter-spacing: 1px;
}
.login-sub {
  margin: 4px 0 24px; text-align: center;
  font-family: var(--cyb-mono); font-size: 11px; color: var(--cyb-text-faint);
  text-transform: lowercase; letter-spacing: 2px;
}
.btn-label { font-family: var(--cyb-mono); letter-spacing: 4px; font-weight: 600; }
.tip {
  margin: 16px 0 0; text-align: center;
  color: var(--cyb-text-faint); font-size: 11px;
  font-family: var(--cyb-mono);
}
.tip code {
  color: var(--cyb-neon); background: var(--cyb-neon-dim);
  padding: 1px 6px; border-radius: var(--cyb-radius-sm);
}

/* 表单 label */
:deep(.n-form-item-label__text) {
  color: var(--cyb-text-dim); font-family: var(--cyb-mono);
  font-size: 11px; letter-spacing: 1px; text-transform: uppercase;
}
</style>
