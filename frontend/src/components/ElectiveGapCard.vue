<script setup lang="ts">
import { computed } from 'vue'
import type { ElectiveCredits } from '@/api/types'

const props = defineProps<{
  elective: ElectiveCredits
}>()

const ri = (v: number | null | undefined) => Math.round(v ?? 0)

const percentage = computed(() => {
  const req = props.elective.elective_required
  if (!req || req <= 0) return 100
  return Math.min(100, Math.round((props.elective.elective_earned / req) * 100))
})

const complete = computed(() => props.elective.elective_gap <= 0)
</script>

<template>
  <el-card shadow="never" class="elective-card">
    <template #header>
      <div class="card-header">
        <span class="card-title">選修</span>
        <el-tag :type="complete ? 'success' : 'danger'" size="small" effect="dark">
          {{ complete ? '已達標' : `尚缺 ${elective.elective_gap} 學分` }}
        </el-tag>
      </div>
    </template>

    <el-progress
      :percentage="percentage"
      :status="complete ? 'success' : undefined"
      :stroke-width="14"
      class="elective-progress"
    />

    <div class="credit-stats">
      <div class="stat">
        <div class="stat-value">{{ ri(elective.elective_required) }}</div>
        <div class="stat-label">應修學分</div>
      </div>
      <div class="stat">
        <div class="stat-value pass">{{ ri(elective.elective_earned) }}</div>
        <div class="stat-label">已修得</div>
      </div>
      <div class="stat">
        <div class="stat-value progress">{{ ri(elective.elective_in_progress) }}</div>
        <div class="stat-label">修課中</div>
      </div>
      <div class="stat">
        <div class="stat-value" :class="{ miss: !complete }">{{ ri(elective.elective_gap) }}</div>
        <div class="stat-label">尚缺</div>
      </div>
    </div>

    <p class="note">{{ elective.note }}</p>
  </el-card>
</template>

<style scoped>
.elective-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-weight: 600;
  font-size: 15px;
}

.elective-progress {
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

.note {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
