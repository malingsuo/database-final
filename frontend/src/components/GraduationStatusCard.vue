<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheckFilled, WarningFilled } from '@element-plus/icons-vue'
import type { CheckSummary, StudentInfo } from '@/api/types'

const props = defineProps<{
  student: StudentInfo
  summary: CheckSummary
}>()

const allComplete = computed(() => props.summary.all_complete)
</script>

<template>
  <el-card shadow="never" class="status-card" :class="allComplete ? 'ok' : 'warn'">
    <div class="status-body">
      <el-icon class="status-icon" :size="56">
        <CircleCheckFilled v-if="allComplete" />
        <WarningFilled v-else />
      </el-icon>
      <div class="status-text">
        <div class="status-title">
          {{ allComplete ? '恭喜，已達成畢業標準！' : '尚未達成畢業標準' }}
        </div>
        <div class="status-sub">
          <span>{{ student.chinese_name || '—' }}</span>
          <el-divider direction="vertical" />
          <span>{{ student.student_number }}</span>
          <el-divider direction="vertical" />
          <span>{{ student.register_major }}</span>
          <template v-if="student.total_credits != null">
            <el-divider direction="vertical" />
            <span>已修 {{ student.total_credits }} 學分</span>
          </template>
        </div>
        <div v-if="!allComplete && summary.incomplete_items.length" class="incomplete">
          <span class="incomplete-label">待完成專案：</span>
          <el-tag
            v-for="item in summary.incomplete_items"
            :key="item"
            type="danger"
            effect="plain"
            class="incomplete-tag"
          >
            {{ item }}
          </el-tag>
        </div>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.status-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.status-card.ok {
  background: linear-gradient(135deg, #e8f7ee 0%, #f5fbf7 100%);
  border-color: var(--el-color-success-light-5);
}

.status-card.warn {
  background: linear-gradient(135deg, #fdf0ef 0%, #fef7f6 100%);
  border-color: var(--el-color-danger-light-5);
}

.status-body {
  display: flex;
  align-items: center;
  gap: 20px;
}

.status-icon {
  flex-shrink: 0;
}

.status-card.ok .status-icon {
  color: var(--el-color-success);
}

.status-card.warn .status-icon {
  color: var(--el-color-danger);
}

.status-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 8px;
}

.status-sub {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.incomplete {
  margin-top: 12px;
}

.incomplete-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.incomplete-tag {
  margin: 0 6px 6px 0;
}
</style>
