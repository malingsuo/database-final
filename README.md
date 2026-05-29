# Database Final

> ERD 圖待更新，需修改專案：
> - `account.id` 改為 UUID（原為 SERIAL）
> - `account.account` 欄位改為 `email`
> - `course.id` 移除，改為複合 PK `(course_code, year, semester)`
> - `course` 新增 `ge_label`（SMALLINT 8-bit 通識標籤），移除 `group_label`；`type` 值域改為：必修 / 群修 / 選修 / 通識 / 體育
> - `token` 表移除（auth 由 JWT 處理）
> - `administrator.id` 直接使用 `account.id`（UUID FK）
> - `enrollment` 的 `course_id` 改為複合 FK `(course_code, year, semester)`

[<img height="630" alt="erd" src="https://github.com/user-attachments/assets/ecefae3c-964a-4e3a-abbe-5c32998f1406" />](https://app.diagrams.net/#Uhttps%3A%2F%2Fgithub.com%2Fmalingsuo%2Fdatabase-final%2Freleases%2Fdownload%2Fresource%2Ferd.drawio)

<details>
<summary>ER to DB</summary>

<p>
<strong>Step 1:</strong> 將所有一般Entity types轉換為Table<br>
    account(<ins>id</ins>, email, password, role)<br>
    administrator(<ins>id</ins>)<br>
    student(<ins>student_id</ins>, name, admission_year)<br>
    department(<ins>id</ins>, college, name)<br>
    course(<ins>course_code</ins>, <ins>year</ins>, <ins>semester</ins>, name, credits, type, ge_label)<br>
</p>
<p>
<strong>Step 4:</strong> 處理1:1 Relationship Types<br>
    account(<ins>id</ins>, email, password, role)<br>
    administrator(<ins>id</ins>, <span style="color:red">department_id (FK), user_id (FK)</span>)<br>
    student(<ins>student_id</ins>, name, admission_year, <span style="color:red">user_id (FK)</span>)<br>
    department(<ins>id</ins>, college, name)<br>
    course(<ins>course_code</ins>, <ins>year</ins>, <ins>semester</ins>, name, credits, type, ge_label)<br>
</p>
<p>
<strong>Step 5:</strong> 處理1:N Relationship Types<br>
    account(<ins>id</ins>, email, password, role)<br>
    administrator(<ins>id</ins>, department_id (FK), user_id (FK))<br>
    student(<ins>student_id</ins>, name, admission_year, user_id (FK))<br>
    department(<ins>id</ins>, college, name)<br>
    course(<ins>course_code</ins>, <ins>year</ins>, <ins>semester</ins>, name, credits, type, ge_label, <span style="color:red">department_id (FK)</span>)<br>
</p>
<p>
<strong>Step 6:</strong> 處理M:N Relationship Types<br>
    account(<ins>id</ins>, email, password, role)<br>
    administrator(<ins>id</ins>, department_id (FK), user_id (FK))<br>
    student(<ins>student_id</ins>, name, admission_year, user_id (FK))<br>
    department(<ins>id</ins>, college, name)<br>
    course(<ins>course_code</ins>, <ins>year</ins>, <ins>semester</ins>, name, credits, type, ge_label, department_id (FK))<br>
    <span style="color:red">enrollment(<ins>student_id</ins>, <ins>course_code</ins>, <ins>year</ins>, <ins>semester</ins>, grade, is_passed, required_or_elective, remark)</span><br>
    <span style="color:red">fields_of_study(<ins>student_id</ins>, <ins>department_id</ins>, program_type, enrollment_year)</span><br>
</p>
</details>

### DB Schema

account(<ins>id</ins>, email, password_hash, role, created_at) \
administrator(<ins>id</ins>, department_id (FK)) \
student(<ins>student_id</ins>, name, admission_year, user_id (FK)) \
department(<ins>id</ins>, college, name) \
course(<ins>course_code</ins>, <ins>year</ins>, <ins>semester</ins>, name, credits, type, ge_label, department_id (FK)) \
enrollment(<ins>student_id</ins>, <ins>course_code</ins>, <ins>year</ins>, <ins>semester</ins>, grade, is_passed, required_or_elective, remark) \
fields_of_study(<ins>student_id</ins>, <ins>department_id</ins>, program_type, enrollment_year)

---

### ge_label 說明

`course.ge_label` 為 SMALLINT，以 8-bit bitmask 紀錄通識課的類別，**僅 `type='通識'` 時有非零值，其餘 type 皆為 0**。

**`course.type` 值域：**

| type | 說明 |
|------|------|
| 必修 | 系所必修課 |
| 群修 | 系所群修課 |
| 選修 | 一般選修（含各系開放外系修） |
| 通識 | 各類通識，細分見 ge_label |
| 體育 | 體育室開課必修 |

**ge_label bit 定義（8-bit，僅 type='通識' 有效）：**

| bit | 值 | 類別 |
|-----|----|------|
| bit7 | 128 | 核心通識 |
| bit6 | 64  | 人文通識 |
| bit5 | 32  | 社會通識 |
| bit4 | 16  | 自然通識 |
| bit3 | 8   | 資訊通識 |
| bit2 | 4   | 書院通識 |
| bit1 | 2   | 外文通識 |
| bit0 | 1   | 中文通識 |

**範例：**

| lmtKind | core | ge_label | 二進位 |
|---------|------|----------|--------|
| 中文通識 | 0 | 1   | 00000001 |
| 外文通識 | 0 | 2   | 00000010 |
| 書院通識 | 0 | 4   | 00000100 |
| 資訊通識 | 0 | 8   | 00001000 |
| 自然通識 | 0 | 16  | 00010000 |
| 社會通識 | 0 | 32  | 00100000 |
| 人文通識 | 0 | 64  | 01000000 |
| 人文通識（核心）| 1 | 192 | 11000000 |
| 社會通識（核心）| 1 | 160 | 10100000 |
| 跨領域(人文、社會) | 0 | 96  | 01100000 |
| 跨領域(人文、自然) | 0 | 80  | 01010000 |
| 跨領域(社會、自然) | 0 | 48  | 00110000 |
| 跨領域(人文、社會、自然) | 0 | 112 | 01110000 |

**SQL 查詢範例：**

```sql
-- 查人文通識（含跨領域有人文的）
WHERE type = '通識' AND (ge_label & 64) > 0

-- 查核心通識
WHERE type = '通識' AND (ge_label & 128) > 0

-- 查中文通識
WHERE type = '通識' AND (ge_label & 1) > 0

-- 查外文通識
WHERE type = '通識' AND (ge_label & 2) > 0

-- 查書院通識
WHERE type = '通識' AND (ge_label & 4) > 0

-- 查體育
WHERE type = '體育'
```
