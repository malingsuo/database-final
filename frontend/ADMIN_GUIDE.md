# 學分檢核系統 - 管理員端開發指南

## 📋 專案概覽

這是一套完整的學分檢核系統管理員端解決方案，採用 **Vue 3 Composition API + TypeScript + Tailwind CSS + Pinia + Element Plus** 技術棧開發。

系統包含：
- ✅ 專業化的管理員登入介面（深色主題，區隔學生端）
- ✅ 功能完整的管理員儀表板（含關鍵指標、預警、課程排行）
- ✅ 強大的學生列表管理（搜尋、篩選、匯出）
- ✅ 詳盡的學生修課記錄管理（含學分進度、備註、狀態更新）
- ✅ 真實感十足的 Mock 資料（包含 5 位狀態不同的學生）

---

## 🗂️ 檔案結構

```
src/
├── stores/
│   └── admin.ts                          # Pinia 管理員資料儲存（核心業務邏輯）
├── views/admin/
│   ├── AdminLogin.vue                    # 管理員登入介面
│   ├── AdminDashboard.vue                # 管理員儀表板
│   ├── StudentList.vue                   # 學生列表管理
│   └── StudentDetail.vue                 # 學生詳細修課記錄
├── layouts/
│   └── AdminLayout.vue                   # 管理員通用佈局（可選）
├── router/
│   └── index.ts                          # ✅ 已更新路由配置
└── ... (其他既有檔案)
```

---

## 🚀 快速開始

### 1. 訪問管理員系統

```
http://localhost:3000/admin/login
```

### 2. 登入憑據（測試用）

| 欄位 | 值 |
|------|-----|
| **賬號** | admin |
| **密碼** | 12345678 |

### 3. 可用路由

| 路徑 | 名稱 | 說明 |
|------|------|------|
| `/admin/login` | admin-login | 管理員登入 |
| `/admin/dashboard` | admin-dashboard | 管理員儀表板 |
| `/admin/student-list` | student-list | 學生列表 |
| `/admin/student/:id` | student-detail | 學生詳情 |

---

## 📊 核心功能說明

### 1. 管理員登入（AdminLogin.vue）

**特點：**
- 深色漸變背景（與學生端區隔）
- 玻璃態設計（Glassmorphism）
- 響應式適配
- 整合 Element Plus 提示

**關鍵程式碼片段：**
```typescript
const handleLogin = async () => {
  const success = adminStore.adminLogin(
    formData.value.account, 
    formData.value.password
  )
  if (success) {
    router.push({ name: 'admin-dashboard' })
  }
}
```

---

### 2. 管理員儀表板（AdminDashboard.vue）

**包含內容：**

#### 📈 關鍵指標卡片（4 個）
- 總學生數
- 已達標學生數
- 學分落後學生數
- 系統透過率（含進度條）

#### 🚨 高風險學生預警（前 5 名）
- 顯示學分進度條
- 支援點選跳轉到學生詳情
- 管理員備註可見

#### 👹 魔王課程排行（TOP 3）
- 課程未透過率統計
- 掛科人數展示
- 排名獎章（金銀銅）

#### ⚡ 快速操作面板
- 快速連結到學生列表
- 匯出學生資料按鈕
- 系統設定入口

---

### 3. 學生列表管理（StudentList.vue）

**核心功能：**

#### 🔍 搜尋
```typescript
// 支援按學號或姓名搜尋
adminStore.searchQuery = 'S001'  // 或 '林子晴'
```

#### 🎯 篩選
```typescript
// 支援按年級篩選
adminStore.filterYear = 2021  // 或 2022, 2023, 2024

// 支援按狀態篩選
adminStore.filterStatus = 'at_risk'  // 或 'on_track', 'all'
```

#### 📥 匯出 CSV
```typescript
adminStore.exportStudentsAsCSV()
// 自動下載包含學號、姓名、入學年度、狀態等資料的 CSV 檔案
```

**卡片展示資訊：**
- 學生基本資訊（姓名、學號、年級）
- 修課狀態徽章（已達標/落後）
- 特殊身份標籤（雙主修、交換生）
- 學分進度條（視覺化比例）
- 課程統計（已修/掛科數）
- 管理員備註預覽

---

### 4. 學生詳細修課記錄（StudentDetail.vue）

**包含三大主區塊：**

#### 📋 基本資訊區
- 姓名、學號、年級、入學年度
- 特殊身份（雙主修、交換生預審）
- 學分統計（總學分、已修學分、必需學分、完成度）

