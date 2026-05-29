<script setup lang="ts">
import { computed } from 'vue'
import type { DeptCheck } from '@/api/types'

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
      :title="check.note || '此項目暫無可比對的畢業規定資料。'"
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
          <div class="stat-value">{{ check.total_credits_required }}</div>
          <div class="stat-label">應修學分</div>
        </div>
        <div class="stat">
          <div class="stat-value pass">{{ check.earned_credits }}</div>
          <div class="stat-label">已修得</div>
        </div>
        <div class="stat">
          <div class="stat-value progress">{{ check.in_progress_credits }}</div>
          <div class="stat-label">修課中</div>
        </div>
        <div class="stat">
          <div class="stat-value" :class="{ miss: (check.missing_credits ?? 0) > 0 }">
            {{ check.missing_credits ?? '-' }}
          </div>
          <div class="stat-label">尚缺</div>
        </div>
      </div>

      <div v-if="check.group_violations && check.group_violations.length" class="violations">
        <div class="violations-title">群修門數未達標：</div>
        <el-tag
          v-for="(gv, idx) in check.group_violations"
          :key="idx"
          type="danger"
          effect="plain"
          class="violation-tag"
        >
          {{ gv.group }}：已過 {{ gv.passed_courses }}/{{ gv.min_courses }} 門
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
