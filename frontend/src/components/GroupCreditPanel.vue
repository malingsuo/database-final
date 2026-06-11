<script setup lang="ts">
import { computed } from 'vue'
import type { CourseEntry, DeptCheck, GroupViolation } from '@/api/types'

const props = defineProps<{
  check: DeptCheck
}>()

type Kind = 'passed' | 'in_progress' | 'missing'
interface GroupRow extends CourseEntry {
  _kind: Kind
}

function courseKey(course: CourseEntry): string {
  const code = course.course_code?.trim()
  if (code && code !== '無') return code.length >= 6 ? code.slice(0, 6) : code
  return course.course_name.replace(/\s+/g, '')
}

function uniqueCount(rows: GroupRow[], kind: Kind): number {
  return new Set(rows.filter((r) => r._kind === kind).map(courseKey)).size
}

function recognizedCount(label: string, rows: GroupRow[], kind: Kind): number {
  const count = uniqueCount(rows, kind)
  if (label === '群A') return Math.min(count, 2)
  if (/^群[A-E]$/.test(label)) return Math.min(count, 1)
  return count
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

const groups = computed(() => {
  const map = new Map<string, GroupRow[]>()
  const push = (list: CourseEntry[], kind: Kind) => {
    for (const c of list) {
      const label = c.group_label
      if (!label) continue
      const arr = map.get(label) ?? []
      arr.push({ ...c, _kind: kind })
      map.set(label, arr)
    }
  }
  push(props.check.passed_courses, 'passed')
  push(props.check.in_progress_courses, 'in_progress')
  push(props.check.missing_courses, 'missing')
  return [...map.entries()]
    .map(([label, rows]) => ({
      label,
      rows,
      passed: recognizedCount(label, rows, 'passed'),
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
})

const violations = computed(() => props.check.group_violations ?? [])
const violationLabels = computed(() => violations.value.map(groupViolationLabel))

const kindMeta: Record<Kind, { label: string; type: 'success' | 'warning' | 'danger' }> = {
  passed: { label: '已通過', type: 'success' },
  in_progress: { label: '修課中', type: 'warning' },
  missing: { label: '未修', type: 'danger' },
}
</script>

<template>
  <el-card shadow="never" class="group-panel">
    <template #header>
      <div class="panel-header">
        <span class="panel-title">群修</span>
        <el-tag :type="violations.length ? 'danger' : 'success'" size="small" effect="dark">
          {{ violations.length ? `${violations.length} 群未達門數` : '門數已達標' }}
        </el-tag>
      </div>
    </template>

    <el-alert
      v-if="violations.length"
      type="warning"
      :closable="false"
      show-icon
      class="violation-alert"
    >
      <template #title>群修門數尚未達標</template>
      <ul class="violation-list">
        <li v-for="(label, idx) in violationLabels" :key="idx">
          {{ label }}
          <span v-if="violations[idx]?.note" class="note">— {{ violations[idx]?.note }}</span>
        </li>
      </ul>
    </el-alert>

    <el-collapse v-if="groups.length" class="group-collapse">
      <el-collapse-item v-for="g in groups" :key="g.label" :name="g.label">
        <template #title>
          <span class="collapse-title">
            <el-tag size="small" type="warning" effect="plain">{{ g.label }}</el-tag>
            認列 {{ g.passed }} 門 / 共列 {{ g.rows.length }} 門
          </span>
        </template>
        <el-table :data="g.rows" size="small" stripe>
          <el-table-column prop="course_name" label="課程名稱" min-width="180" show-overflow-tooltip />
          <el-table-column prop="course_code" label="程式碼" width="110" />
          <el-table-column label="學分" width="70" align="center">
            <template #default="{ row }">{{ row.credits ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="狀態" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="kindMeta[row._kind as Kind].type" effect="plain">
                {{ kindMeta[row._kind as Kind].label }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-collapse-item>
    </el-collapse>

    <el-empty v-else description="無群修課程資料" :image-size="80" />
  </el-card>
</template>

<style scoped>
.group-panel {
  margin-bottom: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  font-weight: 600;
  font-size: 15px;
}

.violation-alert {
  margin-bottom: 12px;
}

.violation-list {
  margin: 6px 0 0;
  padding-left: 18px;
  line-height: 1.7;
}

.note {
  color: var(--el-text-color-secondary);
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
