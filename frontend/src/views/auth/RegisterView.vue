<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref<FormInstance>()
const form = reactive({ account: '', password: '', confirm: '' })
const loading = ref(false)

const validateAccount = (_r: unknown, value: string, cb: (e?: Error) => void) => {
  if (!value) return cb(new Error('請輸入學號'))
  if (!/^112\d+$/.test(value)) return cb(new Error('目前僅開放 112 學年度入學（學號需以 112 開頭）'))
  cb()
}

const validateConfirm = (_r: unknown, value: string, cb: (e?: Error) => void) => {
  if (value !== form.password) return cb(new Error('兩次輸入的密碼不一致'))
  cb()
}

const rules: FormRules = {
  account: [{ validator: validateAccount, trigger: 'blur' }],
  password: [
    { required: true, message: '請輸入密碼', trigger: 'blur' },
    { min: 8, message: '密碼至少需 8 碼', trigger: 'blur' },
  ],
  confirm: [{ validator: validateConfirm, trigger: 'blur' }],
}

async function onSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await auth.register({ account: form.account, password: form.password, role: 'student' })
    ElMessage.success('註冊成功，請登入')
    router.replace({ name: 'login' })
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '註冊失敗')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="always">
      <div class="auth-header">
        <h1 class="title">學生註冊</h1>
        <p class="subtitle">使用學號建立帳號，查詢畢業學分進度</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="onSubmit"
      >
        <el-form-item label="學號" prop="account">
          <el-input v-model="form.account" :prefix-icon="User" placeholder="例如 112703043" />
        </el-form-item>
        <el-form-item label="密碼" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            :prefix-icon="Lock"
            show-password
            placeholder="至少 8 碼"
          />
        </el-form-item>
        <el-form-item label="確認密碼" prop="confirm">
          <el-input
            v-model="form.confirm"
            type="password"
            :prefix-icon="Lock"
            show-password
            placeholder="再次輸入密碼"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="submit-btn" :loading="loading" @click="onSubmit">
            註冊
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        已經有帳號？
        <router-link :to="{ name: 'login' }">前往登入</router-link>
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
