<script setup lang="ts">
import type { CourseEntry, MatchConfidence } from '@/api/types'

withDefaults(
  defineProps<{
    courses: CourseEntry[]
    showScore?: boolean
    showGroup?: boolean
    showType?: boolean
    showNote?: boolean
    showConfidence?: boolean
    emptyText?: string
  }>(),
  {
    showScore: false,
    showGroup: false,
    showType: false,
    showNote: false,
    showConfidence: false,
    emptyText: '無資料',
  },
)

const confidenceMeta: Record<MatchConfidence, { label: string; type: 'success' | 'warning' | 'info' }> = {
  exact: { label: '程式碼比對', type: 'success' },
  normalized: { label: '課名比對', type: 'success' },
  fuzzy: { label: '模糊比對', type: 'warning' },
  none: { label: '未比對', type: 'info' },
}
</script>

<template>
  <el-table :data="courses" stripe size="small" :empty-text="emptyText" class="course-table">
    <el-table-column prop="course_name" label="課程名稱" min-width="180" show-overflow-tooltip />
    <el-table-column prop="course_code" label="課程程式碼" width="110" />
    <el-table-column label="學分" width="70" align="center">
      <template #default="{ row }">{{ row.credits ?? '-' }}</template>
    </el-table-column>
    <el-table-column v-if="showGroup" label="群" width="120" align="center">
      <template #default="{ row }">
        <el-tag v-if="row.group_label" size="small" type="warning" effect="plain">
          {{ row.group_label }}
        </el-tag>
        <span v-else>-</span>
      </template>
    </el-table-column>
    <el-table-column v-if="showType" prop="course_type" label="型別" width="90" align="center">
      <template #default="{ row }">{{ row.course_type ?? '-' }}</template>
    </el-table-column>
    <el-table-column v-if="showScore" label="成績" width="120" align="center">
      <template #default="{ row }">{{ row.score ?? '-' }}</template>
    </el-table-column>
    <el-table-column v-if="showNote" label="備註" min-width="120">
      <template #default="{ row }">{{ row.note ?? '-' }}</template>
    </el-table-column>
    <el-table-column v-if="showConfidence" label="比對" width="100" align="center">
      <template #default="{ row }">
        <el-tag
          v-if="row.match_confidence"
          size="small"
          :type="confidenceMeta[row.match_confidence as MatchConfidence]?.type ?? 'info'"
          effect="plain"
        >
          {{ confidenceMeta[row.match_confidence as MatchConfidence]?.label ?? row.match_confidence }}
        </el-tag>
        <span v-else>-</span>
      </template>
    </el-table-column>
  </el-table>
</template>

<style scoped>
.course-table {
  width: 100%;
}
</style>
