<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download, RefreshRight, Search, TrendCharts, User, Warning } from '@element-plus/icons-vue'
import { useAdminStore } from '@/stores/admin'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const adminStore = useAdminStore()

const dashboardStats = computed(() => adminStore.dashboardStats)
const riskStudents = computed(() => adminStore.riskStudents)
const difficultCourses = computed(() => adminStore.difficultCourses)
const departmentName = computed(() => auth.user?.department_name ?? '未指定單位')
const adminName = computed(() => auth.user?.name || auth.user?.account || '管理員')

onMounted(() => {
  adminStore.fetchDashboard()
  if (adminStore.students.length === 0) adminStore.fetchStudents()
})

function refresh() {
  adminStore.fetchDashboard()
  adminStore.fetchStudents()
  ElMessage.info('資料已更新')
}

function percent(value: number, total: number) {
  return total > 0 ? Math.min(100, Math.round((value / total) * 100)) : 0
}

function navigateToStudent(id: string) {
  router.push({ name: 'student-detail', params: { id } })
}

function exportCsv() {
  adminStore.exportStudentsAsCSV()
  ElMessage.success('已匯出目前學生清單')
}

async function handleLogout() {
  await auth.logout()
  adminStore.reset()
  ElMessage.success('已登出')
  router.push({ name: 'admin-login' })
}
</script>

