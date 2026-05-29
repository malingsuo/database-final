<script setup lang="ts">
import { computed } from 'vue'
import type { ElectiveCredits } from '@/api/types'

const props = defineProps<{
  elective: ElectiveCredits
}>()

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
        <span class="card-title">選修學分缺口</span>
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

    <el-descriptions :column="2" border size="small" class="elective-desc">
      <el-descriptions-item label="畢業總學分">{{ elective.graduation_total }}</el-descriptions-item>
      <el-descriptions-item label="已修總學分">{{ elective.total_credits_earned }}</el-descriptions-item>
      <el-descriptions-item label="主系應修">{{ elective.major_required }}</el-descriptions-item>
      <el-descriptions-item label="通識應修">{{ elective.ge_required }}</el-descriptions-item>
      <el-descriptions-item label="體育應修">{{ elective.pe_required }}</el-descriptions-item>
      <el-descriptions-item label="選修應修">{{ elective.elective_required }}</el-descriptions-item>
      <el-descriptions-item label="選修已修">{{ elective.elective_earned }}</el-descriptions-item>
      <el-descriptions-item label="選修尚缺">
        <span :class="{ miss: !complete }">{{ elective.elective_gap }}</span>
      </el-descriptions-item>
    </el-descriptions>

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

.miss {
  color: var(--el-color-danger);
  font-weight: 700;
}

.note {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
