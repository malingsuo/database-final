<template>
  <div class="min-h-screen bg-slate-50">
    <!-- 顶部导航栏 -->
    <div class="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <button
            @click="goBack"
            class="px-3 py-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition"
          >
            ←
          </button>
          <div>
            <h1 class="text-xl font-bold text-slate-900">学生列表管理</h1>
            <p class="text-xs text-slate-500">共 {{ totalStudents }} 位学生</p>
          </div>
        </div>

        <button
          @click="handleExport"
          class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white font-medium rounded-lg transition inline-flex items-center space-x-2"
        >
          <span>📥</span>
          <span>导出 CSV</span>
        </button>
      </div>
    </div>

    <!-- 主容器 -->
    <div class="max-w-7xl mx-auto px-6 py-8">
      <!-- 搜索与筛选栏 -->
      <div class="bg-white rounded-xl border border-slate-200 p-6 mb-8">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- 搜索框 -->
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-slate-900 mb-2">搜索学生</label>
            <div class="relative">
              <input
                v-model="adminStore.searchQuery"
                type="text"
                placeholder="输入学号或姓名..."
                class="w-full px-4 py-2 pl-10 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span class="absolute left-3 top-2.5 text-slate-400">🔍</span>
            </div>
          </div>

          <!-- 年级筛选 -->
          <div>
            <label class="block text-sm font-medium text-slate-900 mb-2">年级筛选</label>
            <select
              v-model.number="adminStore.filterYear"
              class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option :value="null">全部年级</option>
              <option :value="2021">2021 入学</option>
              <option :value="2022">2022 入学</option>
              <option :value="2023">2023 入学</option>
              <option :value="2024">2024 入学</option>
            </select>
          </div>

          <!-- 状态筛选 -->
          <div>
            <label class="block text-sm font-medium text-slate-900 mb-2">状态筛选</label>
            <select
              v-model="adminStore.filterStatus"
              class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">全部状态</option>
              <option value="on_track">已达标</option>
              <option value="at_risk">学分落后</option>
            </select>
          </div>
        </div>

        <!-- 筛选结果统计 -->
        <div class="mt-4 flex items-center justify-between text-sm">
          <span class="text-slate-600">
            搜索结果：<span class="font-bold text-slate-900">{{ filteredStudents.length }}</span> 位学生
          </span>
          <button
            @click="clearFilters"
            class="text-blue-600 hover:text-blue-700 font-medium"
          >
            清除筛选
          </button>
        </div>
      </div>

      <!-- 学生卡片网格 -->
      <div v-if="filteredStudents.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="student in filteredStudents"
          :key="student.student_id"
          @click="navigateToDetail(student.student_id)"
          class="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-lg hover:border-blue-300 transition cursor-pointer transform hover:scale-105 duration-200 group"
        >
          <!-- 卡片顶部：学生基本信息 -->
          <div class="flex items-start justify-between mb-4">
            <div>
              <h3 class="text-lg font-bold text-slate-900">{{ student.name }}</h3>
              <p class="text-xs text-slate-500 mt-1">学号: {{ student.student_id }}</p>
            </div>

            <!-- 状态徽章 -->
            <div class="flex flex-col items-end space-y-1">
              <span
                :class="[
                  'px-3 py-1 text-xs font-semibold rounded-full',
                  student.status === 'on_track'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-orange-100 text-orange-800',
                ]"
              >
                {{ student.status === 'on_track' ? '✓ 已达标' : '⚠ 落后' }}
              </span>

              <!-- 特殊身份标签 -->
              <div class="flex gap-1 flex-wrap justify-end">
                <span
                  v-if="student.double_major"
                  class="px-2 py-0.5 text-xs font-semibold rounded bg-purple-100 text-purple-800"
                >
                  双主修
                </span>
                <span
                  v-if="student.exchange_student"
                  class="px-2 py-0.5 text-xs font-semibold rounded bg-blue-100 text-blue-800"
                >
                  交换生
                </span>
              </div>
            </div>
          </div>

          <!-- 学分进度 -->
          <div class="space-y-2 mb-4">
            <div class="flex items-center justify-between text-sm">
              <span class="text-slate-600">学分进度</span>
              <span class="font-bold text-slate-900">
                {{ student.total_credits }} / {{ student.required_credits }}
              </span>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-2">
              <div
                class="h-2 rounded-full transition-all"
                :class="[
                  student.status === 'on_track'
                    ? 'bg-gradient-to-r from-green-400 to-green-500'
                    : 'bg-gradient-to-r from-orange-400 to-red-500',
                ]"
                :style="{ width: Math.round((student.total_credits / student.required_credits) * 100) + '%' }"
              ></div>
            </div>
            <p class="text-xs text-slate-500 text-right">
              {{ Math.round((student.total_credits / student.required_credits) * 100) }}% 完成
            </p>
          </div>

          <!-- 课程统计 -->
          <div class="grid grid-cols-2 gap-3 mb-4 p-3 bg-slate-50 rounded-lg">
            <div class="text-center">
              <p class="text-2xl font-bold text-blue-600">{{ student.completed_courses }}</p>
              <p class="text-xs text-slate-600">已修课程</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-purple-600">
                {{ student.courses.filter((c) => !c.is_passed).length }}
              </p>
              <p class="text-xs text-slate-600">挂科课程</p>
            </div>
          </div>

          <!-- 入学年度 -->
          <div class="text-xs text-slate-500 mb-4">
            入学年度: {{ student.admission_year }}
            <span class="ml-2 font-semibold text-slate-700">({{ new Date().getFullYear() - student.admission_year + 1 }}年级)</span>
          </div>

          <!-- 管理员备注预览 -->
          <div
            v-if="student.notes"
            class="p-3 bg-blue-50 border border-blue-200 rounded-lg mb-4"
          >
            <p class="text-xs text-blue-700 line-clamp-2">💬 {{ student.notes }}</p>
          </div>

          <!-- 操作按钮 -->
          <div class="flex gap-2 pt-4 border-t border-slate-200 group-hover:opacity-100 opacity-75">
            <button
              @click.stop="navigateToDetail(student.student_id)"
              class="flex-1 px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 font-medium rounded-lg transition text-sm"
            >
              查看详情 →
            </button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="text-center py-16">
        <p class="text-4xl mb-4">📭</p>
        <p class="text-xl font-semibold text-slate-900 mb-2">未找到符合条件的学生</p>
        <p class="text-slate-600 mb-4">尝试调整搜索或筛选条件</p>
        <button
          @click="clearFilters"
          class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition"
        >
          清除筛选
        </button>
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
// 过滤后的学生列表
const filteredStudents = computed(() => adminStore.filteredStudents)

// 总学生数
const totalStudents = computed(() => adminStore.students.length)

// ===== 方法 =====
/**
 * 导航到学生详情页面
 * @param studentId - 学生ID
 */
const navigateToDetail = (studentId: string) => {
  adminStore.getStudentDetail(studentId)
  router.push({
    name: 'student-detail',
    params: { id: studentId },
  })
}

/**
 * 返回到上一页
 */
const goBack = () => {
  router.back()
}

/**
 * 导出学生列表
 */
const handleExport = () => {
  adminStore.exportStudentsAsCSV()
  ElMessage.success('已导出学生列表')
}

/**
 * 清除所有筛选条件
 */
const clearFilters = () => {
  adminStore.searchQuery = ''
  adminStore.filterYear = null
  adminStore.filterStatus = 'all'
  ElMessage.info('已清除筛选条件')
}
</script>

<style scoped>
/* 卡片阴影效果 */
.group:hover {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}
</style>
