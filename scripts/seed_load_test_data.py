#!/usr/bin/env python3
"""
灌假學生資料，供 dashboard / DB 壓測使用。

用法：
    # 預設灌 500 個學生
    python3 scripts/seed_load_test_data.py
    # 自訂數量
    python3 scripts/seed_load_test_data.py --count 2000
    # 清除所有假資料
    python3 scripts/seed_load_test_data.py --clean

設計：
- 學號 1129xxxxx（避開真實學號 112703043）
- email loadtest_stu<NNNNN>@test.local，密碼統一 "loadtest123"（壓測登入用）
- enrollment 從 course 表撈真實 703 必修/群修/選修 + 通識 + 體育，確保複合 FK 不失敗
- grade 分布：多數通過、少量 fail、少量 in_progress → 讓 dashboard difficult_courses 有資料
- advisor_status ~70% on_track / 30% at_risk → dashboard 統計有差異
- 部分學生掛雙主修(783) → fields_of_study 多型態

注意：argon2 同密碼即使 hash 字串固定，verify 仍會通過，所以所有假帳號共用同一 hash。
"""
from __future__ import annotations

import argparse
import os
import random
import sys

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    sys.exit("需要 psycopg2：uv pip install psycopg2-binary  或在 backend venv 執行")

# 固定的 argon2 hash，對應密碼 "loadtest123"（argon2 同密碼即使 hash 字串固定 verify 仍通過）
PASSWORD = "loadtest123"
PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$jhGCUIrRGgPA+J/T+j9nzA$"
    "fX2Y0RuPAeE+J3Q0Ws0peu0LFdMtUDkOHyNcxkRAG/8"
)

# 學號格式：112703xxx（112學年度入學 + 703資科系 + 流水號）
# 流水號從 101 起跳，避開真實學號 112703043；上限 899 名（101~999）
STUDENT_ID_PREFIX = "112703"      # 資科系 112 學年度
STUDENT_ID_START = 101            # 流水號起點（避開真實 043）
EMAIL_PREFIX = "loadtest_stu"
MAJOR_DEPT = "703"                # 資訊科學系
DOUBLE_MAJOR_DEPT = "783"         # AI 應用學程（部分學生）

DSN = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
    "dbname": os.environ.get("DB_NAME", "dbfinal"),
}


def fetch_course_pool(cur):
    """從 course 表撈真實課程（確保 enrollment 複合 FK 成立）。"""
    pools = {}
    for label, sql in {
        "required": "SELECT course_code, year, semester, credits FROM course WHERE department_id=%s AND type='必修'",
        "group":    "SELECT course_code, year, semester, credits FROM course WHERE department_id=%s AND type='群修'",
        "elective": "SELECT course_code, year, semester, credits FROM course WHERE department_id=%s AND type='選修'",
    }.items():
        cur.execute(sql, (MAJOR_DEPT,))
        pools[label] = cur.fetchall()
    # 通識 / 體育不分系
    cur.execute("SELECT course_code, year, semester, credits FROM course WHERE type='通識' LIMIT 400")
    pools["ge"] = cur.fetchall()
    cur.execute("SELECT course_code, year, semester, credits FROM course WHERE type='體育' LIMIT 400")
    pools["pe"] = cur.fetchall()
    for k, v in pools.items():
        if not v:
            sys.exit(f"course 表沒有 {k} 課程，請先確認 seed 已匯入")
    return pools


def make_grade(rng: random.Random) -> tuple[str | None, bool]:
    """回傳 (grade, is_passed)。分布：80% 通過、10% fail、10% in_progress。"""
    r = rng.random()
    if r < 0.80:
        return f"{rng.randint(60, 100)}.00", True
    if r < 0.90:
        return f"{rng.randint(20, 59)}.00", False        # 真正不及格
    return "成績未到或無成績", False                       # in_progress


def pick_enrollments(rng, pools, student_id):
    """為一名學生挑一組 enrollment，回傳 list[tuple]。"""
    rows = []
    seen = set()  # (course_code, year, semester) 去重，避免複合 PK 衝突

    def add(course_rows, k, req_label):
        chosen = rng.sample(course_rows, min(k, len(course_rows)))
        for code, year, sem, _credits in chosen:
            key = (code, year, sem)
            if key in seen:
                continue
            seen.add(key)
            grade, passed = make_grade(rng)
            rows.append((student_id, code, year, sem, grade, passed, req_label, None))

    add(pools["required"], rng.randint(8, 13), "必")   # 必修
    add(pools["group"],    rng.randint(2, 6),  "群")   # 群修
    add(pools["elective"], rng.randint(5, 15), "選")   # 選修
    add(pools["ge"],       rng.randint(4, 10), "選")   # 通識
    add(pools["pe"],       rng.randint(1, 4),  "必")   # 體育
    return rows