<template>
  <main class="admin-page">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">A</div>
        <div>
          <h1>管理員工作臺</h1>
          <p>{{ departmentName }} · {{ adminName }}</p>
        </div>
      </div>

      <div class="top-actions">
        <el-button :icon="Search" @click="router.push({ name: 'student-list' })">學生查詢</el-button>
        <el-button :icon="Download" @click="exportCsv">匯出</el-button>
        <el-button plain @click="handleLogout">登出</el-button>
      </div>
    </header>

    <section class="hero">
      <div>
        <p class="eyebrow">學分檢核總覽</p>
        <h2>{{ adminName }}，今天需要優先處理 {{ dashboardStats.at_risk_students }} 位風險學生</h2>
        <p class="hero-copy">
          依學生學分進度、未通過課程與備註紀錄彙整待追蹤名單，協助系辦快速掌握畢業檢核風險。
        </p>
      </div>
      <div class="hero-meta">
        <span>管理單位</span>
        <strong>{{ departmentName }}</strong>
      </div>
    </section>

    <section class="stats-grid">
      <article class="stat-card">
        <User class="stat-icon blue" />
        <span>學生總數</span>
        <strong>{{ dashboardStats.total_students }}</strong>
      </article>
      <article class="stat-card">
        <TrendCharts class="stat-icon green" />
        <span>進度正常</span>
        <strong>{{ dashboardStats.on_track_students }}</strong>
      </article>
      <article class="stat-card">
        <Warning class="stat-icon orange" />
        <span>需關注</span>
        <strong>{{ dashboardStats.at_risk_students }}</strong>
      </article>
      <article class="stat-card">
        <RefreshRight class="stat-icon purple" />
        <span>達標率</span>
        <strong>{{ dashboardStats.pass_rate }}%</strong>
      </article>
    </section>

    <section class="workspace">
      <article class="panel wide">
        <div class="panel-header">
          <div>
            <h3>風險學生優先清單</h3>
            <p>依學分缺口排序，點選可進入個別學生檢核資料。</p>
          </div>
          <el-button type="primary" plain @click="router.push({ name: 'student-list' })">完整列表</el-button>
        </div>

        <el-table :data="riskStudents" class="admin-table" empty-text="目前沒有風險學生">
          <el-table-column prop="student_id" label="學號" width="110" />
          <el-table-column prop="name" label="姓名" min-width="120" />
          <el-table-column label="入學年度" width="120">
            <template #default="{ row }">{{ row.admission_year }} 學年度</template>
          </el-table-column>
          <el-table-column label="學分進度" min-width="180">
            <template #default="{ row }">
              <div class="progress-cell">
                <span>{{ row.total_credits }} / {{ row.required_credits }}</span>
                <el-progress :percentage="percent(row.total_credits, row.required_credits)" :show-text="false" />
              </div>
            </template>
          </el-table-column>
          <el-table-column label="狀態" width="110">
            <template #default="{ row }">
              <el-tag :type="row.status === 'on_track' ? 'success' : 'warning'" effect="light">
                {{ row.status === 'on_track' ? '正常' : '需關注' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="navigateToStudent(row.student_id)">檢視</el-button>
            </template>
          </el-table-column>
        </el-table>
      </article>

      <aside class="side-stack">
        <article class="panel">
          <h3>課程風險</h3>
          <p class="panel-note">依學生修課紀錄計算未通過率。</p>
          <div class="course-list">
            <div v-for="course in difficultCourses" :key="course.name" class="course-row">
              <div>
                <strong>{{ course.name }}</strong>
                <span>{{ course.failed }} / {{ course.total }} 未通過</span>
              </div>
              <el-progress type="circle" :width="52" :percentage="course.fail_rate" color="#dc2626" />
            </div>
            <el-empty v-if="difficultCourses.length === 0" description="暫無課程風險資料" :image-size="60" />
          </div>
        </article>

        <article class="panel">
          <h3>快速操作</h3>
          <div class="action-list">
            <el-button :icon="Search" @click="router.push({ name: 'student-list' })">搜尋學生</el-button>
            <el-button :icon="Download" @click="exportCsv">匯出 CSV</el-button>
            <el-button :icon="RefreshRight" @click="refresh">重新整理</el-button>
          </div>
        </article>
      </aside>
    </section>
  </main>
</template>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: #f5f7fb;
  color: #111827;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px clamp(20px, 4vw, 56px);
  border-bottom: 1px solid #e5e7eb;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(10px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 800;
  border-radius: 8px;
  background: #1d4ed8;
}

h1,
h2,
h3,
p {
  margin: 0;
}

h1 {
  font-size: 20px;
}

.brand p,
.hero-copy,
.panel p,
.panel-note {
  color: #6b7280;
}

.top-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.hero,
.stats-grid,
.workspace {
  width: min(1180px, calc(100% - 40px));
  margin-inline: auto;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 34px 0 22px;
}

.eyebrow {
  margin-bottom: 8px;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.hero h2 {
  max-width: 760px;
  font-size: clamp(28px, 4vw, 44px);
  line-height: 1.15;
}

.hero-copy {
  max-width: 760px;
  margin-top: 14px;
  line-height: 1.7;
}

.hero-meta {
  min-width: 210px;
  min-height: 60px;
  display: grid;
  gap: 4px;
  align-content: center;
  align-self: flex-end;
  color: #1f2937;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #fff;
  padding: 10px 16px;
}

.hero-meta span {
  color: #6b7280;
  font-size: 13px;
}

.hero-meta strong {
  font-size: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-card,
.panel {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.stat-card {
  display: grid;
  gap: 8px;
  padding: 20px;
}

.stat-icon {
  width: 28px;
  height: 28px;
}

.stat-icon.blue {
  color: #2563eb;
}

.stat-icon.green {
  color: #16a34a;
}

.stat-icon.orange {
  color: #ea580c;
}

.stat-icon.purple {
  color: #7c3aed;
}

.stat-card span {
  color: #6b7280;
  font-size: 14px;
}

.stat-card strong {
  font-size: 34px;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(300px, 0.8fr);
  gap: 18px;
  padding: 18px 0 40px;
}

.panel {
  padding: 22px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.panel h3 {
  font-size: 18px;
}

.panel p,
.panel-note {
  margin-top: 6px;
  font-size: 14px;
}

.admin-table {
  width: 100%;
}

.progress-cell {
  display: grid;
  gap: 6px;
}

.side-stack {
  display: grid;
  gap: 18px;
  align-content: start;
}

.course-list,
.action-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.course-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px;
  border-radius: 8px;
  background: #f9fafb;
}

.course-row div {
  display: grid;
  gap: 4px;
}

.course-row span {
  color: #6b7280;
  font-size: 13px;
}

.action-list :deep(.el-button) {
  justify-content: flex-start;
  margin-left: 0;
}

@media (max-width: 900px) {
  .topbar,
  .hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .stats-grid,
  .workspace {
    grid-template-columns: 1fr;
  }
}
</style>
