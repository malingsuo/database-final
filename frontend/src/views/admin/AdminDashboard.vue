<template>
  <div class="min-h-screen bg-slate-50">
    <!-- 顶部导航栏 -->
    <div class="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span class="text-white font-bold">A</span>
          </div>
          <h1 class="text-xl font-bold text-slate-900">学分检核系统</h1>
        </div>

        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2 px-4 py-2 bg-slate-50 rounded-lg">
            <span class="text-sm text-slate-600">{{ adminStore.admin?.name }}</span>
            <span class="text-xs text-slate-400">({{ adminStore.admin?.department }})</span>
          </div>
          <button
            @click="handleLogout"
            class="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition"
          >
            登出
          </button>
        </div>
      </div>
    </div>

    <!-- 主容器 -->
    <div class="max-w-7xl mx-auto px-6 py-8 space-y-8">
      <!-- 欢迎区块 -->
      <div class="space-y-2">
        <h2 class="text-3xl font-bold text-slate-900">欢迎回来，{{ adminStore.admin?.name }}</h2>
        <p class="text-slate-600">{{ new Date().toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }) }}</p>
      </div>

      <!-- 关键指标卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <!-- 总学生数 -->
        <div
          class="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-md transition group cursor-pointer"
          @click="navigateTo('student-list')"
        >
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm font-medium text-slate-600 mb-2">总学生数</p>
              <p class="text-4xl font-bold text-slate-900">{{ dashboardStats.total_students }}</p>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition">
              <span class="text-2xl">👥</span>
            </div>
          </div>
          <p class="text-xs text-slate-500 mt-4">点击查看详细列表</p>
        </div>

        <!-- 已达标学生 -->
        <div class="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-md transition group cursor-pointer">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm font-medium text-slate-600 mb-2">已达标</p>
              <p class="text-4xl font-bold text-green-600">{{ dashboardStats.on_track_students }}</p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center group-hover:bg-green-200 transition">
              <span class="text-2xl">✓</span>
            </div>
          </div>
          <p class="text-xs text-slate-500 mt-4">完成毕业要求</p>
        </div>

        <!-- 学分落后学生 -->
        <div class="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-md transition group cursor-pointer">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm font-medium text-slate-600 mb-2">学分落后</p>
              <p class="text-4xl font-bold text-orange-600">{{ dashboardStats.at_risk_students }}</p>
            </div>
            <div class="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center group-hover:bg-orange-200 transition">
              <span class="text-2xl">⚠</span>
            </div>
          </div>
          <p class="text-xs text-slate-500 mt-4">需要重点关注</p>
        </div>

        <!-- 通过率 -->
        <div class="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-md transition">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm font-medium text-slate-600 mb-2">通过率</p>
              <p class="text-4xl font-bold text-purple-600">{{ dashboardStats.pass_rate }}%</p>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <span class="text-2xl">📊</span>
            </div>
          </div>
          <div class="w-full bg-slate-200 rounded-full h-1.5 mt-4">
            <div
              class="bg-gradient-to-r from-purple-500 to-purple-600 h-1.5 rounded-full transition-all"
              :style="{ width: dashboardStats.pass_rate + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- 两列布局 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- 左列：高风险学生预警 -->
        <div class="lg:col-span-2 space-y-8">
          <!-- 高风险学生列表 -->
          <div class="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-orange-50 to-red-50">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                  <span class="text-2xl">🚨</span>
                  <h3 class="text-lg font-bold text-slate-900">高风险学生预警</h3>
                </div>
                <span class="px-3 py-1 bg-orange-200 text-orange-800 text-xs font-semibold rounded-full">
                  前 5 名
                </span>
              </div>
            </div>

            <div class="divide-y divide-slate-200">
              <div
                v-for="student in riskStudents"
                :key="student.student_id"
                class="px-6 py-4 hover:bg-slate-50 transition cursor-pointer group"
                @click="navigateTo('student-detail', { id: student.student_id })"
              >
                <div class="flex items-center justify-between mb-2">
                  <div>
                    <p class="font-semibold text-slate-900">{{ student.name }}</p>
                    <p class="text-xs text-slate-500">学号: {{ student.student_id }}</p>
                  </div>
                  <div class="text-right">
                    <div class="text-sm font-bold text-orange-600">
                      {{ student.total_credits }} / {{ student.required_credits }} 分
                    </div>
                    <p class="text-xs text-slate-500">
                      进度:
                      {{ Math.round((student.total_credits / student.required_credits) * 100) }}%
                    </p>
                  </div>
                </div>

                <!-- 进度条 -->
                <div class="w-full bg-slate-200 rounded-full h-2">
                  <div
                    class="bg-gradient-to-r from-orange-400 to-red-500 h-2 rounded-full transition-all"
                    :style="{ width: Math.round((student.total_credits / student.required_credits) * 100) + '%' }"
                  ></div>
                </div>

                <!-- 备注 -->
                <p v-if="student.notes" class="text-xs text-slate-600 mt-2 italic">💬 {{ student.notes }}</p>
              </div>
            </div>

            <div class="px-6 py-4 bg-slate-50 border-t border-slate-200">
              <router-link
                to="/admin/student-list"
                class="text-sm font-medium text-blue-600 hover:text-blue-700 inline-flex items-center space-x-1"
              >
                <span>查看完整列表</span>
                <span>→</span>
              </router-link>
            </div>
          </div>

          <!-- 魔王课程排行 -->
          <div class="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-red-50 to-pink-50">
              <div class="flex items-center space-x-2">
                <span class="text-2xl">👹</span>
                <h3 class="text-lg font-bold text-slate-900">魔王课程排行</h3>
              </div>
              <p class="text-xs text-slate-600 mt-1">未通过率最高的课程 TOP 3</p>
            </div>

            <div class="divide-y divide-slate-200">
              <div
                v-for="(course, index) in difficultCourses"
                :key="course.name"
                class="px-6 py-4 hover:bg-slate-50 transition"
              >
                <div class="flex items-start justify-between mb-2">
                  <div class="flex items-center space-x-3">
                    <div
                      class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-white"
                      :class="[
                        index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-slate-400' : 'bg-orange-600',
                      ]"
                    >
                      {{ index + 1 }}
                    </div>
                    <div>
                      <p class="font-semibold text-slate-900">{{ course.name }}</p>
                      <p class="text-xs text-slate-500">选修人数: {{ course.total }} 人</p>
                    </div>
                  </div>

                  <div class="text-right">
                    <p class="text-sm font-bold text-red-600">{{ course.failRate }}% 未通过</p>
                    <p class="text-xs text-slate-500">{{ course.failed }} 人挂科</p>
                  </div>
                </div>

                <!-- 未通过率进度条 -->
                <div class="w-full bg-red-100 rounded-full h-1.5">
                  <div
                    class="bg-gradient-to-r from-red-500 to-red-600 h-1.5 rounded-full"
                    :style="{ width: course.failRate + '%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右列：快速操作 & 系统信息 -->
        <div class="space-y-6">
          <!-- 快速操作 -->
          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <h3 class="text-lg font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <span class="text-2xl">⚡</span>
              <span>快速操作</span>
            </h3>

            <div class="space-y-3">
              <router-link
                to="/admin/student-list"
                class="w-full px-4 py-3 bg-blue-50 hover:bg-blue-100 text-blue-700 font-medium rounded-lg transition flex items-center space-x-2"
              >
                <span>📋</span>
                <span>学生列表管理</span>
              </router-link>

              <button
                @click="adminStore.exportStudentsAsCSV()"
                class="w-full px-4 py-3 bg-green-50 hover:bg-green-100 text-green-700 font-medium rounded-lg transition flex items-center space-x-2"
              >
                <span>📥</span>
                <span>导出学生数据</span>
              </button>

              <button
                class="w-full px-4 py-3 bg-purple-50 hover:bg-purple-100 text-purple-700 font-medium rounded-lg transition flex items-center space-x-2"
              >
                <span>📊</span>
                <span>查看详细报表</span>
              </button>

              <button
                class="w-full px-4 py-3 bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium rounded-lg transition flex items-center space-x-2"
              >
                <span>⚙️</span>
                <span>系统设置</span>
              </button>
            </div>
          </div>

          <!-- 系统信息 -->
          <div class="bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl border border-slate-200 p-6 space-y-4">
            <h3 class="text-lg font-bold text-slate-900">系统信息</h3>

            <div class="space-y-3 text-sm">
              <div class="flex items-center justify-between">
                <span class="text-slate-600">系统版本</span>
                <span class="font-medium text-slate-900">v1.0.0</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">最后更新</span>
                <span class="font-medium text-slate-900">今天 10:30</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">数据更新频率</span>
                <span class="font-medium text-slate-900">实时</span>
              </div>
            </div>

            <div class="pt-4 border-t border-slate-200">
              <p class="text-xs text-slate-600 leading-relaxed">
                💡 提示：系统会自动检测学生学分状态，高风险学生会被标记为需要重点关注。
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'

// ===== 状态管理 =====
const router = useRouter()
const adminStore = useAdminStore()

// ===== 计算属性 =====
// 获取仪表板统计数据
const dashboardStats = computed(() => adminStore.dashboardStats)

// 获取高风险学生列表
const riskStudents = computed(() => adminStore.riskStudents)

// 获取魔王课程
const difficultCourses = computed(() => adminStore.difficultCourses)

// ===== 方法 =====
/**
 * 导航到指定页面
 * @param routeName - 路由名称
 * @param params - 路由参数
 */
const navigateTo = (routeName: string, params?: Record<string, any>) => {
  router.push({
    name: routeName,
    params: params,
  })
}

/**
 * 处理登出
 */
const handleLogout = () => {
  adminStore.adminLogout()
  ElMessage.success('已登出')
  router.push({ name: 'admin-login' })
}
</script>

<style scoped>
/* 卡片悬停效果 */
.group:hover {
  transform: translateY(-2px);
}
</style>
