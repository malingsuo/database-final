<script setup lang="ts">
import { computed } from 'vue'
import type { CourseEntry, DeptCheck, GroupViolation } from '@/api/types'

const props = defineProps<{
  title: string
  check: DeptCheck
}>()

const statusMeta = computed(() => {
  switch (props.check.status) {
    case 'complete':
      return { label: '已達標', type: 'success' as const }
    case 'incomplete':
      return { label: '未達標', type: 'danger' as const }
    case 'dept_not_found':
      return { label: '查無系所規定', type: 'info' as const }
    case 'no_data':
      return { label: '規定暫無資料', type: 'info' as const }
    default:
      return { label: props.check.status, type: 'info' as const }
  }
})

const hasRules = computed(
  () => props.check.found && !props.check.no_data && props.check.total_credits_required != null,
)

const percentage = computed(() => {
  const req = props.check.total_credits_required
  if (!req || req <= 0) return props.check.status === 'complete' ? 100 : 0
  return Math.min(100, Math.round((props.check.earned_credits / req) * 100))
})

const progressStatus = computed(() => {
  if (props.check.status === 'complete') return 'success'
  return percentage.value >= 100 ? 'success' : 'warning'
})

const hasCreditBreakdown = computed(() => Boolean(props.check.credit_breakdown))

function formatCredit(value: number | null | undefined): string {
  if (value == null) return '-'
  if (!Number.isFinite(value)) return '-'
  return Number.isInteger(value) ? `${value}` : value.toFixed(1)
}

function formatCreditParts(kind: 'required' | 'earned' | 'in_progress' | 'missing'): string {
  const parts = props.check.credit_breakdown?.[kind]
  if (!parts) return '-'
  return `${formatCredit(parts.mandatory)}+${formatCredit(parts.group)}`
}

const requiredCreditsLabel = computed(() =>
  hasCreditBreakdown.value
    ? formatCreditParts('required')
    : formatCredit(props.check.total_credits_required),
)

const earnedCreditsLabel = computed(() =>
  hasCreditBreakdown.value
    ? formatCreditParts('earned')
    : formatCredit(props.check.earned_credits),
)

const inProgressCreditsLabel = computed(() =>
  hasCreditBreakdown.value
    ? formatCreditParts('in_progress')
    : formatCredit(props.check.in_progress_credits),
)

const missingCreditsLabel = computed(() =>
  hasCreditBreakdown.value
    ? formatCreditParts('missing')
    : formatCredit(props.check.missing_credits),
)

function isMandatoryCourse(course: CourseEntry): boolean {
  return course.group_label === '必修' || course.course_type === '必修'
}

function courseLabel(course: CourseEntry): string {
  return course.note ? `${course.course_name}（${course.note}）` : course.course_name
}

function groupRequirementLabel(group: string): string {
  const parts = group.split('+').filter(Boolean)
  if (parts.length <= 1) return group
  const first = parts[0]!
  const last = parts[parts.length - 1]!.replace(/^群/, '')
  return `${first}~${last}總共`
}

function groupViolationLabel(violation: GroupViolation): string {
  const missing = Math.max(0, violation.min_courses - violation.passed_courses)
  const inProgress = violation.in_progress_courses
    ? `（修課中可補 ${violation.in_progress_courses} 門）`
    : ''
  return `${groupRequirementLabel(violation.group)}缺 ${missing} 門${inProgress}`
}

const mandatoryMissingCourses = computed(() =>
  props.check.missing_courses.filter(isMandatoryCourse),
)

const groupMissingItems = computed(() =>
  (props.check.group_violations ?? [])
    .filter((gv) => gv.min_courses > gv.passed_courses)
    .map(groupViolationLabel),
)

const hasMissingItems = computed(
  () => mandatoryMissingCourses.value.length > 0 || groupMissingItems.value.length > 0,
)
</script>

<template>
  <el-card shadow="never" class="req-block">
    <template #header>
      <div class="req-header">
        <span class="req-title">{{ title }}</span>
        <div class="req-header-right">
          <span v-if="check.dept_name" class="dept-name">{{ check.dept_name }}</span>
          <el-tag :type="statusMeta.type" effect="dark" size="small">{{ statusMeta.label }}</el-tag>
        </div>
      </div>
    </template>

    <el-alert
      v-if="!hasRules"
      :title="check.note || '此專案暫無可比對的畢業規定資料。'"
      type="info"
      :closable="false"
      show-icon
    />

    <template v-else>
      <el-progress
        :percentage="percentage"
        :status="progressStatus === 'success' ? 'success' : undefined"
        :stroke-width="14"
        class="req-progress"
      />

      <div class="credit-stats">
        <div class="stat">
          <div class="stat-value">{{ requiredCreditsLabel }}</div>
          <div class="stat-label">{{ hasCreditBreakdown ? '必修+群修' : '應修學分' }}</div>
        </div>
        <div class="stat">
          <div class="stat-value pass">{{ earnedCreditsLabel }}</div>
          <div class="stat-label">已修得</div>
        </div>
        <div class="stat">
          <div class="stat-value progress">{{ inProgressCreditsLabel }}</div>
          <div class="stat-label">修課中</div>
        </div>
        <div class="stat">
          <div class="stat-value" :class="{ miss: (check.missing_credits ?? 0) > 0 }">
            {{ missingCreditsLabel }}
          </div>
          <div class="stat-label">尚缺</div>
        </div>
      </div>

      <div v-if="hasMissingItems" class="violations">
        <div class="violations-title">尚缺項目：</div>
        <el-tag
          v-for="course in mandatoryMissingCourses"
          :key="`mandatory-${course.course_code}-${course.course_name}`"
          type="danger"
          effect="plain"
          class="violation-tag"
        >
          必修：{{ courseLabel(course) }}
        </el-tag>
        <el-tag
          v-for="(item, idx) in groupMissingItems"
          :key="`group-${idx}`"
          type="danger"
          effect="plain"
          class="violation-tag"
        >
          {{ item }}
        </el-tag>
      </div>
    </template>
  </el-card>
</template>

<style scoped>
.req-block {
  margin-bottom: 16px;
}

.req-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.req-title {
  font-weight: 600;
  font-size: 15px;
}

.req-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dept-name {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.req-progress {
  margin-bottom: 16px;
}

.credit-stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.stat {
  flex: 1;
  min-width: 80px;
  text-align: center;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 10px 6px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
}

.stat-value.pass {
  color: var(--el-color-success);
}

.stat-value.progress {
  color: var(--el-color-warning);
}

.stat-value.miss {
  color: var(--el-color-danger);
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.violations {
  margin-top: 14px;
}

.violations-title {
  font-size: 13px;
  color: var(--el-color-danger);
  margin-bottom: 6px;
}

.violation-tag {
  margin: 0 6px 6px 0;
}
</style>
