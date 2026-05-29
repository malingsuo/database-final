<template>
  <div class="min-h-screen bg-slate-50">
    <!-- 顶部导航栏 -->
    <div class="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-sm">
      <div class="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <button
            @click="goBack"
            class="px-3 py-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition"
          >
            ← 返回
          </button>
          <div v-if="student">
            <h1 class="text-xl font-bold text-slate-900">{{ student.name }} 的修课记录</h1>
            <p class="text-xs text-slate-500">学号: {{ student.student_id }}</p>
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <span
            :class="[
              'px-3 py-1 text-xs font-semibold rounded-full',
              student?.status === 'on_track'
                ? 'bg-green-100 text-green-800'
                : 'bg-orange-100 text-orange-800',
            ]"
          >
            {{ student?.status === 'on_track' ? '✓ 已达标' : '⚠ 学分落后' }}
          </span>
        </div>
      </div>
    </div>

    <!-- 主容器 -->
    <div class="max-w-5xl mx-auto px-6 py-8" v-if="student">
      <!-- 基本信息卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <!-- 学生信息卡 -->
        <div class="bg-white rounded-xl border border-slate-200 p-6 md:col-span-2">
          <h2 class="text-lg font-bold text-slate-900 mb-4">基本信息</h2>

          <div class="space-y-4">
            <!-- 姓名 -->
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <span class="text-slate-600 font-medium">姓名</span>
              <span class="text-slate-900 font-semibold">{{ student.name }}</span>
            </div>

            <!-- 学号 -->
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <span class="text-slate-600 font-medium">学号</span>
              <span class="text-slate-900 font-semibold">{{ student.student_id }}</span>
            </div>

            <!-- 入学年度与年级 -->
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <span class="text-slate-600 font-medium">入学年度 / 年级</span>
              <span class="text-slate-900 font-semibold">
                {{ student.admission_year }} / {{ new Date().getFullYear() - student.admission_year + 1 }}年级
              </span>
            </div>

            <!-- 特殊身份 -->
            <div class="pt-3 border-t border-slate-100">
              <span class="text-slate-600 font-medium block mb-2">特殊身份</span>
              <div class="flex gap-2 flex-wrap">
                <span
                  v-if="student.double_major"
                  class="px-3 py-1 bg-purple-100 text-purple-800 text-sm font-semibold rounded-full"
                >
                  🎓 双主修
                </span>
                <span
                  v-if="student.exchange_student"
                  class="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-semibold rounded-full"
                >
                  ✈️ 交换生预审
                </span>
                <span
                  v-if="!student.double_major && !student.exchange_student"
                  class="px-3 py-1 bg-slate-100 text-slate-600 text-sm font-semibold rounded-full"
                >
                  普通学生
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 学分统计卡 -->
        <div class="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl border border-blue-200 p-6">
          <h2 class="text-lg font-bold text-slate-900 mb-4">学分统计</h2>

          <div class="space-y-4">
            <!-- 完成学分 -->
            <div class="text-center p-4 bg-white rounded-lg">
              <p class="text-3xl font-bold text-blue-600">{{ student.total_credits }}</p>
              <p class="text-sm text-slate-600 mt-1">已修学分</p>
            </div>

            <!-- 必需学分 -->
            <div class="text-center p-4 bg-white rounded-lg">
              <p class="text-3xl font-bold text-purple-600">{{ student.required_credits }}</p>
              <p class="text-sm text-slate-600 mt-1">必需学分</p>
            </div>

            <!-- 完成度 -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm text-slate-600">完成度</span>
                <span class="text-lg font-bold text-slate-900">
                  {{ Math.round((student.total_credits / student.required_credits) * 100) }}%
                </span>
              </div>
              <div class="w-full bg-slate-300 rounded-full h-3">
                <div
                  class="h-3 rounded-full bg-gradient-to-r from-blue-500 to-purple-600"
                  :style="{ width: Math.round((student.total_credits / student.required_credits) * 100) + '%' }"
                ></div>
              </div>
            </div>

            <!-- 课程统计 -->
            <div class="pt-4 border-t border-blue-200 space-y-2 text-sm">
              <div class="flex items-center justify-between">
                <span class="text-slate-600">已修课程</span>
                <span class="font-bold text-slate-900">{{ student.completed_courses }} 门</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">通过课程</span>
                <span class="font-bold text-green-600">{{ student.courses.filter((c) => c.is_passed).length }} 门</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-600">挂科课程</span>
                <span class="font-bold text-red-600">{{ student.courses.filter((c) => !c.is_passed).length }} 门</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 学分进度条展示 -->
      <div class="bg-white rounded-xl border border-slate-200 p-6 mb-8">
        <h2 class="text-lg font-bold text-slate-900 mb-6">学分分类进度</h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- 系必修 -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="font-semibold text-slate-900">系必修课程</span>
              <span class="text-sm text-slate-600">{{ getCategoryCredits('departmentCore') }} / 40 分</span>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-3">
              <div
                class="h-3 rounded-full bg-gradient-to-r from-blue-400 to-blue-600"
                :style="{ width: Math.round((getCategoryCredits('departmentCore') / 40) * 100) + '%' }"
              ></div>
            </div>
            <p class="text-xs text-slate-500 mt-2">{{ Math.round((getCategoryCredits('departmentCore') / 40) * 100) }}% 完成</p>
          </div>

          <!-- 校必修 -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="font-semibold text-slate-900">校必修课程</span>
              <span class="text-sm text-slate-600">{{ getCategoryCredits('core') }} / 30 分</span>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-3">
              <div
                class="h-3 rounded-full bg-gradient-to-r from-green-400 to-green-600"
                :style="{ width: Math.round((getCategoryCredits('core') / 30) * 100) + '%' }"
              ></div>
            </div>
            <p class="text-xs text-slate-500 mt-2">{{ Math.round((getCategoryCredits('core') / 30) * 100) }}% 完成</p>
          </div>

          <!-- 选修课程 -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="font-semibold text-slate-900">选修课程</span>
              <span class="text-sm text-slate-600">{{ getCategoryCredits('elective') }} / 30 分</span>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-3">
              <div
                class="h-3 rounded-full bg-gradient-to-r from-purple-400 to-purple-600"
                :style="{ width: Math.round((getCategoryCredits('elective') / 30) * 100) + '%' }"
              ></div>
            </div>
            <p class="text-xs text-slate-500 mt-2">{{ Math.round((getCategoryCredits('elective') / 30) * 100) }}% 完成</p>
          </div>

          <!-- 通识课程 -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="font-semibold text-slate-900">通识课程</span>
              <span class="text-sm text-slate-600">{{ getCategoryCredits('general') }} / 20 分</span>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-3">
              <div
                class="h-3 rounded-full bg-gradient-to-r from-orange-400 to-orange-600"
                :style="{ width: Math.round((getCategoryCredits('general') / 20) * 100) + '%' }"
              ></div>
            </div>
            <p class="text-xs text-slate-500 mt-2">{{ Math.round((getCategoryCredits('general') / 20) * 100) }}% 完成</p>
          </div>
        </div>
      </div>

      <!-- 修课清单 -->
      <div class="bg-white rounded-xl border border-slate-200 p-6 mb-8">
        <h2 class="text-lg font-bold text-slate-900 mb-4">修课清单</h2>

        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 border-b border-slate-200">
              <tr>
                <th class="px-4 py-3 text-left font-semibold text-slate-900">课程名称</th>
                <th class="px-4 py-3 text-center font-semibold text-slate-900">类别</th>
                <th class="px-4 py-3 text-center font-semibold text-slate-900">学分</th>
                <th class="px-4 py-3 text-center font-semibold text-slate-900">学年学期</th>
                <th class="px-4 py-3 text-center font-semibold text-slate-900">成绩</th>
                <th class="px-4 py-3 text-center font-semibold text-slate-900">状态</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr
                v-for="course in student.courses"
                :key="course.course_id"
                class="hover:bg-slate-50 transition"
                :class="{ 'bg-red-50': !course.is_passed }"
              >
                <td class="px-4 py-3">
                  <span class="font-semibold text-slate-900">{{ course.course_name }}</span>
                  <p class="text-xs text-slate-500">{{ course.course_id }}</p>
                </td>
                <td class="px-4 py-3 text-center">
                  <span
                    class="px-2 py-1 text-xs font-semibold rounded"
                    :class="getCategoryBadgeClass(course.category)"
                  >
                    {{ getCategoryName(course.category) }}
                  </span>
                </td>
                <td class="px-4 py-3 text-center font-semibold">{{ course.credits }}</td>
                <td class="px-4 py-3 text-center text-slate-600">
                  {{ course.year }}/{{ course.semester }}
                </td>
                <td
                  class="px-4 py-3 text-center font-bold"
                  :class="{
                    'text-green-600': course.is_passed && course.grade >= 80,
                    'text-orange-600': course.is_passed && course.grade < 80,
                    'text-red-600': !course.is_passed,
                  }"
                >
                  {{ course.grade }}
                </td>
                <td class="px-4 py-3 text-center">
                  <span
                    v-if="course.is_passed"
                    class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800"
                  >
                    ✓ 通过
                  </span>
                  <span
                    v-else
                    class="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800"
                  >
                    ✗ 挂科
                  </span>
                </td>
              </tr>

              <!-- 如果没有课程记录 -->
              <tr v-if="student.courses.length === 0">
                <td colspan="6" class="px-4 py-8 text-center text-slate-500">
                  暂无修课记录
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 管理员备忘录区块 -->
      <div class="bg-white rounded-xl border border-slate-200 p-6">
        <h2 class="text-lg font-bold text-slate-900 mb-4">管理员备忘录</h2>

        <div class="space-y-4">
          <p class="text-sm text-slate-600">
            💡 在此区域记录该生的特殊抵免状况、行政备注或学业指导建议。
          </p>

          <textarea
            v-model="editingNotes"
            rows="6"
            placeholder="输入备注信息，例如：已通过校级交换生审核、申请科技学分认证中..."
            class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder-slate-400"
          ></textarea>

          <div class="flex gap-3 justify-end">
            <button
              @click="cancelEdit"
              class="px-4 py-2 text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition font-medium"
            >
              取消
            </button>
            <button
              @click="saveNotes"
              class="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition font-medium"
            >
              保存备忘录
            </button>
          </div>

          <!-- 显示现有备注 -->
          <div v-if="student.notes" class="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p class="text-sm text-blue-900">📝 现有备注：</p>
            <p class="text-sm text-blue-800 mt-2">{{ student.notes }}</p>
          </div>
        </div>
      </div>

      <!-- 学生状态管理 -->
      <div class="bg-white rounded-xl border border-slate-200 p-6 mt-8">
        <h2 class="text-lg font-bold text-slate-900 mb-4">学生状态管理</h2>

        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
            <div>
              <p class="font-semibold text-slate-900">当前状态</p>
              <p class="text-sm text-slate-600">
                该学生目前标记为：
                <span
                  :class="[
                    'font-bold',
                    student.status === 'on_track' ? 'text-green-600' : 'text-orange-600',
                  ]"
                >
                  {{ student.status === 'on_track' ? '已达标' : '学分落后' }}
                </span>
              </p>
            </div>

            <div class="flex gap-2">
              <button
                v-if="student.status !== 'on_track'"
                @click="updateStatus('on_track')"
                class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition font-medium text-sm"
              >
                标记为已达标
              </button>
              <button
                v-if="student.status !== 'at_risk'"
                @click="updateStatus('at_risk')"
                class="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg transition font-medium text-sm"
              >
                标记为学分落后
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="text-center py-16">
      <p class="text-lg text-slate-600">未找到该学生信息</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'