#### 📊 學分分類進度
四類學分進度條展示：
- 系必修課程：40 分
- 校必修課程：30 分
- 選修課程：30 分
- 通識課程：20 分

**每個進度條顯示：**
- 已完成學分 / 目標學分
- 完成百分比
- 彩色漸變填充

#### 📝 修課清單表格
| 課程名稱 | 類別 | 學分 | 學年學期 | 成績 | 狀態 |
|---------|------|------|---------|------|------|
| 數位系統 | 系必修 | 3 | 2024/1 | 80 | ✓ 透過 |
| 微積分 | 校必修 | 3 | 2023/1 | 52 | ✗ 掛科 |

**成績著色：**
- 綠色：透過且成績 ≥ 80
- 橙色：透過但成績 < 80
- 紅色：掛科（未透過）

#### 📌 管理員備忘錄
- 文字區域供管理員記錄：
  - 特殊抵免狀況
  - 行政備註
  - 學業指導建議
  - 交換認可等特殊情況

#### ⚙️ 學生狀態管理
- 按鈕快速更新學生狀態（已達標 ↔ 學分落後）

---

## 💾 Mock 資料詳解

### 包含的 5 位測試學生

| 學號 | 姓名 | 年級 | 狀態 | 特殊身份 | 用途 |
|------|------|------|------|---------|------|
| S001 | 林子晴 | 3年 | 已達標 | 雙主修 | 優秀學生示例 |
| S002 | 王浩宇 | 2年 | 落後 | 無 | 預警學生示例 |
| S003 | 陳思語 | 3年 | 已達標 | 交換生 | 特殊身份示例 |
| S004 | 許家豪 | 2年 | 落後 | 無 | 高風險學生 |
| S005 | 黃詩涵 | 4年 | 已達標 | 無 | 即將離校學生 |

### 關鍵課程資料

**必須包含的測試課程：**
```javascript
{
  course_id: 'CS101',
  course_name: '數位系統',      // ← 題目要求
  grade: 80,                      // ← 題目要求
  is_passed: true
}
```

此課程出現在林子晴（S001）的修課記錄中。

---

## 🎨 設計特點

### 顏色方案

**管理員登入介面（深色系）**
- 背景：`from-slate-900 via-slate-800 to-slate-900`
- 強調色：`blue-500` 到 `purple-600` 的漸變

**管理員儀表板（亮色系）**
- 背景：`slate-50`
- 卡片：`white` 配 `border-slate-200`

### 響應式設計

```
Mobile-First 斷點：
- sm: ≥ 640px   (md)
- md: ≥ 768px   (表格、雙列)
- lg: ≥ 1024px  (完整三列布局)
- max-width: 7xl (1280px)
```

---

## 🔌 Pinia Store API 參考

### 狀態（State）

```typescript
// 管理員使用者資訊
admin: AdminUser | null

// 學生列表
students: Student[]

// 當前選中的學生
currentStudent: Student | null

// 搜尋與篩選條件
searchQuery: string
filterYear: number | null
filterStatus: 'all' | 'on_track' | 'at_risk'
```

### 計算屬性（Computed）

```typescript
// 儀表板統計資料
dashboardStats: {
  total_students: number
  on_track_students: number
  at_risk_students: number
  pass_rate: number
}

// 高風險學生列表（前 5 名）
riskStudents: Student[]

// 魔王課程排行（未透過率最高的 TOP 3）
difficultCourses: Array<{
  name: string
  total: number
  failed: number
  failRate: number
}>

// 過濾後的學生列表
filteredStudents: Student[]
```

### 方法（Actions）

```typescript
// 管理員登入
adminLogin(account: string, password: string): boolean

// 管理員登出
adminLogout(): void

// 獲取學生詳情
getStudentDetail(studentId: string): Student | undefined

// 更新學生備註
updateStudentNotes(studentId: string, notes: string): void

// 更新學生狀態
updateStudentStatus(
  studentId: string, 
  status: 'on_track' | 'at_risk'
): void

// 匯出學生列表為 CSV
exportStudentsAsCSV(): void
```

---

## 📱 使用場景演示

### 場景 1：檢視高風險學生

1. 登入管理員系統 (`/admin/login`)
2. 進入儀表板 (`/admin/dashboard`)
3. 在"高風險學生預警"區塊中點選任何學生
4. 自動跳轉到該生的詳細修課記錄
5. 檢視學分進度、修課清單、特殊備註

### 場景 2：搜尋與篩選學生

1. 點選"學生列表管理"
2. 在搜尋框輸入：
   - 學號：`S002`
   - 姓名：`王浩宇`
