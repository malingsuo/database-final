"""
scripts/gen_seed_sql.py
從 NCCUCourse/1142.db 產生 PostgreSQL seed SQL：
  db/seed_departments.sql
  db/seed_courses.sql

執行方式：
  python scripts/gen_seed_sql.py --db /path/to/1142.db
"""
import argparse
import sqlite3
import re
from pathlib import Path

# department name 對照表（dp3 -> 正式系名）
# unit 欄位是開課限制用的縮寫，這裡用 dp3 歸納出正式名稱
# 若 dp3 沒對應就用 unit 第一個不含數字的值 fallback
DEPT_NAME_MAP = {
    "100": "文學院",
    "101": "中國文學系",
    "102": "教育學系",
    "103": "歷史學系",
    "104": "哲學系",
    "105": "企業管理學系",
    "106": "統計學系",
    "107": "經濟學系",
    "108": "國際經營與貿易學系",
    "109": "企業管理學系",
    "110": "財務管理學系",
    "111": "社會學系",
    "112": "政治學系",
    "113": "會計學系",
    "114": "會計學系",
    "115": "應用數學系",
    "116": "會計學系",
    "117": "會計學系",
    "118": "財政學系",
    "119": "法律學系",
    "120": "經濟學系",
    "121": "財政學系",
    "122": "財務管理學系",
    "123": "外交學系",
    "124": "經濟學系",
    "125": "心理學系",
    "126": "心理學系",
    "129": "經濟學系",
    "130": "資訊管理學系",
    "131": "公共行政學系",
    "200": "社會科學學院",
    "201": "政治學系",
    "202": "政治學系",
    "203": "外交學系",
    "204": "社會學系",
    "205": "財政學系",
    "206": "公共行政學系",
    "207": "地政學系",
    "208": "經濟學系",
    "209": "民族學系",
    "300": "商學院",
    "301": "國際經營與貿易學系",
    "302": "金融學系",
    "303": "會計學系",
    "304": "統計學系",
    "305": "企業管理學系",
    "306": "資訊管理學系",
    "307": "財務管理學系",
    "308": "風險管理與保險學系",
    "400": "傳播學院",
    "401": "新聞學系",
    "402": "廣告學系",
    "403": "廣播電視學系",
    "404": "傳播學院傳播碩士學位學程",
    "500": "外國語文學院",
    "501": "英國語文學系",
    "502": "阿拉伯語文學系",
    "503": "斯拉夫語文學系",
    "504": "日本語文學系",
    "505": "韓國語文學系",
    "506": "日本語文學系",
    "507": "土耳其語文學系",
    "508": "土耳其語文學系",
    "509": "歐洲語文學系",
    "600": "法學院",
    "601": "法律學系",
    "700": "理學院",
    "701": "應用數學系",
    "702": "心理學系",
    "703": "資訊科學系",
    "704": "神經科學研究所",
    "705": "應用物理研究所",
    "782": "電子物理學士學位學程",
    "783": "人工智慧應用學士學位學程",
    "800": "國際事務學院",
    "801": "外交學系",
    "802": "東亞研究所",
    "900": "教育學院",
    "901": "教育學系",
    "902": "幼兒教育研究所",
    "903": "教育政策與行政研究所",
    "904": "輔導與諮商碩士學位學程",
    "ZA0": "資訊學院",
    "Z23": "創新國際學院",
    "ZC0": "其他學程",
}

# college 對照（dp1 -> 院名）
COLLEGE_MAP = {
    "01": "政治大學（跨院通識）",
    "02": "政治大學（跨院開放）",
    "03": "體育室",
    "100": "文學院",
    "200": "社會科學學院",
    "300": "商學院",
    "400": "傳播學院",
    "500": "外國語文學院",
    "600": "法學院",
    "700": "理學院",
    "800": "國際事務學院",
    "900": "教育學院",
    "Z23": "創新國際學院",
    "ZA0": "資訊學院",
    "ZC0": "其他",
}

KIND_MAP = {
    0: "選修",
    1: "必修",
    2: "通識",
    3: "群修",
    4: "通識",
}

# ge_label bit 定義（高位到低位）
# bit5=核心 bit4=人文 bit3=社會 bit2=自然 bit1=資訊 bit0=書院
GE_BIT = {
    "核心": 1 << 5,  # 32
    "人文": 1 << 4,  # 16
    "社會": 1 << 3,  # 8
    "自然": 1 << 2,  # 4
    "資訊": 1 << 1,  # 2
    "書院": 1 << 0,  # 1
}

LMT_TO_BITS = {
    "人文通識":            GE_BIT["人文"],
    "社會通識":            GE_BIT["社會"],
    "自然通識":            GE_BIT["自然"],
    "資訊通識":            GE_BIT["資訊"],
    "書院通識":            GE_BIT["書院"],
    "中文通識":            GE_BIT["人文"],
    "外文通識":            GE_BIT["人文"],
    "跨領域(人文、社會)":        GE_BIT["人文"] | GE_BIT["社會"],
    "跨領域(人文、自然)":        GE_BIT["人文"] | GE_BIT["自然"],
    "跨領域(人文、資訊)":        GE_BIT["人文"] | GE_BIT["資訊"],
    "跨領域(社會、自然)":        GE_BIT["社會"] | GE_BIT["自然"],
    "跨領域(社會、資訊)":        GE_BIT["社會"] | GE_BIT["資訊"],
    "跨領域(自然、資訊)":        GE_BIT["自然"] | GE_BIT["資訊"],
    "跨領域(人文、社會、自然)":    GE_BIT["人文"] | GE_BIT["社會"] | GE_BIT["自然"],
    "跨領域(人文、社會、資訊)":    GE_BIT["人文"] | GE_BIT["社會"] | GE_BIT["資訊"],
    "跨領域(社會、自然、資訊)":    GE_BIT["社會"] | GE_BIT["自然"] | GE_BIT["資訊"],
}


