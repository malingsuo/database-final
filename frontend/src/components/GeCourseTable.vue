<script setup lang="ts">
import type { GeCourse } from '@/api/types'

defineProps<{ courses: GeCourse[] }>()

const GE_CORE    = 1 << 7
const DOMAIN_BITS = [
  { bit: 1 << 6, label: '人' },
  { bit: 1 << 5, label: '社' },
  { bit: 1 << 4, label: '自' },
  { bit: 1 << 3, label: '資' },
  { bit: 1 << 2, label: '書' },
  { bit: 1 << 1, label: '外' },
  { bit: 1 << 0, label: '中' },
]

function isCore(label: number) {
  return (label & GE_CORE) !== 0
}

function crossDomainTags(label: number): string[] {
  const domainOnly = label & ~GE_CORE
  const hits = DOMAIN_BITS.filter(d => (domainOnly & d.bit) !== 0).map(d => d.label)
  return hits.length > 1 ? hits : []
}
</script>

<template>
  <el-table :data="courses" stripe size="small" empty-text="無資料" class="course-table">
    <el-table-column prop="course_name" label="課程名稱" min-width="180" show-overflow-tooltip />
    <el-table-column prop="course_code" label="課程代碼" width="110" />
    <el-table-column label="學分" width="70" align="center">
      <template #default="{ row }">{{ row.credits ?? '-' }}</template>
    </el-table-column>
    <el-table-column label="成績" width="120" align="center">
      <template #default="{ row }">{{ row.score ?? '-' }}</template>
    </el-table-column>
    <el-table-column label="標註" width="160" align="center">
      <template #default="{ row }">
        <el-tag
          v-if="isCore(row.ge_label)"
          size="small"
          type="danger"
          effect="plain"
          class="tag"
        >核心</el-tag>
        <el-tag
          v-for="t in crossDomainTags(row.ge_label)"
          :key="t"
          size="small"
          type="info"
          effect="plain"
          class="tag"
        >[{{ t }}]</el-tag>
        <span v-if="!isCore(row.ge_label) && crossDomainTags(row.ge_label).length === 0">-</span>
      </template>
    </el-table-column>
  </el-table>
</template>

<style scoped>
.course-table { width: 100%; }
.tag { margin: 0 2px; }
</style>
