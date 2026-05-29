<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useCheckStore } from '@/stores/check'

const router = useRouter()
const check = useCheckStore()
const { loading, error, hasData, result } = storeToRefs(check)

onMounted(() => {
  if (hasData.value === null && !loading.value) {
    check.resolveMyCheck()
  }
})

function retry() {
  check.resolveMyCheck()
}

function goUpload() {
  router.push({ name: 'upload' })
}
</script>

<template>
  <div v-loading="loading" class="check-gate">
    <el-alert v-if="error" type="error" :closable="false" show-icon class="gate-alert">
      <template #title>載入失敗</template>
      <div>{{ error }}</div>
      <el-button size="small" class="retry-btn" @click="retry">重新載入</el-button>
    </el-alert>

    <el-empty
      v-else-if="hasData === false"
      description="尚未上傳修課資料"
    >
      <p class="empty-hint">請先上傳校務系統匯出的 exportStudentData.json，才能進行畢業學分檢核。</p>
      <el-button type="primary" @click="goUpload">前往上傳資料</el-button>
    </el-empty>

    <template v-else-if="hasData && result">
      <slot :result="result" />
    </template>

    <div v-else-if="loading" class="loading-placeholder" />
  </div>
</template>

<style scoped>
.check-gate {
  min-height: 200px;
}

.gate-alert {
  max-width: 640px;
}

.retry-btn {
  margin-top: 10px;
}

.empty-hint {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin: 0 0 12px;
}

.loading-placeholder {
  height: 200px;
}
</style>