def get_type(kind: int, lmt_kind: str) -> str:
    lmt = (lmt_kind or "").strip()
    if kind == 1:
        return "必修"
    if kind == 3:
        return "群修"
    if kind in (2, 4) or (kind == 0 and lmt):
        return "通識"
    return "選修"


def get_ge_label(kind: int, lmt_kind: str, core: int) -> int:
    """通識課才有 ge_label，非通識回傳 0"""
    lmt = (lmt_kind or "").strip()
    if kind not in (0, 2, 4):
        return 0
    if kind == 0 and not lmt:
        return 0
    bits = LMT_TO_BITS.get(lmt, 0)
    if core == 1:
        bits |= GE_BIT["核心"]
    return bits


def escape(s: str) -> str:
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="/Users/pengqize/Documents/code/NCCU-AI-SYSTEM/NCCUCourse/1142.db")
    args = parser.parse_args()

    db_path = Path(args.db)
    out_dir = Path(__file__).parent.parent / "db"
    out_dir.mkdir(exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ── 1. department ──────────────────────────────────────────────────────
    # 從 COURSE 取出所有 dp3（系代碼），搭配 dp1 推算院
    cur.execute("SELECT DISTINCT dp1, dp3, unit FROM COURSE ORDER BY dp3")
    rows = cur.fetchall()

    # dp3 → (dp1, unit_fallback)
    dept_seen: dict[str, tuple[str, str]] = {}
    for r in rows:
        dp3 = r["dp3"].strip()
        if dp3 not in dept_seen:
            dept_seen[dp3] = (r["dp1"].strip(), r["unit"].strip())

    dept_lines = []
    dept_lines.append("-- auto-generated by scripts/gen_seed_sql.py")
    dept_lines.append("-- department seed (1142 NCCU course DB)")
    dept_lines.append("")
    dept_lines.append("INSERT INTO department (id, college, name) VALUES")

    dept_values = []
    dept_id_map: dict[str, int] = {}  # dp3 -> sequential id (1-based)
    sorted_depts = sorted(dept_seen.items(), key=lambda x: x[0])
    for idx, (dp3, (dp1, unit_fallback)) in enumerate(sorted_depts, start=1):
        dept_id_map[dp3] = idx
        name = DEPT_NAME_MAP.get(dp3, unit_fallback)
        college = COLLEGE_MAP.get(dp1, dp1)
        dept_values.append(f"    ({escape(dp3)}, {escape(college)}, {escape(name)})")

    dept_lines.append(",\n".join(dept_values))
    dept_lines.append("ON CONFLICT (code) DO NOTHING;")

    dept_sql = "\n".join(dept_lines)
    (out_dir / "seed_departments.sql").write_text(dept_sql, encoding="utf-8")
    print(f"seed_departments.sql: {len(sorted_depts)} 個系所")

    # ── 2. course ──────────────────────────────────────────────────────────
    # 以 subNum（課號）+ y（學年）+ s（學期）去重，取第一筆
    cur.execute("""
        SELECT subNum, y, s, name, point, kind, lmtKind, core, dp3
        FROM COURSE
        GROUP BY subNum, y, s
        ORDER BY subNum, y, s
    """)
    course_rows = cur.fetchall()

    course_lines = []
    course_lines.append("-- auto-generated by scripts/gen_seed_sql.py")
    course_lines.append("-- course seed (1142 NCCU course DB)")
    course_lines.append("")

    # 分批 INSERT 避免單一 statement 太大
    BATCH = 500
    total = len(course_rows)
    print(f"course 總筆數: {total}")

    batches = [course_rows[i:i+BATCH] for i in range(0, total, BATCH)]
    for batch in batches:
        course_lines.append("INSERT INTO course (course_code, year, semester, name, credits, type, ge_label, department_id) VALUES")
        vals = []
        for r in batch:
            sub_num = (r["subNum"] or "").strip()
            year = r["y"]
            sem = r["s"]
            name = (r["name"] or "").strip()
            credits = float(r["point"]) if r["point"] is not None else 0.0
            kind = r["kind"] or 0
            lmt_kind = r["lmtKind"] or ""
            core = r["core"] or 0
            course_type = get_type(kind, lmt_kind)
            ge_label = get_ge_label(kind, lmt_kind, core)
            dp3 = (r["dp3"] or "").strip()
            vals.append(
                f"    ({escape(sub_num)}, {escape(year)}, {escape(sem)}, "
                f"{escape(name)}, {credits}, {escape(course_type)}, {ge_label}, {escape(dp3)})"
            )
        course_lines.append(",\n".join(vals))
        course_lines.append("ON CONFLICT (course_code, year, semester) DO NOTHING;")
        course_lines.append("")

    course_sql = "\n".join(course_lines)
    (out_dir / "seed_courses.sql").write_text(course_sql, encoding="utf-8")
    print(f"seed_courses.sql: {total} 筆課程（{len(batches)} 個 batch）")

    conn.close()
    print("完成！")


if __name__ == "__main__":
    main()
