<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Check, EditPen, Warning } from '@element-plus/icons-vue'
import { useAdminStore } from '@/stores/admin'
import CheckOverview from '@/components/CheckOverview.vue'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const editingNotes = ref('')
const savingNotes = ref(false)
const savingStatus = ref(false)

const student = computed(() => adminStore.currentStudent)
const check = computed(() => adminStore.currentCheck)
const loading = computed(() => adminStore.loading)

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

function statusTag(status?: 'on_track' | 'at_risk') {
  return status === 'on_track'
    ? { label: '已達標', type: 'success' as const, icon: Check }
    : { label: '需關注', type: 'warning' as const, icon: Warning }
}

function goBack() {
  router.push({ name: 'admin-dashboard' })
}

async function saveNotes() {
  if (!student.value) return
  savingNotes.value = true
  try {
    await adminStore.updateStudentNotes(student.value.student_id, editingNotes.value)
    ElMessage.success('備註已儲存')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '備註儲存失敗')
  } finally {
    savingNotes.value = false
  }
}

function cancelEdit() {
  editingNotes.value = student.value?.notes ?? ''
}

async function updateStatus(status: 'on_track' | 'at_risk') {
  if (!student.value) return
  savingStatus.value = true
  try {
    await adminStore.updateStudentStatus(student.value.student_id, status)
    ElMessage.success('學生狀態已更新')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '狀態更新失敗')
  } finally {
    savingStatus.value = false
  }
}

watch(
  student,
  (s) => {
    editingNotes.value = s?.notes ?? ''
  },
  { immediate: true },
)

onMounted(() => {
  adminStore.fetchStudentDetail(route.params.id as string)
})
</script>

<template>
  <main v-loading="loading" class="detail-page">
    <template v-if="student">
      <header class="detail-header">
        <el-button :icon="ArrowLeft" text @click="goBack">返回管理員工作臺</el-button>
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
            <span>未通過課程</span>
            <strong class="danger">{{ student.failed_courses }}</strong>
          </div>
          <div>
            <span>身分</span>
            <strong>{{ student.double_major ? '雙主修' : '一般生' }}</strong>
          </div>
        </div>
      </section>

      <el-row :gutter="16">
        <el-col :xs="24" :lg="15">
          <el-card shadow="never" class="block-card">
            <template #header>
              <div class="block-header"><span>畢業檢核結果</span></div>
            </template>
            <CheckOverview v-if="check" :result="check" />
            <el-empty v-else description="尚無檢核資料（學生可能未上傳修課資料）" />
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
              <el-tag v-else effect="plain">一般學生</el-tag>
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
              <el-button type="primary" :loading="savingNotes" @click="saveNotes">儲存備註</el-button>
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
                :loading="savingStatus"
                @click="updateStatus('on_track')"
              >
                標記為已達標
              </el-button>
              <el-button
                v-if="student.status !== 'at_risk'"
                type="warning"
                :loading="savingStatus"
                @click="updateStatus('at_risk')"
              >
                標記為需關注
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <el-empty v-else-if="!loading" description="找不到此學生資料">
      <el-button type="primary" @click="goBack">返回管理員工作臺</el-button>
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
