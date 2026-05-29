<script setup lang="ts">
import type { GeCheck, PeCheck } from '@/api/types'
import CheckGate from '@/components/CheckGate.vue'
import GraduationStatusCard from '@/components/GraduationStatusCard.vue'
import RequirementBlock from '@/components/RequirementBlock.vue'
import ElectiveGapCard from '@/components/ElectiveGapCard.vue'

function gePercentage(ge: GeCheck): number {
  const required = ge.categories.reduce((s, c) => s + c.credits_required, 0)
  if (required <= 0) return ge.status === 'complete' ? 100 : 0
  const earned = ge.categories.reduce((s, c) => s + Math.min(c.earned_credits, c.credits_required), 0)
  return Math.min(100, Math.round((earned / required) * 100))
}

function pePercentage(pe: PeCheck): number {
  if (pe.required_semesters <= 0) return 100
  return Math.min(100, Math.round((pe.passed_semesters / pe.required_semesters) * 100))
}

function statusTag(status: string) {
  return status === 'complete'
    ? { label: '已達標', type: 'success' as const }
    : { label: '未達標', type: 'danger' as const }
}
</script>

<template>
  <CheckGate v-slot="{ result }">
    <div class="overview">
      <GraduationStatusCard :student="result.student" :summary="result.summary" />

      <el-row :gutter="16">
        <el-col :xs="24" :md="12">
          <RequirementBlock title="主修系所" :check="result.major_check" />
        </el-col>
        <el-col v-if="result.double_major_check" :xs="24" :md="12">
          <RequirementBlock title="雙主修" :check="result.double_major_check" />
        </el-col>
        <el-col
          v-for="(minor, idx) in result.minor_checks"
          :key="idx"
          :xs="24"
          :md="12"
        >
          <RequirementBlock :title="`輔系（${minor.dept_name}）`" :check="minor" />
        </el-col>

        <!-- 通識 -->
        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="block">
            <template #header>
              <div class="block-header">
                <span class="block-title">通識</span>
                <el-tag :type="statusTag(result.ge_check.status).type" effect="dark" size="small">
                  {{ statusTag(result.ge_check.status).label }}
                </el-tag>
              </div>
            </template>
            <el-progress
              :percentage="gePercentage(result.ge_check)"
              :status="result.ge_check.status === 'complete' ? 'success' : undefined"
              :stroke-width="14"
              class="block-progress"
            />
            <div class="ge-cats">
              <div v-for="cat in result.ge_check.categories" :key="cat.remark_code" class="ge-cat">
                <span class="ge-cat-name">
                  {{ cat.category_name }}
                  <el-tag size="small" effect="plain">{{ cat.remark_code }}</el-tag>
                </span>
                <span
                  class="ge-cat-credit"
                  :class="{ miss: cat.missing_credits > 0 }"
                >
                  {{ cat.earned_credits }} / {{ cat.credits_required }}
                </span>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 體育 -->
        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="block">
            <template #header>
              <div class="block-header">
                <span class="block-title">體育必修</span>
                <el-tag :type="statusTag(result.pe_check.status).type" effect="dark" size="small">
                  {{ statusTag(result.pe_check.status).label }}
                </el-tag>
              </div>
            </template>
            <el-progress
              :percentage="pePercentage(result.pe_check)"
              :status="result.pe_check.status === 'complete' ? 'success' : undefined"
              :stroke-width="14"
              class="block-progress"
            />
            <div class="pe-stats">
              <span>已透過 <strong class="pass">{{ result.pe_check.passed_semesters }}</strong> 學期</span>
              <span>應修 <strong>{{ result.pe_check.required_semesters }}</strong> 學期</span>
              <span>
                尚缺
                <strong :class="{ miss: result.pe_check.missing_semesters > 0 }">
                  {{ result.pe_check.missing_semesters }}
                </strong>
                學期
              </span>
            </div>
          </el-card>
        </el-col>

        <!-- 選修缺口 -->
        <el-col :xs="24" :md="12">
          <ElectiveGapCard :elective="result.summary.elective_credits" />
        </el-col>
      </el-row>
    </div>
  </CheckGate>
</template>

<style scoped>
.block {
  margin-bottom: 16px;
}

.block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.block-title {
  font-weight: 600;
  font-size: 15px;
}

.block-progress {
  margin-bottom: 14px;
}

.ge-cats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ge-cat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
}

.ge-cat-name {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ge-cat-credit {
  font-weight: 600;
}

.ge-cat-credit.miss,
.miss {
  color: var(--el-color-danger);
}

.pass {
  color: var(--el-color-success);
}

.pe-stats {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}
</style>
