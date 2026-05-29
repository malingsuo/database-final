# 学分检核系统 - 管理员端开发指南

## 📋 项目概览

这是一套完整的学分检核系统管理员端解决方案，采用 **Vue 3 Composition API + TypeScript + Tailwind CSS + Pinia + Element Plus** 技术栈开发。

系统包含：
- ✅ 专业化的管理员登入界面（深色主题，区隔学生端）
- ✅ 功能完整的管理员仪表板（含关键指标、预警、课程排行）
- ✅ 强大的学生列表管理（搜索、筛选、导出）
- ✅ 详尽的学生修课记录管理（含学分进度、备注、状态更新）
- ✅ 真实感十足的 Mock 数据（包含 5 位状态不同的学生）

---

## 🗂️ 文件结构

```
src/
├── stores/
│   └── admin.ts                          # Pinia 管理员数据存储（核心业务逻辑）
├── views/admin/
│   ├── AdminLogin.vue                    # 管理员登入界面
│   ├── AdminDashboard.vue                # 管理员仪表板
│   ├── StudentList.vue                   # 学生列表管理
│   └── StudentDetail.vue                 # 学生详细修课记录
├── layouts/
│   └── AdminLayout.vue                   # 管理员通用布局（可选）
├── router/
│   └── index.ts                          # ✅ 已更新路由配置
└── ... (其他既有文件)
```

---

## 🚀 快速开始

### 1. 访问管理员系统

```
http://localhost:3000/admin/login
```

### 2. 登入凭据（测试用）

| 字段 | 值 |
|------|-----|
| **账号** | admin |
| **密码** | 12345678 |

### 3. 可用路由

| 路径 | 名称 | 说明 |
|------|------|------|
| `/admin/login` | admin-login | 管理员登入 |
| `/admin/dashboard` | admin-dashboard | 管理员仪表板 |
| `/admin/student-list` | student-list | 学生列表 |
| `/admin/student/:id` | student-detail | 学生详情 |

---

## 📊 核心功能说明

### 1. 管理员登入（AdminLogin.vue）

**特点：**
- 深色渐变背景（与学生端区隔）
- 玻璃态设计（Glassmorphism）
- 响应式适配
- 集成 Element Plus 提示

**关键代码片段：**
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

### 2. 管理员仪表板（AdminDashboard.vue）

**包含内容：**

#### 📈 关键指标卡片（4 个）
- 总学生数
- 已达标学生数
- 学分落后学生数
- 系统通过率（含进度条）

#### 🚨 高风险学生预警（前 5 名）
- 显示学分进度条
- 支持点击跳转到学生详情
- 管理员备注可见

#### 👹 魔王课程排行（TOP 3）
- 课程未通过率统计
- 挂科人数展示
- 排名奖章（金银铜）

#### ⚡ 快速操作面板
- 快速链接到学生列表
- 导出学生数据按钮
- 系统设置入口

---

### 3. 学生列表管理（StudentList.vue）

**核心功能：**

#### 🔍 搜索
```typescript
// 支持按学号或姓名搜索
adminStore.searchQuery = 'S001'  // 或 '林子晴'
```

#### 🎯 筛选
```typescript
// 支持按年级筛选
adminStore.filterYear = 2021  // 或 2022, 2023, 2024

// 支持按状态筛选
adminStore.filterStatus = 'at_risk'  // 或 'on_track', 'all'
```

#### 📥 导出 CSV
```typescript
adminStore.exportStudentsAsCSV()
// 自动下载包含学号、姓名、入学年度、状态等数据的 CSV 文件
```

**卡片展示信息：**
- 学生基本信息（姓名、学号、年级）
- 修课状态徽章（已达标/落后）
- 特殊身份标签（双主修、交换生）
- 学分进度条（可视化比例）
- 课程统计（已修/挂科数）
- 管理员备注预览

---

### 4. 学生详细修课记录（StudentDetail.vue）

**包含三大主区块：**

#### 📋 基本信息区
- 姓名、学号、年级、入学年度
- 特殊身份（双主修、交换生预审）
- 学分统计（总学分、已修学分、必需学分、完成度）

#### 📊 学分分类进度
四类学分进度条展示：
- 系必修课程：40 分
- 校必修课程：30 分
- 选修课程：30 分
- 通识课程：20 分

