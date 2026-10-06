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
      <h1>PKB 个人知识库</h1>
      <n-form label-placement="top" @submit.prevent="submit">
        <n-form-item label="用户名">
          <n-input v-model:value="form.username" placeholder="admin" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" show-password-on="click" placeholder="admin123" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="submit">登录</n-button>
      </n-form>
      <p class="tip">默认 admin / admin123</p>
    </div>
  </div>
</template>

<style scoped>
.login-wrap { display: flex; align-items: center; justify-content: center; height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.login-card { width: 380px; padding: 36px 32px; background: #fff; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,.25); }
.login-card h1 { margin: 0 0 24px; text-align: center; font-size: 22px; color: #333; }
.tip { margin: 14px 0 0; text-align: center; color: #999; font-size: 12px; }
</style>
