<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import {
  ElMessage,
  type UploadFile,
  type UploadInstance,
  type UploadRawFile,
} from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useCheckStore } from '@/stores/check'

const router = useRouter()
const check = useCheckStore()
const { loading, result, hasData } = storeToRefs(check)

const uploadRef = ref<UploadInstance>()
const selectedFile = ref<UploadRawFile | null>(null)

onMounted(() => {
  // 進頁時若尚未解析過，先嘗試載入既有資料以顯示目前狀態
  if (hasData.value === null && !loading.value) {
    check.resolveMyCheck()
  }
})

function onChange(file: UploadFile) {
  selectedFile.value = file.raw ?? null
}

function onRemove() {
  selectedFile.value = null
}

async function submit() {
  const file = selectedFile.value
  if (!file) {
    ElMessage.warning('請先選擇要上傳的 .json 檔案')
    return
  }
  if (!file.name.toLowerCase().endsWith('.json')) {
    ElMessage.error('只接受 .json 格式的檔案')
    return
  }
  try {
    const res = await check.upload(file)
    ElMessage.success(`上傳成功，已匯入 ${res.course_count} 筆修課紀錄`)
    uploadRef.value?.clearFiles()
    selectedFile.value = null
    router.push({ name: 'overview' })
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '上傳失敗')
  }
}
</script>

<template>
  <div class="upload-view">
    <el-card v-if="result" shadow="never" class="current-card">
      <template #header><span class="card-title">目前已上傳的資料</span></template>
      <el-descriptions :column="3" border size="small">
        <el-descriptions-item label="姓名">{{ result.student.chinese_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="學號">{{ result.student.student_number }}</el-descriptions-item>
        <el-descriptions-item label="主修">{{ result.student.register_major }}</el-descriptions-item>
      </el-descriptions>
      <p class="hint">重新上傳會以新檔覆蓋現有修課紀錄。</p>
    </el-card>

    <el-card shadow="never" class="upload-card">
      <template #header><span class="card-title">上傳修課資料</span></template>

      <el-upload
        ref="uploadRef"
        drag
        accept=".json"
        :auto-upload="false"
        :limit="1"
        :on-change="onChange"
        :on-remove="onRemove"
        class="uploader"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">將 <em>exportStudentData.json</em> 拖曳到此，或<em>點選選擇檔案</em></div>
        <template #tip>
          <div class="el-upload__tip">
            僅接受校務系統匯出的 .json 檔，且入學年度須為 112 學年度。
          </div>
        </template>
      </el-upload>

      <div class="actions">
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!selectedFile"
          @click="submit"
        >
          開始上傳並檢核
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.upload-view {
  max-width: 720px;
}

.current-card,
.upload-card {
  margin-bottom: 20px;
}

.card-title {
  font-weight: 600;
  font-size: 15px;
}

.hint {
  margin: 12px 0 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.uploader {
  width: 100%;
}

.actions {
  margin-top: 16px;
  text-align: center;
}
</style>
