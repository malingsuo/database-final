<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Download, Search } from '@element-plus/icons-vue'
import { useAdminStore } from '@/stores/admin'

const router = useRouter()
const adminStore = useAdminStore()

const filteredStudents = computed(() => adminStore.filteredStudents)
const totalStudents = computed(() => adminStore.students.length)

const currentAcademicYear = computed(() => {
  const now = new Date()
  const taiwanYear = now.getFullYear() - 1911
  return now.getMonth() + 1 >= 8 ? taiwanYear : taiwanYear - 1
})

function gradeLabel(admissionYear: number) {
  const grade = Math.max(1, currentAcademicYear.value - admissionYear + 1)
  return `${grade} 年級`
}

function progress(s: { total_credits: number; required_credits: number }) {
  if (s.required_credits <= 0) return 0
  return Math.min(100, Math.round((s.total_credits / s.required_credits) * 100))
}

function statusTag(status: 'on_track' | 'at_risk') {
  return status === 'on_track'
    ? { label: '已達標', type: 'success' as const }
    : { label: '需關注', type: 'warning' as const }
}

function navigateToDetail(studentId: string) {
  router.push({ name: 'student-detail', params: { id: studentId } })
}

function goBack() {
  router.push({ name: 'admin-dashboard' })
}

function handleExport() {
  if (filteredStudents.value.length === 0) {
    ElMessage.warning('目前沒有可匯出的學生')
    return
  }
  adminStore.exportStudentsAsCSV()
  ElMessage.success('已匯出學生列表')
}

function clearFilters() {
  adminStore.searchQuery = ''
  adminStore.filterYear = null
  adminStore.filterStatus = 'all'
  ElMessage.info('已清除篩選條件')
}

onMounted(() => {
  if (adminStore.students.length === 0) adminStore.fetchStudents()
})
</script>

<template>
  <main class="list-page">
    <header class="topbar">
      <div class="title-block">
        <el-button :icon="ArrowLeft" text @click="goBack">返回工作臺</el-button>
        <div>
          <h1>學生列表管理</h1>
          <p>共 {{ totalStudents }} 位學生</p>
        </div>
      </div>
      <el-button type="success" :icon="Download" @click="handleExport">匯出 CSV</el-button>
    </header>

    <el-card shadow="never" class="filter-card">
      <div class="filters">
        <el-input
          v-model="adminStore.searchQuery"
          class="filter-search"
          placeholder="輸入學號或姓名搜尋…"
          clearable
          :prefix-icon="Search"
        />
        <el-select v-model="adminStore.filterYear" class="filter-select" placeholder="入學年度" clearable>
          <el-option :value="112" label="112 學年度" />
          <el-option :value="113" label="113 學年度" />
          <el-option :value="114" label="114 學年度" />
        </el-select>
        <el-select v-model="adminStore.filterStatus" class="filter-select" placeholder="狀態">
          <el-option value="all" label="全部狀態" />
          <el-option value="on_track" label="已達標" />
          <el-option value="at_risk" label="需關注" />
        </el-select>
      </div>
      <div class="filter-foot">
        <span>搜尋結果：<strong>{{ filteredStudents.length }}</strong> 位學生</span>
        <el-button link type="primary" @click="clearFilters">清除篩選</el-button>
      </div>
    </el-card>

    <div v-loading="adminStore.loading" class="list-body">
      <el-row v-if="filteredStudents.length > 0" :gutter="16">
        <el-col v-for="s in filteredStudents" :key="s.student_id" :xs="24" :sm="12" :lg="8">
          <el-card shadow="hover" class="student-card" @click="navigateToDetail(s.student_id)">
            <div class="card-head">
              <div>
                <h3>{{ s.name || '未命名' }}</h3>
                <p class="sid">學號 {{ s.student_id }}</p>
              </div>
              <div class="tags">
                <el-tag :type="statusTag(s.status).type" effect="light" size="small">
                  {{ statusTag(s.status).label }}
                </el-tag>
                <el-tag v-if="s.double_major" type="info" effect="plain" size="small">雙主修</el-tag>
              </div>
            </div>

            <div class="credit-row">
              <span>學分進度</span>
              <strong>{{ s.total_credits }} / {{ s.required_credits }}</strong>
            </div>
            <el-progress
              :percentage="progress(s)"
              :status="s.status === 'on_track' ? 'success' : 'warning'"
              :stroke-width="10"
            />

            <div class="stat-row">
              <div>
                <strong class="pass">{{ s.completed_courses }}</strong>
                <span>已修課程</span>
              </div>
              <div>
                <strong class="miss">{{ s.failed_courses }}</strong>
                <span>未通過課程</span>
              </div>
              <div>
                <strong>{{ gradeLabel(s.admission_year) }}</strong>
                <span>{{ s.admission_year }} 學年度入學</span>
              </div>
            </div>

            <el-alert
              v-if="s.notes"
              class="note"
              type="info"
              :closable="false"
              :title="s.notes"
            />

            <el-button class="detail-btn" type="primary" plain @click.stop="navigateToDetail(s.student_id)">
              檢視詳情
            </el-button>
          </el-card>
        </el-col>
      </el-row>

      <el-empty v-else description="找不到符合條件的學生">
        <el-button type="primary" @click="clearFilters">清除篩選</el-button>
      </el-empty>
    </div>
  </main>
</template>

<style scoped>
.list-page {
  min-height: 100vh;
  padding: 24px clamp(16px, 4vw, 48px) 48px;
  background: #f5f7fa;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.title-block {
  display: flex;
  align-items: center;
  gap: 12px;
}

h1 {
  margin: 0;
  font-size: 22px;
  color: #1f2937;
}

.title-block p {
  margin: 2px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.filter-card {
  margin-bottom: 18px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-search {
  flex: 1 1 280px;
}

.filter-select {
  width: 160px;
}

.filter-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.list-body {
  min-height: 200px;
}

.student-card {
  margin-bottom: 16px;
  cursor: pointer;
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.card-head h3 {
  margin: 0;
  font-size: 17px;
  color: #1f2937;
}

.sid {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.tags {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.credit-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  margin-bottom: 6px;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin: 16px 0;
  text-align: center;
}

.stat-row div {
  display: grid;
  gap: 2px;
  padding: 8px 4px;
  border-radius: 6px;
  background: #f8fafc;
}

.stat-row strong {
  font-size: 18px;
}

.stat-row span {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.pass {
  color: var(--el-color-primary);
}

.miss {
  color: var(--el-color-danger);
}

.note {
  margin-bottom: 12px;
}

.detail-btn {
  width: 100%;
}
</style>