def seed(count: int, seed_val: int = 42):
    rng = random.Random(seed_val)
    conn = psycopg2.connect(**DSN)
    conn.autocommit = False
    cur = conn.cursor()

    pools = fetch_course_pool(cur)
    print(f"course pool: " + ", ".join(f"{k}={len(v)}" for k, v in pools.items()))

    accounts, students, fields, all_enroll = [], [], [], []
    import uuid
    max_n = 1000 - STUDENT_ID_START  # 學號流水號 3 碼，101~999
    if count > max_n:
        sys.exit(f"學號格式 {STUDENT_ID_PREFIX}xxx 流水號 3 碼，最多 {max_n} 名"
                 f"（{STUDENT_ID_START}~999）。如需更多請改用更長的流水號格式。")
    for i in range(count):
        seq = STUDENT_ID_START + i                # 101, 102, ...
        sid = f"{STUDENT_ID_PREFIX}{seq:03d}"     # 112703101, 112703102, ...
        acc_id = str(uuid.uuid4())
        email = f"{EMAIL_PREFIX}{seq:03d}@test.local"
        status = "at_risk" if rng.random() < 0.30 else "on_track"
        accounts.append((acc_id, email, PASSWORD_HASH, "student"))
        students.append((sid, acc_id, f"壓測生{seq:03d}", 112, status, None))
        fields.append((sid, MAJOR_DEPT, "主修", 112))
        if rng.random() < 0.25:  # 25% 掛雙主修
            fields.append((sid, DOUBLE_MAJOR_DEPT, "雙主修", 112))
        all_enroll.extend(pick_enrollments(rng, pools, sid))

    print(f"準備寫入：{len(accounts)} 帳號 / {len(students)} 學生 / "
          f"{len(fields)} fields / {len(all_enroll)} enrollment")

    execute_values(cur,
        "INSERT INTO account (id, email, password_hash, role) VALUES %s ON CONFLICT DO NOTHING",
        accounts, page_size=1000)
    execute_values(cur,
        "INSERT INTO student (student_id, user_id, name, admission_year, advisor_status, advisor_notes) "
        "VALUES %s ON CONFLICT DO NOTHING",
        students, page_size=1000)
    execute_values(cur,
        "INSERT INTO fields_of_study (student_id, department_id, program_type, enrollment_year) "
        "VALUES %s ON CONFLICT DO NOTHING",
        fields, page_size=1000)
    execute_values(cur,
        "INSERT INTO enrollment (student_id, course_code, year, semester, grade, is_passed, required_or_elective, remark) "
        "VALUES %s ON CONFLICT DO NOTHING",
        all_enroll, page_size=2000)

    conn.commit()
    # 用 email prefix 統計，避免誤計真實學生 112703043
    cur.execute(
        "SELECT count(*) FROM student s JOIN account a ON a.id=s.user_id "
        "WHERE a.email LIKE %s", (EMAIL_PREFIX + "%",))
    total = cur.fetchone()[0]
    cur.close(); conn.close()
    last_seq = STUDENT_ID_START + count - 1
    print(f"✅ 完成。目前假學生總數：{total}")
    print(f"   學號範圍：{STUDENT_ID_PREFIX}{STUDENT_ID_START:03d} .. {STUDENT_ID_PREFIX}{last_seq:03d}")
    print(f"   登入帳號：{EMAIL_PREFIX}{STUDENT_ID_START:03d}@test.local .. {EMAIL_PREFIX}{last_seq:03d}@test.local")
    print(f"   統一密碼：{PASSWORD}")


def clean():
    conn = psycopg2.connect(**DSN)
    cur = conn.cursor()
    # account ON DELETE CASCADE 會連帶刪 student/enrollment/fields/administrator
    cur.execute("DELETE FROM account WHERE email LIKE %s", (EMAIL_PREFIX + "%",))
    deleted = cur.rowcount
    conn.commit()
    cur.close(); conn.close()
    print(f"🧹 已刪除 {deleted} 個假帳號（含 cascade 的 student/enrollment/fields）")


def main():
    p = argparse.ArgumentParser(description="灌假學生資料供壓測用")
    p.add_argument("--count", type=int, default=500, help="學生數量（預設 500）")
    p.add_argument("--seed", type=int, default=42, help="random seed（可重現）")
    p.add_argument("--clean", action="store_true", help="清除所有假資料")
    args = p.parse_args()
    if args.clean:
        clean()
    else:
        seed(args.count, args.seed)


if __name__ == "__main__":
    main()
