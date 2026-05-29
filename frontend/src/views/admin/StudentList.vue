<template>
  <div class="min-h-screen bg-slate-50">
    <!-- 頂部導覽列 -->
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
            <h1 class="text-xl font-bold text-slate-900">學生列表管理</h1>
            <p class="text-xs text-slate-500">共 {{ totalStudents }} 位學生</p>
          </div>
        </div>

        <button
          @click="handleExport"
          class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white font-medium rounded-lg transition inline-flex items-center space-x-2"
        >
          <span>匯出 CSV</span>
        </button>
      </div>
    </div>

    <!-- 主容器 -->
    <div class="max-w-7xl mx-auto px-6 py-8">
      <!-- 搜尋與篩選列 -->
      <div class="bg-white rounded-xl border border-slate-200 p-6 mb-8">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- 搜尋框 -->
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-slate-900 mb-2">搜尋學生</label>
            <div class="relative">
              <input
                v-model="adminStore.searchQuery"
                type="text"
                placeholder="輸入學號或姓名..."
                class="w-full px-4 py-2 pl-10 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span class="absolute left-3 top-2.5 text-slate-400">🔍</span>
            </div>
          </div>

          <!-- 入學年度篩選 -->
          <div>
            <label class="block text-sm font-medium text-slate-900 mb-2">入學年度篩選</label>
            <select
              v-model.number="adminStore.filterYear"
              class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option :value="null">全部學年度</option>
              <option :value="112">112 學年度</option>
              <option :value="113">113 學年度</option>
              <option :value="114">114 學年度</option>
            </select>
          </div>

          <!-- 狀態篩選 -->
          <div>
            <label class="block text-sm font-medium text-slate-900 mb-2">狀態篩選</label>
            <select
              v-model="adminStore.filterStatus"
              class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">全部狀態</option>
              <option value="on_track">已達標</option>
              <option value="at_risk">需關注</option>
            </select>
          </div>
        </div>

        <!-- 篩選結果統計 -->
        <div class="mt-4 flex items-center justify-between text-sm">
          <span class="text-slate-600">
            搜尋結果：<span class="font-bold text-slate-900">{{ filteredStudents.length }}</span> 位學生
          </span>
          <button
            @click="clearFilters"
            class="text-blue-600 hover:text-blue-700 font-medium"
          >
            清除篩選
          </button>
        </div>
      </div>

      <!-- 學生卡片網格 -->
      <div v-if="filteredStudents.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="student in filteredStudents"
          :key="student.student_id"
          @click="navigateToDetail(student.student_id)"
          class="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-lg hover:border-blue-300 transition cursor-pointer transform hover:scale-105 duration-200 group"
        >
          <!-- 卡片頂部：學生基本資訊 -->
          <div class="flex items-start justify-between mb-4">
            <div>
              <h3 class="text-lg font-bold text-slate-900">{{ student.name }}</h3>
              <p class="text-xs text-slate-500 mt-1">學號：{{ student.student_id }}</p>
            </div>

            <!-- 狀態標籤 -->
            <div class="flex flex-col items-end space-y-1">
              <span
                :class="[
                  'px-3 py-1 text-xs font-semibold rounded-full',
                  student.status === 'on_track'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-orange-100 text-orange-800',
                ]"
              >
                {{ student.status === 'on_track' ? '已達標' : '需關注' }}
              </span>

              <!-- 特殊身分標籤 -->
              <div class="flex gap-1 flex-wrap justify-end">
                <span
                  v-if="student.double_major"
                  class="px-2 py-0.5 text-xs font-semibold rounded bg-purple-100 text-purple-800"
                >
                  雙主修
                </span>
                <span
                  v-if="student.exchange_student"
                  class="px-2 py-0.5 text-xs font-semibold rounded bg-blue-100 text-blue-800"
                >
                  交換生
                </span>
              </div>
            </div>
          </div>

          <!-- 學分進度 -->
          <div class="space-y-2 mb-4">
            <div class="flex items-center justify-between text-sm">
              <span class="text-slate-600">學分進度</span>
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

          <!-- 課程統計 -->
          <div class="grid grid-cols-2 gap-3 mb-4 p-3 bg-slate-50 rounded-lg">
            <div class="text-center">
              <p class="text-2xl font-bold text-blue-600">{{ student.completed_courses }}</p>
              <p class="text-xs text-slate-600">已修課程</p>
            </div>
            <div class="text-center">
              <p class="text-2xl font-bold text-purple-600">
                {{ student.courses.filter((c) => !c.is_passed).length }}
              </p>
              <p class="text-xs text-slate-600">未通過課程</p>
            </div>
          </div>

          <!-- 入學年度 -->
          <div class="text-xs text-slate-500 mb-4">
            入學年度：{{ student.admission_year }} 學年度
            <span class="ml-2 font-semibold text-slate-700">（{{ gradeLabel(student.admission_year) }}）</span>
          </div>

          <!-- 管理員備註預覽 -->
          <div
            v-if="student.notes"
            class="p-3 bg-blue-50 border border-blue-200 rounded-lg mb-4"
          >
            <p class="text-xs text-blue-700 line-clamp-2">{{ student.notes }}</p>
          </div>

          <!-- 操作按鈕 -->
          <div class="flex gap-2 pt-4 border-t border-slate-200 group-hover:opacity-100 opacity-75">
            <button
              @click.stop="navigateToDetail(student.student_id)"
              class="flex-1 px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 font-medium rounded-lg transition text-sm"
            >
              檢視詳情
            </button>
          </div>
        </div>
      </div>

      <!-- 空狀態 -->
      <div v-else class="text-center py-16">
        <p class="text-xl font-semibold text-slate-900 mb-2">找不到符合條件的學生</p>
        <p class="text-slate-600 mb-4">請調整搜尋或篩選條件</p>
        <button
          @click="clearFilters"
          class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition"
        >
          清除篩選
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

// ===== 狀態管理 =====
const router = useRouter()
const adminStore = useAdminStore()

// ===== 計算屬性 =====
const filteredStudents = computed(() => adminStore.filteredStudents)

const totalStudents = computed(() => adminStore.students.length)

// ===== 方法 =====
const currentAcademicYear = computed(() => {
  const now = new Date()
  const taiwanYear = now.getFullYear() - 1911
  return now.getMonth() + 1 >= 8 ? taiwanYear : taiwanYear - 1
})

const gradeLabel = (admissionYear: number) => {
  const grade = Math.max(1, currentAcademicYear.value - admissionYear + 1)
  return `${grade} 年級`
}

const navigateToDetail = (studentId: string) => {
  adminStore.getStudentDetail(studentId)
  router.push({
    name: 'student-detail',
    params: { id: studentId },
  })
}

const goBack = () => {
  router.back()
}

const handleExport = () => {
  adminStore.exportStudentsAsCSV()
  ElMessage.success('已匯出學生列表')
}

const clearFilters = () => {
  adminStore.searchQuery = ''
  adminStore.filterYear = null
  adminStore.filterStatus = 'all'
  ElMessage.info('已清除篩選條件')
}
</script>

<style scoped>
/* 卡片陰影效果 */
.group:hover {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}
</style>