import type { Course } from '@/stores/admin'

// ===== 状态管理 =====
const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

// 编辑备忘录的本地状态
const editingNotes = ref('')

// ===== 计算属性 =====
// 获取当前学生
const student = computed(() => adminStore.currentStudent)

// ===== 方法 =====
/**
 * 根据课程类别获取学分总数
 * @param category - 课程类别
 */
const getCategoryCredits = (category: string): number => {
  if (!student.value) return 0
  return student.value.courses
    .filter((c: Course) => c.category === category && c.is_passed)
    .reduce((sum: number, c: Course) => sum + c.credits, 0)
}

/**
 * 获取课程类别名称
 * @param category - 课程类别
 */
const getCategoryName = (category: string): string => {
  const names: Record<string, string> = {
    core: '校必修',
    departmentCore: '系必修',
    elective: '选修',
    general: '通识',
  }
  return names[category] || category
}

/**
 * 获取课程类别徽章样式
 * @param category - 课程类别
 */
const getCategoryBadgeClass = (category: string): string => {
  const classes: Record<string, string> = {
    core: 'bg-green-100 text-green-800',
    departmentCore: 'bg-blue-100 text-blue-800',
    elective: 'bg-purple-100 text-purple-800',
    general: 'bg-orange-100 text-orange-800',
  }
  return classes[category] || 'bg-slate-100 text-slate-800'
}

/**
 * 返回上一页
 */
const goBack = () => {
  router.back()
}

/**
 * 保存备忘录
 */
const saveNotes = () => {
  if (student.value) {
    adminStore.updateStudentNotes(student.value.student_id, editingNotes.value)
    ElMessage.success('备忘录已保存')
  }
}

/**
 * 取消编辑
 */
const cancelEdit = () => {
  if (student.value) {
    editingNotes.value = student.value.notes || ''
  }
}

/**
 * 更新学生状态
 * @param status - 新状态
 */
const updateStatus = (status: 'on_track' | 'at_risk') => {
  if (student.value) {
    adminStore.updateStudentStatus(student.value.student_id, status)
    ElMessage.success('学生状态已更新')
  }
}

// ===== 生命周期 =====
onMounted(() => {
  // 获取学生ID并加载学生数据
  const studentId = route.params.id as string
  adminStore.getStudentDetail(studentId)

  // 初始化编辑备忘录的值
  if (student.value) {
    editingNotes.value = student.value.notes || ''
  }
})
</script>

<style scoped>
/* 表格行悬停效果 */
tbody tr:hover {
  background-color: rgba(59, 130, 246, 0.05);
}
</style>