**每个进度条显示：**
- 已完成学分 / 目标学分
- 完成百分比
- 彩色渐变填充

#### 📝 修课清单表格
| 课程名称 | 类别 | 学分 | 学年学期 | 成绩 | 状态 |
|---------|------|------|---------|------|------|
| 数位系统 | 系必修 | 3 | 2024/1 | 80 | ✓ 通过 |
| 微积分 | 校必修 | 3 | 2023/1 | 52 | ✗ 挂科 |

**成绩着色：**
- 绿色：通过且成绩 ≥ 80
- 橙色：通过但成绩 < 80
- 红色：挂科（未通过）

#### 📌 管理员备忘录
- 文字区域供管理员记录：
  - 特殊抵免状况
  - 行政备注
  - 学业指导建议
  - 交换认可等特殊情况

#### ⚙️ 学生状态管理
- 按钮快速更新学生状态（已达标 ↔ 学分落后）

---

## 💾 Mock 数据详解

### 包含的 5 位测试学生

| 学号 | 姓名 | 年级 | 状态 | 特殊身份 | 用途 |
|------|------|------|------|---------|------|
| S001 | 林子晴 | 3年 | 已达标 | 双主修 | 优秀学生示例 |
| S002 | 王浩宇 | 2年 | 落后 | 无 | 预警学生示例 |
| S003 | 陈思语 | 3年 | 已达标 | 交换生 | 特殊身份示例 |
| S004 | 许家豪 | 2年 | 落后 | 无 | 高风险学生 |
| S005 | 黄诗涵 | 4年 | 已达标 | 无 | 即将离校学生 |

### 关键课程数据

**必须包含的测试课程：**
```javascript
{
  course_id: 'CS101',
  course_name: '数位系统',      // ← 题目要求
  grade: 80,                      // ← 题目要求
  is_passed: true
}
```

此课程出现在林子晴（S001）的修课记录中。

---

## 🎨 设计特点

### 颜色方案

**管理员登入界面（深色系）**
- 背景：`from-slate-900 via-slate-800 to-slate-900`
- 强调色：`blue-500` 到 `purple-600` 的渐变

**管理员仪表板（亮色系）**
- 背景：`slate-50`
- 卡片：`white` 配 `border-slate-200`

### 响应式设计

```
Mobile-First 断点：
- sm: ≥ 640px   (md)
- md: ≥ 768px   (表格、双列)
- lg: ≥ 1024px  (完整三列布局)
- max-width: 7xl (1280px)
```

---

## 🔌 Pinia Store API 参考

### 状态（State）

```typescript
// 管理员用户信息
admin: AdminUser | null

// 学生列表
students: Student[]

// 当前选中的学生
currentStudent: Student | null

// 搜索与筛选条件
searchQuery: string
filterYear: number | null
filterStatus: 'all' | 'on_track' | 'at_risk'
```

### 计算属性（Computed）

```typescript
// 仪表板统计数据
dashboardStats: {
  total_students: number
  on_track_students: number
  at_risk_students: number
  pass_rate: number
}

// 高风险学生列表（前 5 名）
riskStudents: Student[]

// 魔王课程排行（未通过率最高的 TOP 3）
difficultCourses: Array<{
  name: string
  total: number
  failed: number
  failRate: number
}>

// 过滤后的学生列表
filteredStudents: Student[]
```

### 方法（Actions）

```typescript
// 管理员登入
adminLogin(account: string, password: string): boolean

// 管理员登出
adminLogout(): void

// 获取学生详情
getStudentDetail(studentId: string): Student | undefined

// 更新学生备注
updateStudentNotes(studentId: string, notes: string): void

// 更新学生状态
updateStudentStatus(
  studentId: string, 
  status: 'on_track' | 'at_risk'
): void

// 导出学生列表为 CSV
exportStudentsAsCSV(): void
```

---

## 📱 使用场景演示

### 场景 1：查看高风险学生

1. 登入管理员系统 (`/admin/login`)
2. 进入仪表板 (`/admin/dashboard`)
3. 在"高风险学生预警"区块中点击任何学生
4. 自动跳转到该生的详细修课记录
5. 查看学分进度、修课清单、特殊备注

### 场景 2：搜索与筛选学生

