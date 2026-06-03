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
const form = reactive({ email: '', password: '' })
const loading = ref(false)

const rules: FormRules = {
  email: [
    { required: true, message: '請輸入電子信箱', trigger: 'blur' },
    { type: 'email', message: '請輸入有效的電子信箱', trigger: 'blur' },
  ],
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
    <section class="auth-visual">
      <p class="eyebrow">Graduation Radar</p>
      <h2>把畢業進度變成一眼看懂的路線圖</h2>
      <div class="visual-grid">
        <div class="metric-card primary">
          <span>總學分進度</span>
          <strong>87%</strong>
        </div>
        <div class="metric-card">
          <span>缺修提醒</span>
          <strong>4</strong>
        </div>
        <div class="metric-card">
          <span>通識完成</span>
          <strong>23/28</strong>
        </div>
      </div>
    </section>

    <el-card class="auth-card" shadow="always">
      <div class="auth-header">
        <h1 class="title">學生畢業學分審核器</h1>
        <p class="subtitle">請登入以檢視你的畢業進度</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="onSubmit"
      >
        <el-form-item label="電子信箱" prop="email">
          <el-input v-model="form.email" :prefix-icon="User" placeholder="例如 112703043@example.com" />
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
  display: grid;
  grid-template-columns: minmax(280px, 520px) minmax(360px, 420px);
  align-items: center;
  justify-content: center;
  gap: clamp(28px, 6vw, 86px);
  background: var(--app-bg-gradient);
  padding: 32px;
}

.auth-visual {
  color: var(--app-text-strong);
}

.eyebrow {
  margin: 0 0 12px;
  color: var(--app-primary);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.auth-visual h2 {
  margin: 0;
  max-width: 520px;
  font-size: clamp(34px, 5vw, 58px);
  line-height: 1.08;
  font-weight: 900;
}

.visual-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 12px;
  margin-top: 28px;
  max-width: 470px;
}

.metric-card {
  min-height: 112px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 18px;
  border: 1px solid color-mix(in srgb, var(--app-border) 80%, transparent);
  border-radius: 8px;
  background: var(--app-surface-glass);
  box-shadow: var(--app-shadow-soft);
  backdrop-filter: blur(16px);
}

.metric-card.primary {
  grid-row: span 2;
  min-height: 236px;
  color: #fff;
  background:
    linear-gradient(145deg, var(--app-primary), var(--app-accent));
  box-shadow: 0 24px 56px color-mix(in srgb, var(--app-primary) 26%, transparent);
}

.metric-card span {
  color: inherit;
  opacity: 0.72;
  font-size: 13px;
  font-weight: 700;
}

.metric-card strong {
  font-size: 38px;
  line-height: 1;
  font-weight: 900;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  border-radius: 8px;
  padding: 6px;
}

.auth-header {
  text-align: center;
  margin-bottom: 24px;
}

.title {
  font-size: 22px;
  margin: 0 0 8px;
  color: var(--app-text-strong);
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

@media (max-width: 900px) {
  .auth-page {
    grid-template-columns: 1fr;
  }

  .auth-visual {
    display: none;
  }
}
</style>