3. 從"年級篩選"選擇 `2022 入學`
4. 從"狀態篩選"選擇 `學分落後`
5. 結果自動更新

### 場景 3：更新學生備註

1. 進入學生詳情頁面
2. 滾動到"管理員備忘錄"區塊
3. 編輯文字框內容，例如：
   ```
   已透過校級交換生稽核，擬赴日本北海道大學交換一年。
   需要確認所修課程是否可認證為本校學分。
   ```
4. 點選"儲存備忘錄"按鈕
5. 系統提示"備忘錄已儲存"

### 場景 4：匯出學生資料

1. 進入學生列表
2. 應用所需的篩選條件（可選）
3. 點選頁面右上角"匯出 CSV"按鈕
4. 瀏覽器自動下載 `學生列表_[時間戳].csv` 檔案
5. 可用 Excel 或 Google Sheets 開啟

---

## 🔄 資料流圖

```
User
 ↓
AdminLogin.vue
 ↓ (輸入賬號密碼)
 ↓
adminStore.adminLogin()
 ↓ (登入成功)
 ↓ 設定 admin 物件
 ↓
AdminDashboard.vue
 ↓ (點選學生或"學生列表")
 ↓
StudentList.vue
 ↓ (搜尋/篩選/點選學生)
 ↓
adminStore.getStudentDetail()
 ↓ 設定 currentStudent
 ↓
StudentDetail.vue
 ↓ (編輯/儲存)
 ↓
adminStore.updateStudentNotes()
```

---

## 🛠️ 開發與擴充套件建議

### 連線真實後端 API

當前所有資料使用 Mock 資料。要連線真實 API：

```typescript
// 在 admin.ts 中替換登入方法
async function adminLogin(account: string, password: string) {
  const res = await apiClient.post('/api/admin/login', {
    account,
    password
  })
  admin.value = res.data.admin
  // 從 API 獲取學生列表
  const studentsRes = await apiClient.get('/api/students')
  students.value = studentsRes.data
  return true
}
```

### 新增分頁功能

```typescript
// 在 admin.ts 中新增
const pageSize = ref(10)
const currentPage = ref(1)

const paginatedStudents = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredStudents.value.slice(start, start + pageSize.value)
})
```

### 新增詳細報表功能

```typescript
// 生成 PDF 報告、班級對比分析等
const generateClassReport = () => {
  // 實現 PDF 生成邏輯
}
```

### 許可權管理增強

```typescript
// 區分不同管理員角色（系主任、教務管理員等）
enum AdminRole {
  SUPER_ADMIN = 'super_admin',
  DEPARTMENT_ADMIN = 'department_admin',
  ACADEMIC_ADMIN = 'academic_admin'
}
```

---

## 📚 技術棧版本

```json
{
  "vue": "^3.5.32",
  "vue-router": "^5.1.0",
  "pinia": "^3.0.4",
  "tailwindcss": "^4.3.0",
  "element-plus": "^3.x",
  "typescript": "~6.0.0"
}
```

---

## 🎯 功能清單驗收

- [x] 管理員登入介面（深色主題、視覺區隔）
- [x] 管理員儀表板（關鍵指標、預警、課程排行）
- [x] 學生列表管理（搜尋、篩選、匯出）
- [x] 學生詳細修課記錄（學分進度、修課清單、備註）
- [x] Mock 資料（5 位學生，包含特殊身份）
- [x] "數位系統" 課程 80 分示例
- [x] 完整的 TypeScript 型別定義
- [x] 響應式 RWD 設計
- [x] 中文註釋說明
- [x] Vue Router 整合與導航守衛
- [x] Element Plus 提示整合

---

## 📞 常見問題

**Q: 管理員登出後如何重新登入？**
A: 點選頁面右上角的"登出"按鈕，系統會跳轉到 `/admin/login` 登入頁面。

**Q: 可以同時登入學生端和管理員端嗎？**
A: 當前實現中，學生端和管理員端使用獨立的認證系統，可以分別登入。

**Q: Mock 資料如何修改？**
A: 編輯 `src/stores/admin.ts` 中的 `mockStudents` 陣列。

**Q: 如何新增更多學生？**
A: 在 `mockStudents` 陣列中新增新的 Student 物件，遵循現有格式即可。

---

## 📝 許可證

本專案為學分檢核系統的演示實現，遵循專案整體許可協議。

---

**最後更新**：2026-05-29  
**開發者**：Vue 3 前端工程師  
**版本**：1.0.0