1. 点击"学生列表管理"
2. 在搜索框输入：
   - 学号：`S002`
   - 姓名：`王浩宇`
3. 从"年级筛选"选择 `2022 入学`
4. 从"状态筛选"选择 `学分落后`
5. 结果自动更新

### 场景 3：更新学生备注

1. 进入学生详情页面
2. 滚动到"管理员备忘录"区块
3. 编辑文本框内容，例如：
   ```
   已通过校级交换生审核，拟赴日本北海道大学交换一年。
   需要确认所修课程是否可认证为本校学分。
   ```
4. 点击"保存备忘录"按钮
5. 系统提示"备忘录已保存"

### 场景 4：导出学生数据

1. 进入学生列表
2. 应用所需的筛选条件（可选）
3. 点击页面右上角"导出 CSV"按钮
4. 浏览器自动下载 `学生列表_[时间戳].csv` 文件
5. 可用 Excel 或 Google Sheets 打开

---

## 🔄 数据流图

```
User
 ↓
AdminLogin.vue
 ↓ (输入账号密码)
 ↓
adminStore.adminLogin()
 ↓ (登入成功)
 ↓ 设置 admin 对象
 ↓
AdminDashboard.vue
 ↓ (点击学生或"学生列表")
 ↓
StudentList.vue
 ↓ (搜索/筛选/点击学生)
 ↓
adminStore.getStudentDetail()
 ↓ 设置 currentStudent
 ↓
StudentDetail.vue
 ↓ (编辑/保存)
 ↓
adminStore.updateStudentNotes()
```

---

## 🛠️ 开发与扩展建议

### 连接真实后端 API

当前所有数据使用 Mock 数据。要连接真实 API：

```typescript
// 在 admin.ts 中替换登入方法
async function adminLogin(account: string, password: string) {
  const res = await apiClient.post('/api/admin/login', {
    account,
    password
  })
  admin.value = res.data.admin
  // 从 API 获取学生列表
  const studentsRes = await apiClient.get('/api/students')
  students.value = studentsRes.data
  return true
}
```

### 添加分页功能

```typescript
// 在 admin.ts 中添加
const pageSize = ref(10)
const currentPage = ref(1)

const paginatedStudents = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredStudents.value.slice(start, start + pageSize.value)
})
```

### 添加详细报表功能

```typescript
// 生成 PDF 报告、班级对比分析等
const generateClassReport = () => {
  // 实现 PDF 生成逻辑
}
```

### 权限管理增强

```typescript
// 区分不同管理员角色（系主任、教务管理员等）
enum AdminRole {
  SUPER_ADMIN = 'super_admin',
  DEPARTMENT_ADMIN = 'department_admin',
  ACADEMIC_ADMIN = 'academic_admin'
}
```

---

## 📚 技术栈版本

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

## 🎯 功能清单验收

- [x] 管理员登入界面（深色主题、视觉区隔）
- [x] 管理员仪表板（关键指标、预警、课程排行）
- [x] 学生列表管理（搜索、筛选、导出）
- [x] 学生详细修课记录（学分进度、修课清单、备注）
- [x] Mock 数据（5 位学生，包含特殊身份）
- [x] "数位系统" 课程 80 分示例
- [x] 完整的 TypeScript 类型定义
- [x] 响应式 RWD 设计
- [x] 中文注释说明
- [x] Vue Router 集成与导航守卫
- [x] Element Plus 提示集成

---

## 📞 常见问题

**Q: 管理员登出后如何重新登入？**
A: 点击页面右上角的"登出"按钮，系统会跳转到 `/admin/login` 登入页面。

**Q: 可以同时登入学生端和管理员端吗？**
A: 当前实现中，学生端和管理员端使用独立的认证系统，可以分别登入。

**Q: Mock 数据如何修改？**
A: 编辑 `src/stores/admin.ts` 中的 `mockStudents` 数组。

**Q: 如何添加更多学生？**
A: 在 `mockStudents` 数组中添加新的 Student 对象，遵循现有格式即可。

---

## 📝 许可证

本项目为学分检核系统的演示实现，遵循项目整体许可协议。

---

**最后更新**：2026-05-29  
**开发者**：Vue 3 前端工程师  
**版本**：1.0.0
