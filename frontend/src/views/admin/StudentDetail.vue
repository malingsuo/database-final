<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Check, DocumentChecked, EditPen, Warning } from '@element-plus/icons-vue'
import { useAdminStore, type Course } from '@/stores/admin'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const editingNotes = ref('')
const student = computed(() => adminStore.currentStudent)

const currentAcademicYear = computed(() => {
  const now = new Date()
  const taiwanYear = now.getFullYear() - 1911
  return now.getMonth() + 1 >= 8 ? taiwanYear : taiwanYear - 1
})

const gradeLabel = computed(() => {
  if (!student.value) return '-'
  const grade = Math.max(1, currentAcademicYear.value - student.value.admission_year + 1)
  return `${grade} 年級`
})

const completionPercentage = computed(() => {
  if (!student.value || student.value.required_credits <= 0) return 0
  return Math.min(100, Math.round((student.value.total_credits / student.value.required_credits) * 100))
})

const passedCourses = computed(() => student.value?.courses.filter((course) => course.is_passed) ?? [])
const failedCourses = computed(() => student.value?.courses.filter((course) => !course.is_passed) ?? [])

const categoryTargets = [
  { key: 'departmentCore', label: '系所必修', target: 40, color: '#409eff' },
  { key: 'core', label: '校共同必修', target: 30, color: '#67c23a' },
  { key: 'elective', label: '選修課程', target: 30, color: '#7c3aed' },
  { key: 'general', label: '通識課程', target: 20, color: '#e6a23c' },
] as const

function getCategoryCredits(category: Course['category']) {
  if (!student.value) return 0
  return student.value.courses
    .filter((course) => course.category === category && course.is_passed)
    .reduce((sum, course) => sum + course.credits, 0)
}

function categoryPercentage(category: Course['category'], target: number) {
  if (target <= 0) return 0
  return Math.min(100, Math.round((getCategoryCredits(category) / target) * 100))
}

function getCategoryName(category: Course['category']) {
  const names: Record<Course['category'], string> = {
    core: '校共同必修',
    departmentCore: '系所必修',
    elective: '選修',
    general: '通識',
  }
  return names[category]
}

function statusTag(status?: 'on_track' | 'at_risk') {
  return status === 'on_track'
    ? { label: '已達標', type: 'success' as const, icon: Check }
    : { label: '需關注', type: 'warning' as const, icon: Warning }
}

function goBack() {
  router.push({ name: 'admin-dashboard' })
}

function saveNotes() {
  if (!student.value) return
  adminStore.updateStudentNotes(student.value.student_id, editingNotes.value)
  ElMessage.success('備註已儲存')
}

function cancelEdit() {
  editingNotes.value = student.value?.notes || ''
}

function updateStatus(status: 'on_track' | 'at_risk') {
  if (!student.value) return
  adminStore.updateStudentStatus(student.value.student_id, status)
  ElMessage.success('學生狀態已更新')
}

onMounted(() => {
  const studentId = route.params.id as string
  adminStore.getStudentDetail(studentId)
  editingNotes.value = student.value?.notes || ''
})
</script>

