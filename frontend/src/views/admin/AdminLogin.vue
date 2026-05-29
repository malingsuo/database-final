<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
    <!-- 背景装饰 -->
    <div class="absolute top-0 left-0 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
    <div class="absolute bottom-0 right-0 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl translate-x-1/2 translate-y-1/2"></div>

    <!-- 登入卡片 -->
    <div class="relative w-full max-w-md">
      <div
        class="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl p-8 space-y-8"
      >
        <!-- 标题与说明 -->
        <div class="text-center space-y-3">
          <div class="flex items-center justify-center space-x-2">
            <div class="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-600 rounded-lg flex items-center justify-center">
              <span class="text-white font-bold text-lg">A</span>
            </div>
            <h1 class="text-3xl font-bold text-white">管理员入口</h1>
          </div>
          <p class="text-slate-300 text-sm">学分检核系统 - 管理员专用</p>
        </div>

        <!-- 登入表单 -->
        <form @submit.prevent="handleLogin" class="space-y-5">
          <!-- 账号输入框 -->
          <div class="space-y-2">
            <label class="block text-sm font-medium text-white">
              <span class="inline-block w-5 h-5 bg-blue-500/20 rounded-full text-center text-xs text-blue-300 leading-5 mr-2">
                👤
              </span>
              账号
            </label>
            <input
              v-model="formData.account"
              type="text"
              placeholder="请输入账号"
              required
              :disabled="isLoading"
              class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 disabled:opacity-50"
            />
          </div>

          <!-- 密码输入框 -->
          <div class="space-y-2">
            <label class="block text-sm font-medium text-white">
              <span class="inline-block w-5 h-5 bg-blue-500/20 rounded-full text-center text-xs text-blue-300 leading-5 mr-2">
                🔑
              </span>
              密码
            </label>
            <input
              v-model="formData.password"
              type="password"
              placeholder="请输入密码"
              required
              :disabled="isLoading"
              class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 disabled:opacity-50"
            />
          </div>

          <!-- 错误提示 -->
          <div v-if="errorMessage" class="p-3 bg-red-500/20 border border-red-500/50 rounded-lg">
            <p class="text-red-200 text-sm">{{ errorMessage }}</p>
          </div>

          <!-- 登入按钮 -->
          <button
            type="submit"
            :disabled="isLoading"
            class="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-slate-600 disabled:to-slate-700 text-white font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 active:scale-95 disabled:cursor-not-allowed disabled:scale-100 flex items-center justify-center space-x-2"
          >
            <span v-if="!isLoading" class="text-lg">→</span>
            <span v-else class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <span>{{ isLoading ? '登入中...' : '进入管理系统' }}</span>
          </button>
        </form>

        <!-- 底部信息 -->
        <div class="pt-4 border-t border-white/10">
          <p class="text-slate-400 text-xs text-center">
            仅限授权人员使用 · 违规使用将追究责任
          </p>
        </div>
      </div>

      <!-- 卡片阴影效果 -->
      <div class="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur opacity-0 group-hover:opacity-100 transition duration-1000 -z-10"></div>
    </div>

    <!-- 右下角装饰 -->
    <div class="absolute bottom-6 right-6 text-slate-600 text-xs">
      <p>v1.0 Admin Panel</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'

// ===== 状态管理 =====
const router = useRouter()
const adminStore = useAdminStore()

const formData = ref({
  account: 'admin',
  password: '12345678',
})

const isLoading = ref(false)
const errorMessage = ref('')

// ===== 登入处理 =====
/**
 * 处理登入表单提交
 * 这里使用模拟数据，实际应连接后端API
 */
const handleLogin = async () => {
  if (!formData.value.account || !formData.value.password) {
    errorMessage.value = '请输入账号和密码'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    // 模拟网络延迟
    await new Promise((resolve) => setTimeout(resolve, 800))

    // 调用 store 中的登入方法
    const success = adminStore.adminLogin(formData.value.account, formData.value.password)

    if (success) {
      ElMessage.success('登入成功！')
      // 跳转到管理员仪表板
      router.push({ name: 'admin-dashboard' })
    } else {
      errorMessage.value = '账号或密码错误'
    }
  } catch (error) {
    errorMessage.value = '登入失败，请稍后重试'
    console.error('登入错误:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* 输入框焦点效果 */
input:focus {
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
}

/* 按钮按下效果 */
button:active {
  transform: scale(0.98);
}
</style>
