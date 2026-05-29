<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({
  email: 'admin@example.com',
  password: '12345678',
})

const rules: FormRules = {
  email: [
    { required: true, message: '請輸入管理員電子信箱', trigger: 'blur' },
    { type: 'email', message: '請輸入有效的電子信箱', trigger: 'blur' },
  ],
  password: [{ required: true, message: '請輸入密碼', trigger: 'blur' }],
}

async function handleLogin() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await auth.login({ ...form })
    if (res.role !== 'admin') {
      await auth.logout()
      ElMessage.error('此入口僅限管理員使用')
      return
    }
    ElMessage.success('管理員登入成功')
    router.replace((route.query.redirect as string) || '/admin/dashboard')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '登入失敗')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="admin-login">
    <section class="login-panel">
      <div class="brand-block">
        <div class="brand-mark">A</div>
        <div>
          <h1>管理員入口</h1>
          <p>畢業學分檢核系統</p>
        </div>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="電子信箱" prop="email">
          <el-input v-model="form.email" :prefix-icon="User" placeholder="admin@example.com" />
        </el-form-item>
        <el-form-item label="密碼" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            :prefix-icon="Lock"
            show-password
            placeholder="至少 8 碼"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button type="primary" class="login-button" :loading="loading" @click="handleLogin">
          進入管理介面
        </el-button>
      </el-form>

      <div class="login-links">
        <router-link :to="{ name: 'register' }">註冊管理員帳號</router-link>
        <router-link :to="{ name: 'login' }">學生登入</router-link>
      </div>
    </section>
  </div>
</template>

<style scoped>
.admin-login {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    linear-gradient(135deg, rgba(31, 41, 55, 0.92), rgba(29, 78, 216, 0.74)),
    #1f2937;
}

.login-panel {
  width: min(100%, 440px);
  padding: 32px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.24);
}

.brand-block {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 28px;
}

.brand-mark {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 800;
  border-radius: 8px;
  background: #1d4ed8;
}

h1 {
  margin: 0;
  font-size: 24px;
  color: #111827;
}

p {
  margin: 4px 0 0;
  color: #6b7280;
}

.login-button {
  width: 100%;
}

.login-links {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 18px;
  font-size: 14px;
}
</style>
