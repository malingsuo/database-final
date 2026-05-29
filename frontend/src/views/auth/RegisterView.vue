<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Lock, OfficeBuilding, User, UserFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { listDepartments } from '@/api/department'
import type { Department, Role } from '@/api/types'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const departments = ref<Department[]>([])
const form = reactive({
  role: 'student' as Role,
  email: '',
  password: '',
  confirm: '',
  studentId: '',
  studentName: '',
  admissionYear: 112,
  departmentId: '',
})

onMounted(async () => {
  try {
    departments.value = await listDepartments()
  } catch {
    // fallback: keep empty list
  }
})

const isStudent = computed(() => form.role === 'student')

const validateEmail = (_r: unknown, value: string, cb: (e?: Error) => void) => {
  if (!value) return cb(new Error('請輸入電子信箱'))
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return cb(new Error('請輸入有效的電子信箱'))
  cb()
}

const validateStudentId = (_r: unknown, value: string, cb: (e?: Error) => void) => {
  if (!isStudent.value) return cb()
  if (!value) return cb(new Error('請輸入學號'))
  if (!/^\d{9}$/.test(value)) return cb(new Error('學號需為 9 碼數字'))
  cb()
}

const validateStudentName = (_r: unknown, value: string, cb: (e?: Error) => void) => {
  if (!isStudent.value) return cb()
  if (!value.trim()) return cb(new Error('請輸入學生姓名'))
  cb()
}

const validateDepartment = (_r: unknown, value: string, cb: (e?: Error) => void) => {
  if (isStudent.value) return cb()
  if (!departments.value.some((dept) => dept.id === value)) return cb(new Error('請選擇管理單位'))
  cb()
}

const validateConfirm = (_r: unknown, value: string, cb: (e?: Error) => void) => {
  if (value !== form.password) return cb(new Error('兩次輸入的密碼不一致'))
  cb()
}

const rules: FormRules = {
  role: [{ required: true, message: '請選擇身分', trigger: 'change' }],
  email: [{ validator: validateEmail, trigger: 'blur' }],
  password: [
    { required: true, message: '請輸入密碼', trigger: 'blur' },
    { min: 8, message: '密碼至少需 8 碼', trigger: 'blur' },
  ],
  confirm: [{ validator: validateConfirm, trigger: 'blur' }],
  studentId: [{ validator: validateStudentId, trigger: 'blur' }],
  studentName: [{ validator: validateStudentName, trigger: 'blur' }],
  admissionYear: [{ required: true, message: '請輸入入學年度', trigger: 'change' }],
  departmentId: [{ validator: validateDepartment, trigger: 'change' }],
}

async function onSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await auth.register({
      email: form.email,
      password: form.password,
      role: form.role,
      student: isStudent.value
        ? {
            student_id: form.studentId,
            name: form.studentName.trim(),
            admission_year: form.admissionYear,
          }
        : undefined,
      administrator: !isStudent.value ? { department_id: form.departmentId } : undefined,
    })
    ElMessage.success(isStudent.value ? '學生註冊成功，請登入' : '管理員註冊成功，請登入')
    router.replace(isStudent.value ? { name: 'login' } : { name: 'admin-login' })
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
        <h1 class="title">建立系統帳號</h1>
        <p class="subtitle">依身分填寫必要資料，建立畢業檢核系統帳號</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="onSubmit"
      >
        <el-form-item label="身分" prop="role">
          <el-segmented
            v-model="form.role"
            class="role-switch"
            :options="[
              { label: '學生', value: 'student' },
              { label: '管理員', value: 'admin' },
            ]"
          />
        </el-form-item>

        <el-form-item label="電子信箱" prop="email">
          <el-input v-model="form.email" :prefix-icon="User" placeholder="例如 user@example.com" />
        </el-form-item>

        <template v-if="isStudent">
          <el-form-item label="學號" prop="studentId">
            <el-input v-model="form.studentId" :prefix-icon="User" placeholder="例如 112703043" />
          </el-form-item>
          <el-form-item label="姓名" prop="studentName">
            <el-input v-model="form.studentName" :prefix-icon="UserFilled" placeholder="請輸入真實姓名" />
          </el-form-item>
          <el-form-item label="入學年度" prop="admissionYear">
            <el-input-number v-model="form.admissionYear" :min="109" :max="114" controls-position="right" />
          </el-form-item>
        </template>

        <template v-else>
          <el-form-item label="管理單位" prop="departmentId">
            <el-select v-model="form.departmentId" :prefix-icon="OfficeBuilding" placeholder="選擇管理單位">
              <el-option v-for="dept in departments" :key="dept.id" :label="`${dept.id} - ${dept.name}`" :value="dept.id" :disabled="!dept.id" />
            </el-select>
          </el-form-item>
        </template>

        <el-form-item label="密碼" prop="password">
          <el-input v-model="form.password" type="password" :prefix-icon="Lock" show-password placeholder="至少 8 碼" />
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
          <el-button type="primary" class="submit-btn" :loading="loading" @click="onSubmit">註冊</el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        已經有帳號？
        <router-link :to="isStudent ? { name: 'login' } : { name: 'admin-login' }">前往登入</router-link>
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
  background:
    linear-gradient(135deg, rgba(49, 130, 206, 0.12), rgba(56, 161, 105, 0.08)),
    #f6f8fb;
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 480px;
  border-radius: 8px;
}

.auth-header {
  text-align: center;
  margin-bottom: 24px;
}

.title {
  font-size: 24px;
  margin: 0 0 8px;
  color: #1f2937;
}

.subtitle {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.role-switch,
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
