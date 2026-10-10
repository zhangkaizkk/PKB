import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import pluginTs from '@typescript-eslint/eslint-plugin'
import parserTs from '@typescript-eslint/parser'
import vueParser from 'vue-eslint-parser'
import prettier from 'eslint-config-prettier'

export default [
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    files: ['**/*.{ts,vue}'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: parserTs,
        ecmaVersion: 'latest',
        sourceType: 'module',
        extraFileExtensions: ['.vue'],
      },
      globals: {
        // Browser globals that TS/Vue code commonly uses
        FormData: 'readonly',
        Blob: 'readonly',
        URL: 'readonly',
        URLSearchParams: 'readonly',
        document: 'readonly',
        window: 'readonly',
        location: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        console: 'readonly',
      },
    },
    plugins: {
      '@typescript-eslint': pluginTs,
    },
    rules: {
      ...pluginTs.configs.recommended.rules,
      'vue/multi-word-component-names': 'off',
      'vue/no-v-html': 'off',
      // TS 已覆盖 no-undef，关掉 ESLint 原生版本（避免 Vue 模板里误报）
      'no-undef': 'off',
      // 现有代码还没全面类型化，暂时关闭
      '@typescript-eslint/no-explicit-any': 'off',
      // Vue 模板里的变量 ESLint 误判为未使用，关掉
      '@typescript-eslint/no-unused-vars': 'off',
    },
  },
  prettier,
  {
    ignores: ['dist/', 'node_modules/', '*.config.js', 'package-lock.json'],
  },
]