<template>
  <main class="detail-page">
    <template v-if="student">
      <header class="detail-header">
        <el-button :icon="ArrowLeft" text @click="goBack">返回管理員工作台</el-button>
        <div class="header-main">
          <div>
            <p class="eyebrow">學生檢核詳情</p>
            <h1>{{ student.name }}</h1>
            <p class="student-meta">
              學號 {{ student.student_id }} · {{ student.admission_year }} 學年度入學 · {{ gradeLabel }}
            </p>
          </div>
          <el-tag :type="statusTag(student.status).type" effect="dark" size="large">
            <el-icon><component :is="statusTag(student.status).icon" /></el-icon>
            {{ statusTag(student.status).label }}
          </el-tag>
        </div>
      </header>

      <section class="summary-card">
        <div class="summary-main">
          <div>
            <p class="eyebrow">畢業進度</p>
            <h2>{{ completionPercentage }}%</h2>
            <p>已取得 {{ student.total_credits }} / {{ student.required_credits }} 學分</p>
          </div>
          <el-progress
            type="circle"
            :width="128"
            :stroke-width="12"
            :percentage="completionPercentage"
            :status="student.status === 'on_track' ? 'success' : 'warning'"
          />
        </div>

        <div class="summary-stats">
          <div>
            <span>已修課程</span>
            <strong>{{ student.completed_courses }}</strong>
          </div>
          <div>
            <span>通過課程</span>
            <strong class="success">{{ passedCourses.length }}</strong>
          </div>
          <div>
            <span>未通過課程</span>
            <strong class="danger">{{ failedCourses.length }}</strong>
          </div>
        </div>
      </section>

      <el-row :gutter="16">
        <el-col :xs="24" :lg="15">
          <el-card shadow="never" class="block-card">
            <template #header>
              <div class="block-header">
                <span>學分分類進度</span>
                <DocumentChecked class="header-icon" />
              </div>
            </template>

            <div class="category-list">
              <div v-for="item in categoryTargets" :key="item.key" class="category-row">
                <div class="category-title">
                  <strong>{{ item.label }}</strong>
                  <span>{{ getCategoryCredits(item.key) }} / {{ item.target }} 學分</span>
                </div>
                <el-progress
                  :percentage="categoryPercentage(item.key, item.target)"
                  :stroke-width="14"
                  :color="item.color"
                />
              </div>
            </div>
          </el-card>

          <el-card shadow="never" class="block-card">
            <template #header>
              <div class="block-header">
                <span>修課清單</span>
                <el-tag effect="plain">{{ student.courses.length }} 門課</el-tag>
              </div>
            </template>

            <el-table :data="student.courses" empty-text="目前沒有修課紀錄">
              <el-table-column label="課程" min-width="180">
                <template #default="{ row }">
                  <strong>{{ row.course_name }}</strong>
                  <p class="course-code">{{ row.course_id }}</p>
                </template>
              </el-table-column>
              <el-table-column label="類別" width="120">
                <template #default="{ row }">
                  <el-tag effect="plain">{{ getCategoryName(row.category) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="credits" label="學分" width="80" align="center" />
              <el-table-column label="學年學期" width="110" align="center">
                <template #default="{ row }">{{ row.year }}-{{ row.semester }}</template>
              </el-table-column>
              <el-table-column prop="grade" label="成績" width="90" align="center" />
              <el-table-column label="狀態" width="110" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.is_passed ? 'success' : 'danger'" effect="light">
                    {{ row.is_passed ? '通過' : '未通過' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="9">
          <el-card shadow="never" class="block-card">
            <template #header>
              <div class="block-header">
                <span>學生資訊</span>
                <el-tag :type="statusTag(student.status).type" effect="plain">
                  {{ statusTag(student.status).label }}
                </el-tag>
              </div>
            </template>

            <div class="info-list">
              <div>
                <span>姓名</span>
                <strong>{{ student.name }}</strong>
              </div>
              <div>
                <span>學號</span>
                <strong>{{ student.student_id }}</strong>
              </div>
              <div>
                <span>入學年度</span>
                <strong>{{ student.admission_year }} 學年度</strong>
              </div>
              <div>
                <span>年級</span>
                <strong>{{ gradeLabel }}</strong>
              </div>
            </div>

            <div class="tag-group">
              <el-tag v-if="student.double_major" type="info" effect="plain">雙主修</el-tag>
              <el-tag v-if="student.exchange_student" type="primary" effect="plain">交換生預審</el-tag>
              <el-tag v-if="!student.double_major && !student.exchange_student" effect="plain">一般學生</el-tag>
            </div>
          </el-card>

          <el-card shadow="never" class="block-card">
            <template #header>
              <div class="block-header">
                <span>管理員備註</span>
                <EditPen class="header-icon" />
              </div>
            </template>

            <el-input
              v-model="editingNotes"
              type="textarea"
              :rows="6"
              placeholder="記錄抵免狀況、學業輔導建議或行政追蹤事項"
            />
            <div class="note-actions">
              <el-button @click="cancelEdit">取消</el-button>
              <el-button type="primary" @click="saveNotes">儲存備註</el-button>
            </div>

            <el-alert
              v-if="student.notes"
              class="current-note"
              type="info"
              :closable="false"
              show-icon
              :title="student.notes"
            />
          </el-card>

          <el-card shadow="never" class="block-card">
            <template #header>
              <div class="block-header">
                <span>狀態調整</span>
                <Warning class="header-icon" />
              </div>
            </template>

            <p class="status-copy">
              目前標記為
              <strong :class="student.status === 'on_track' ? 'success' : 'warning'">
                {{ statusTag(student.status).label }}
              </strong>
            </p>
            <div class="status-actions">
              <el-button
                v-if="student.status !== 'on_track'"
                type="success"
                @click="updateStatus('on_track')"
              >
                標記為已達標
              </el-button>
              <el-button
                v-if="student.status !== 'at_risk'"
                type="warning"
                @click="updateStatus('at_risk')"
              >
                標記為需關注
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <el-empty v-else description="找不到此學生資料">
      <el-button type="primary" @click="goBack">返回管理員工作台</el-button>
    </el-empty>
  </main>
</template>

<style scoped>
.detail-page {
  min-height: 100vh;
  padding: 24px clamp(16px, 4vw, 48px) 48px;
  background: #f5f7fa;
}

.detail-header,
.summary-card,
.block-card {
  width: min(1180px, 100%);
  margin-inline: auto;
}

.detail-header {
  margin-bottom: 16px;
}

.header-main {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-top: 12px;
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--el-color-primary);
  font-size: 12px;
  font-weight: 700;
}

h1,
h2,
p {
  margin: 0;
}

h1 {
  font-size: clamp(28px, 4vw, 42px);
  color: #1f2937;
}

.student-meta,
.summary-main p,
.course-code,
.status-copy {
  color: var(--el-text-color-secondary);
}

.summary-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 24px;
  align-items: center;
  margin-bottom: 16px;
  padding: 24px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: #fff;
}

.summary-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.summary-main h2 {
  font-size: 44px;
  color: #1f2937;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(90px, 1fr));
  gap: 12px;
}

.summary-stats div {
  display: grid;
  gap: 4px;
  padding: 14px;
  border-radius: 8px;
  background: #f8fafc;
}

.summary-stats span,
.info-list span {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.summary-stats strong {
  font-size: 24px;
}

.success {
  color: var(--el-color-success);
}

.danger {
  color: var(--el-color-danger);
}

.warning {
  color: var(--el-color-warning);
}

.block-card {
  margin-bottom: 16px;
}

.block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 700;
}

.header-icon {
  width: 18px;
  color: var(--el-color-primary);
}

.category-list {
  display: grid;
  gap: 18px;
}

.category-title {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 8px;
}

.category-title span {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.course-code {
  margin-top: 4px;
  font-size: 12px;
}

.info-list {
  display: grid;
  gap: 14px;
}

.info-list div {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.tag-group,
.note-actions,
.status-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.note-actions,
.status-actions {
  justify-content: flex-end;
}

.current-note {
  margin-top: 16px;
}

.status-copy {
  line-height: 1.7;
}

@media (max-width: 768px) {
  .header-main,
  .summary-card,
  .summary-main {
    align-items: flex-start;
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .summary-stats {
    grid-template-columns: 1fr;
  }
}
</style>
