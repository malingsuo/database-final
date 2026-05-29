<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useCheckStore } from '@/stores/check'
import type { DeptCheck } from '@/api/types'
import CheckGate from '@/components/CheckGate.vue'
import CourseTable from '@/components/CourseTable.vue'
import GroupCreditPanel from '@/components/GroupCreditPanel.vue'

const check = useCheckStore()
const { result } = storeToRefs(check)

interface Section {
  source: string
  check: DeptCheck
}

// 主修 + 雙主修 + 各輔系，依序組成可逐區呈現的清單
const sections = computed<Section[]>(() => {
  const r = result.value
  if (!r) return []
  const list: Section[] = [{ source: '主修', check: r.major_check }]
  if (r.double_major_check) list.push({ source: '雙主修', check: r.double_major_check })
  for (const m of r.minor_checks) list.push({ source: `輔系（${m.dept_name}）`, check: m })
  return list
})

const passedSections = computed(() =>
  sections.value.filter((s) => s.check.passed_courses.length > 0),
)
const missingSections = computed(() =>
  sections.value.filter((s) => s.check.missing_courses.length > 0),
)
const inProgressSections = computed(() =>
  sections.value.filter((s) => s.check.in_progress_courses.length > 0),
)

const geMissingCategories = computed(
  () => result.value?.ge_check.categories.filter((c) => c.missing_credits > 0) ?? [],
)
</script>

<template>
  <CheckGate>
    <div class="inventory">
      <el-tabs type="border-card">
        <!-- 已過清單 -->
        <el-tab-pane label="已過清單">
          <template v-if="passedSections.length || (result && result.ge_check.categories.some((c) => c.courses.length))">
            <section v-for="s in passedSections" :key="s.source" class="section">
              <h3 class="section-title">{{ s.source }}：{{ s.check.dept_name }}</h3>
              <CourseTable :courses="s.check.passed_courses" show-score show-group show-confidence />
            </section>

            <section
              v-for="cat in (result?.ge_check.categories ?? []).filter((c) => c.courses.length)"
              :key="cat.remark_code"
              class="section"
            >
              <h3 class="section-title">通識 — {{ cat.category_name }}（{{ cat.remark_code }}）</h3>
              <CourseTable :courses="cat.courses" show-score />
            </section>
          </template>
          <el-empty v-else description="尚無已通過的應修課程" :image-size="80" />
        </el-tab-pane>

        <!-- 缺修清單 -->
        <el-tab-pane label="缺修清單">
          <template v-if="missingSections.length || geMissingCategories.length">
            <section v-for="s in missingSections" :key="s.source" class="section">
              <h3 class="section-title">{{ s.source }}：{{ s.check.dept_name }}</h3>
              <CourseTable
                :courses="s.check.missing_courses"
                show-type
                show-group
                show-note
              />
            </section>

            <section v-if="geMissingCategories.length" class="section">
              <h3 class="section-title">通識缺額</h3>
              <el-table :data="geMissingCategories" stripe size="small">
                <el-table-column prop="category_name" label="類別" min-width="160" />
                <el-table-column prop="remark_code" label="代碼" width="90" align="center" />
                <el-table-column prop="credits_required" label="應修" width="80" align="center" />
                <el-table-column prop="earned_credits" label="已修" width="80" align="center" />
                <el-table-column label="尚缺" width="80" align="center">
                  <template #default="{ row }">
                    <span class="miss">{{ row.missing_credits }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </section>
          </template>
          <el-result
            v-else
            icon="success"
            title="所有應修項目皆已完成或修課中"
            sub-title="目前沒有缺修課程"
          />
        </el-tab-pane>

        <!-- 修課中 -->
        <el-tab-pane label="修課中">
          <template v-if="inProgressSections.length">
            <section v-for="s in inProgressSections" :key="s.source" class="section">
              <h3 class="section-title">{{ s.source }}：{{ s.check.dept_name }}</h3>
              <CourseTable :courses="s.check.in_progress_courses" show-group show-score />
            </section>
          </template>
          <el-empty v-else description="目前沒有修課中的應修課程" :image-size="80" />
        </el-tab-pane>

        <!-- 體育 -->
        <el-tab-pane label="體育">
          <div v-if="result" class="pe-pane">
            <el-alert
              :type="result.pe_check.status === 'complete' ? 'success' : 'warning'"
              :closable="false"
              show-icon
              class="pe-alert"
            >
              已通過 {{ result.pe_check.passed_semesters }} / {{ result.pe_check.required_semesters }} 學期
              <template v-if="result.pe_check.missing_semesters > 0">
                ，尚缺 {{ result.pe_check.missing_semesters }} 學期
              </template>
            </el-alert>
            <el-table :data="result.pe_check.passed_courses" stripe size="small" empty-text="無已通過的體育課">
              <el-table-column prop="course_name" label="課程名稱" min-width="160" show-overflow-tooltip />
              <el-table-column prop="course_code" label="代碼" width="110" />
              <el-table-column prop="academic_year_semester" label="學年期" width="100" align="center" />
              <el-table-column prop="score" label="成績" width="120" align="center">
                <template #default="{ row }">{{ row.score ?? '-' }}</template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 資訊群修 -->
        <el-tab-pane label="資訊群修 A~E">
          <GroupCreditPanel v-if="result" :check="result.major_check" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </CheckGate>
</template>

<style scoped>
.section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 10px;
  padding-left: 8px;
  border-left: 3px solid var(--el-color-primary);
}

.miss {
  color: var(--el-color-danger);
  font-weight: 600;
}

.pe-alert {
  margin-bottom: 16px;
}
</style>
