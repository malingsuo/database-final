<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref<FormInstance>()
const form = reactive({ account: '', password: '' })
const loading = ref(false)

const rules: FormRules = {
  account: [{ required: true, message: '請輸入帳號（學號）', trigger: 'blur' }],
  password: [{ required: true, message: '請輸入密碼', trigger: 'blur' }],
}

async function onSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await auth.login({ ...form })
    if (res.role === 'admin') {
      ElMessage.success('管理員登入成功')
      router.replace((route.query.redirect as string) || '/admin/dashboard')
      return
    }
    const redirect = (route.query.redirect as string) || '/overview'
    router.replace(redirect)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '登入失敗')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="always">
      <div class="auth-header">
        <h1 class="title">學生畢業學分審核器</h1>
        <p class="subtitle">請登入以查看你的畢業進度</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="onSubmit"
      >
        <el-form-item label="帳號（學號）" prop="account">
          <el-input v-model="form.account" :prefix-icon="User" placeholder="例如 112703043" />
        </el-form-item>
        <el-form-item label="密碼" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            :prefix-icon="Lock"
            show-password
            placeholder="請輸入密碼"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="submit-btn" :loading="loading" @click="onSubmit">
            登入
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        還沒有帳號？
        <router-link :to="{ name: 'register' }">前往註冊</router-link>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e0eafc 0%, #f5f7fa 100%);
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  border-radius: 12px;
}

.auth-header {
  text-align: center;
  margin-bottom: 24px;
}

.title {
  font-size: 22px;
  margin: 0 0 8px;
  color: var(--el-color-primary);
}

.subtitle {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.submit-btn {
  width: 100%;
}

.auth-footer {
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}
</style>
