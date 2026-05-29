"""
src/services/checker.py - 畢業學分檢核核心邏輯

畢業規定從 JSON 檔載入（不查 DB）。
DB 只存學生資料（student, student_course）。

JSON 規定目錄：data/（repo 根目錄）
  graduation_requirements/<entry_year>/<key>.json    主系規定
  double_major_requirements/<entry_year>/<key>.json  雙主修規定
  minor_requirements/<entry_year>/<key>.json         輔系規定

主要入口：check_graduation(session, student_id) → dict
"""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Student, StudentCourse

# ---------------------------------------------------------------------------
# JSON 規定載入
# 路徑：backend/src/services/checker.py → 往上 4 層 → repo 根 → data/
# ---------------------------------------------------------------------------
_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


@lru_cache(maxsize=None)
def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _find_rules(kind: str, entry_year: int, dept_name: str) -> dict | None:
    dir_path = _DATA_DIR / f"{kind}_requirements" / str(entry_year)
    if not dir_path.exists():
        return None
    for f in sorted(dir_path.glob("*.json")):
        if f.name.startswith("_"):
            continue
        data = _load_json(f)
        if not isinstance(data, dict):
            continue
        name = data.get("dept_name", "")
        if name == dept_name or dept_name in name or name in dept_name:
            return data
    return None


def _find_double_major_rules(entry_year: int, dm_name: str, is_cs: bool) -> dict | None:
    dir_path = _DATA_DIR / "double_major_requirements" / str(entry_year)
    if not dir_path.exists():
        return None

    # AI 學程：優先找 variant 檔
    for f in sorted(dir_path.glob("783_*.json")):
        data = _load_json(f)
        if not isinstance(data, dict):
            continue
        name = data.get("dept_name") or data.get("program_name", "")
        if dm_name not in name and name not in dm_name:
            if "AI" not in name and "人工智慧" not in dm_name:
                continue
        variant = data.get("variant", "")
        if is_cs and variant == "cs":
            return data
        if not is_cs and variant == "non_cs":
            return data

    # 一般雙主修
    for f in sorted(dir_path.glob("*.json")):
        if f.name.startswith("_") or "783_" in f.name:
            continue
        data = _load_json(f)
        if not isinstance(data, dict):
            continue
        name = data.get("dept_name", "")
        if name == dm_name or dm_name in name or name in dm_name:
            return data
    return None


def _load_ge_rules(entry_year: int) -> list[dict]:
    p = _DATA_DIR / "graduation_requirements" / str(entry_year) / "ge_requirements.json"
    data = _load_json(p)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("categories", [])
    return []


# ---------------------------------------------------------------------------
# 工具：成績狀態
# ---------------------------------------------------------------------------

def _score_status(score: str | None) -> str:
    if score is None or str(score).strip() == "":
        return "in_progress"
    s = str(score).strip()
    if s == "通過":
        return "passed"
    if s == "成績未到或無成績":
        return "in_progress"
    try:
        val = float(s)
        return "passed" if val >= 60 else "failed"
    except ValueError:
        return "failed"


# ---------------------------------------------------------------------------
# 工具：課程比對
# ---------------------------------------------------------------------------

_FULLWIDTH_TO_HALF = str.maketrans(
    "".join(chr(0xFF01 + i) for i in range(94)),
    "".join(chr(0x21 + i) for i in range(94)),
)


def _normalize_name(name: str) -> str:
    s = (name or "").strip()
    s = s.translate(_FULLWIDTH_TO_HALF)
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"（[^）]*）", "", s)
    s = re.sub(r"\s+", "", s)
    return s.strip()


def _build_sc_by_code(student_courses: Sequence[StudentCourse]) -> dict:
    result = {}
    for sc in student_courses:
        code = (sc.course_code or "").strip()
        if code and code not in result:
            result[code] = sc
    return result


def _match_course(
    rule_code: str | None,
    rule_name: str,
    sc_by_code: dict,
    student_courses: Sequence[StudentCourse],
) -> tuple:
    code = (rule_code or "").strip()
    if code and code in sc_by_code:
        return sc_by_code[code], "exact"

    rule_norm = _normalize_name(rule_name)
    best_sc = None
    best_ratio = 0.0

    for sc in student_courses:
        sc_norm = _normalize_name(sc.course_name)
        if rule_norm and (rule_norm in sc_norm or sc_norm in rule_norm):
            return sc, "normalized"
        if rule_norm and sc_norm:
            ratio = difflib.SequenceMatcher(None, rule_norm, sc_norm).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_sc = sc

    if best_ratio >= 0.85:
        return best_sc, "fuzzy"
    return None, "none"


# ---------------------------------------------------------------------------
# 工具：群修分組門數驗證
# ---------------------------------------------------------------------------

def _check_group_rules(
    group_rules: dict | None,
    passed_courses: list,
    in_progress_courses: list,
) -> list[dict]:
    if not group_rules or not isinstance(group_rules, dict):
        return []

    violations = []
    group_passed: dict[str, int] = {}
    group_in_prog: dict[str, int] = {}
    for c in passed_courses:
        gl = c.get("group_label")
        if gl:
            group_passed[gl] = group_passed.get(gl, 0) + 1
    for c in in_progress_courses:
        gl = c.get("group_label")
        if gl:
            group_in_prog[gl] = group_in_prog.get(gl, 0) + 1

    for grp, rule in group_rules.items():
        if grp == "_shared":
            shared_groups: list[str] = rule.get("groups", [])
            min_total: int = rule.get("min_total_courses", 0)
            unique_groups: bool = rule.get("unique_groups", False)
            if unique_groups:
                total_passed = sum(1 for g in shared_groups if group_passed.get(g, 0) > 0)
                total_in_prog = sum(1 for g in shared_groups if group_in_prog.get(g, 0) > 0)
            else:
                total_passed = sum(group_passed.get(g, 0) for g in shared_groups)
                total_in_prog = sum(group_in_prog.get(g, 0) for g in shared_groups)

            if total_passed < min_total:
                violations.append({
                    "group": "_shared(" + "+".join(shared_groups) + ")",
                    "min_courses": min_total,
                    "passed_courses": total_passed,
                    "in_progress_courses": total_in_prog,
                    "note": rule.get("note", ""),
                    "status": "incomplete",
                })
            continue

        min_c = rule.get("min_courses")
        if min_c is None:
            continue
        passed_cnt = group_passed.get(grp, 0)
        in_prog_cnt = group_in_prog.get(grp, 0)
        if passed_cnt < min_c:
            violations.append({
                "group": grp,
                "min_courses": min_c,
                "passed_courses": passed_cnt,
                "in_progress_courses": in_prog_cnt,
                "note": rule.get("note", ""),
                "status": "incomplete",
            })
    return violations


# ---------------------------------------------------------------------------
# 工具：從 JSON 規定課表跑比對（主系 / 雙主修 / 輔系共用核心）
# ---------------------------------------------------------------------------

def _match_courses_from_rules(
    rule_courses: list[dict],
    student_courses: Sequence[StudentCourse],
    sc_by_code: dict,
    alt_code_key: str | None = None,
) -> tuple[list, list, list, float, float]:
    passed, in_progress, missing = [], [], []
    earned = 0.0
    in_prog_credits = 0.0

    for dc in rule_courses:
        rule_name = dc.get("name", "")
        rule_code = dc.get("course_code_required") or dc.get("code") or ""
        group_label = dc.get("group_label") or dc.get("type")
        cred = float(dc.get("credits", 0) or 0)

        alt_code = dc.get(alt_code_key, "") if alt_code_key else ""

        matched, confidence = None, "none"
        if alt_code and alt_code in sc_by_code:
            matched, confidence = sc_by_code[alt_code], "exact"
        else:
            matched, confidence = _match_course(rule_code, rule_name, sc_by_code, student_courses)

        if matched is None:
            missing.append({
                "course_name": rule_name,
                "course_code": alt_code or rule_code,
                "course_type": dc.get("type"),
                "group_label": group_label,
                "credits": cred,
                "match_confidence": "none",
            })
        else:
            status = _score_status(matched.score)
            entry = {
                "course_name": matched.course_name,
                "course_code": matched.course_code,
                "credits": float(matched.credit),
                "score": matched.score,
                "group_label": group_label,
                "match_confidence": confidence,
            }
            if status == "passed":
                earned += cred
                passed.append(entry)
            elif status == "in_progress":
                in_prog_credits += cred
                in_progress.append(entry)
            else:
                missing.append({
                    "course_name": rule_name,
                    "course_code": alt_code or rule_code,
                    "course_type": dc.get("type"),
                    "group_label": group_label,
                    "credits": cred,
                    "score": matched.score,
                    "note": "成績不通過",
                    "match_confidence": confidence,
                })

    return passed, in_progress, missing, earned, in_prog_credits


# ---------------------------------------------------------------------------
# check_major
# ---------------------------------------------------------------------------

def check_major(session: Session, student: Student) -> dict:
    rules = _find_rules("graduation", student.entry_year, student.register_major)
    if rules is None:
        return _not_found_result(student.register_major)

    all_courses = rules.get("courses", [])
    rule_courses = [c for c in all_courses if c.get("type") in ("必修", "群修")]

    if not rule_courses and rules.get("total_credits_required") is None:
        return _no_data_result(rules.get("dept_name", student.register_major))

    student_courses = (
        session.execute(select(StudentCourse).where(StudentCourse.student_id == student.id))
        .scalars()
        .all()
    )
    sc_by_code = _build_sc_by_code(student_courses)

    passed, in_progress, missing, earned, in_prog_credits = _match_courses_from_rules(
        rule_courses, student_courses, sc_by_code
    )

    total_req = rules.get("total_credits_required")
    if total_req is None and rule_courses:
        total_req = round(sum(float(c.get("credits", 0) or 0) for c in rule_courses), 1)
    missing_credits = max(0.0, float(total_req) - earned) if total_req is not None else None

    group_rules = rules.get("group_rules")
    group_violations = _check_group_rules(group_rules, passed, in_progress)

    return {
        "dept_name": rules.get("dept_name", student.register_major),
        "found": True,
        "total_credits_required": total_req,
        "earned_credits": round(earned, 1),
        "in_progress_credits": round(in_prog_credits, 1),
        "missing_credits": round(missing_credits, 1) if missing_credits is not None else None,
        "passed_courses": passed,
        "in_progress_courses": in_progress,
        "missing_courses": missing,
        "group_violations": group_violations,
        "status": "complete"
        if (missing_credits is not None and missing_credits == 0 and not group_violations)
        else "incomplete",
    }


# ---------------------------------------------------------------------------
# check_double_major
# ---------------------------------------------------------------------------

def check_double_major(session: Session, student: Student) -> dict | None:
    if not student.register_double_major:
        return None

    dm_name = student.register_double_major.strip()
    is_cs = "資訊科學" in (student.register_major or "")

    rules = _find_double_major_rules(student.entry_year, dm_name, is_cs)
    if rules is None:
        result = _not_found_result(dm_name)
        result["type"] = "double_major"
        return result

    all_courses = rules.get("courses", [])
    if not all_courses and "categories" in rules:
        for cat in rules["categories"]:
            for c in cat.get("courses", []):
                c.setdefault("group_label", cat.get("name"))
            all_courses.extend(cat.get("courses", []))

    rule_courses = [c for c in all_courses if c.get("type") in ("必修", "群修")]

    student_courses = (
        session.execute(select(StudentCourse).where(StudentCourse.student_id == student.id))
        .scalars()
        .all()
    )
    sc_by_code = _build_sc_by_code(student_courses)

    passed, in_progress, missing, earned, in_prog_credits = _match_courses_from_rules(
        rule_courses, student_courses, sc_by_code, alt_code_key="double_major_course_code"
    )

    total_req = rules.get("total_credits_required")
    missing_credits = max(0.0, float(total_req) - earned) if total_req is not None else None

    group_checks: list[dict] = []
    group_incomplete: list[str] = []
    if "categories" in rules:
        earned_by_group: dict[str, float] = {}
        for c in passed:
            lbl = c.get("group_label") or ""
            if lbl:
                earned_by_group[lbl] = earned_by_group.get(lbl, 0.0) + c["credits"]
        for cat in rules["categories"]:
            req_c = float(cat.get("credits_required", 0) or 0)
            if req_c == 0:
                continue
            grp = cat["name"]
            earned_c = earned_by_group.get(grp, 0.0)
            complete = earned_c >= req_c
            if not complete:
                group_incomplete.append(grp)
            group_checks.append({
                "group": grp,
                "credits_required": req_c,
                "earned_credits": round(earned_c, 1),
                "missing_credits": round(max(0.0, req_c - earned_c), 1),
                "status": "complete" if complete else "incomplete",
            })

    overall_complete = (
        missing_credits is not None and missing_credits == 0 and not group_incomplete
    )

    return {
        "dept_name": rules.get("dept_name") or rules.get("program_name", dm_name),
        "type": "double_major",
        "found": True,
        "total_credits_required": total_req,
        "earned_credits": round(earned, 1),
        "in_progress_credits": round(in_prog_credits, 1),
        "missing_credits": round(missing_credits, 1) if missing_credits is not None else None,
        "group_checks": group_checks,
        "passed_courses": passed,
        "in_progress_courses": in_progress,
        "missing_courses": missing,
        "status": "complete" if overall_complete else "incomplete",
    }


# ---------------------------------------------------------------------------
# check_minor
# ---------------------------------------------------------------------------

def check_minor(session: Session, student: Student, minor_name: str) -> dict:
    rules = _find_rules("minor", student.entry_year, minor_name)
    if rules is None:
        return _not_found_result(minor_name)

    rule_courses = rules.get("courses", [])
    student_courses = (
        session.execute(select(StudentCourse).where(StudentCourse.student_id == student.id))
        .scalars()
        .all()
    )
    sc_by_code = _build_sc_by_code(student_courses)

    passed, in_progress, missing, earned, in_prog_credits = _match_courses_from_rules(
        rule_courses, student_courses, sc_by_code
    )

    total_req = rules.get("total_credits_required")
    missing_credits = max(0.0, float(total_req) - earned) if total_req is not None else None

    return {
        "dept_name": rules.get("dept_name", minor_name),
        "found": True,
        "total_credits_required": total_req,
        "earned_credits": round(earned, 1),
        "in_progress_credits": round(in_prog_credits, 1),
        "missing_credits": round(missing_credits, 1) if missing_credits is not None else None,
        "passed_courses": passed,
        "in_progress_courses": in_progress,
        "missing_courses": missing,
        "status": "complete"
        if (missing_credits is not None and missing_credits == 0)
        else "incomplete",
    }


# ---------------------------------------------------------------------------
# check_ge
# ---------------------------------------------------------------------------

def check_ge(session: Session, student: Student) -> dict:
    ge_categories = _load_ge_rules(student.entry_year)

    student_courses = (
        session.execute(select(StudentCourse).where(StudentCourse.student_id == student.id))
        .scalars()
        .all()
    )

    remark_credits: dict[str, float] = {}
    remark_courses: dict[str, list] = {}
    for sc in student_courses:
        remark = (sc.remark or "").strip()
        if not remark:
            continue
        if _score_status(sc.score) != "passed":
            continue
        cred = float(sc.credit or 0)
        remark_credits[remark] = remark_credits.get(remark, 0.0) + cred
        remark_courses.setdefault(remark, []).append({
            "course_name": sc.course_name,
            "course_code": sc.course_code,
            "credits": cred,
            "score": sc.score,
            "remark": remark,
        })

    category_results = []
    all_complete = True

    for cat in ge_categories:
        rc = (cat.get("remark_code") or "").strip()
        required = cat.get("credits_required", 0)
        earned = remark_credits.get(rc, 0.0)
        complete = earned >= required
        if not complete:
            all_complete = False
        category_results.append({
            "category_name": cat.get("category_name", rc),
            "remark_code": rc,
            "credits_required": required,
            "earned_credits": round(earned, 1),
            "missing_credits": round(max(0.0, required - earned), 1),
            "courses": remark_courses.get(rc, []),
            "status": "complete" if complete else "incomplete",
        })

    if not ge_categories:
        all_complete = False

    return {
        "categories": category_results,
        "status": "complete" if all_complete else "incomplete",
    }


# ---------------------------------------------------------------------------
# check_pe
# ---------------------------------------------------------------------------

def check_pe(session: Session, student: Student) -> dict:
    pe_courses = (
        session.execute(
            select(StudentCourse).where(
                StudentCourse.student_id == student.id,
                StudentCourse.course_name.like("%體育%"),
                StudentCourse.required_or_elective == "必",
            )
        )
        .scalars()
        .all()
    )

    passed, in_progress, failed = [], [], []
    for sc in pe_courses:
        status = _score_status(sc.score)
        entry = {
            "course_name": sc.course_name,
            "course_code": sc.course_code,
            "academic_year_semester": sc.academic_year_semester,
            "score": sc.score,
        }
        if status == "passed":
            passed.append(entry)
        elif status == "in_progress":
            in_progress.append(entry)
        else:
            failed.append(entry)

    REQUIRED = 4
    passed_count = len(passed)
    missing_count = max(0, REQUIRED - passed_count)

    return {
        "required_semesters": REQUIRED,
        "passed_semesters": passed_count,
        "missing_semesters": missing_count,
        "passed_courses": passed,
        "in_progress_courses": in_progress,
        "failed_courses": failed,
        "status": "complete" if missing_count == 0 else "incomplete",
    }


# ---------------------------------------------------------------------------
# 輔助函式
# ---------------------------------------------------------------------------

def _not_found_result(dept_name: str) -> dict:
    return {
        "dept_name": dept_name,
        "found": False,
        "no_data": False,
        "total_credits_required": None,
        "earned_credits": 0,
        "in_progress_credits": 0,
        "missing_credits": None,
        "passed_courses": [],
        "in_progress_courses": [],
        "missing_courses": [],
        "status": "dept_not_found",
        "note": None,
    }


def _no_data_result(dept_name: str) -> dict:
    return {
        "dept_name": dept_name,
        "found": True,
        "no_data": True,
        "total_credits_required": None,
        "earned_credits": 0,
        "in_progress_credits": 0,
        "missing_credits": None,
        "passed_courses": [],
        "in_progress_courses": [],
        "missing_courses": [],
        "status": "no_data",
        "note": "此系畢業規定暫無資料，請洽教務處確認畢業學分規定。",
    }


# ---------------------------------------------------------------------------
# check_graduation — 主入口
# ---------------------------------------------------------------------------

GRADUATION_TOTAL_CREDITS = 128
GE_REQUIRED_CREDITS = 28
PE_REQUIRED_CREDITS = 4


def _calc_elective_gap(
    student: Student,
    major_result: dict,
    ge_result: dict,
    pe_result: dict,
) -> dict:
    TOTAL = GRADUATION_TOTAL_CREDITS
    major_required = major_result.get("total_credits_required") or 0
    major_earned = major_result.get("earned_credits") or 0.0

    ge_earned = sum(cat.get("earned_credits", 0.0) for cat in ge_result.get("categories", []))
    ge_earned = min(ge_earned, float(GE_REQUIRED_CREDITS))

    pe_passed = len(pe_result.get("passed_courses", []))
    pe_earned = float(min(pe_passed, PE_REQUIRED_CREDITS))

    elective_required = max(0, TOTAL - major_required - GE_REQUIRED_CREDITS - PE_REQUIRED_CREDITS)
    total_earned = float(student.total_credits or 0)
    elective_earned = max(0.0, total_earned - major_earned - ge_earned - pe_earned)
    elective_gap = max(0.0, elective_required - elective_earned)

    note = (
        f"選修應修 = {TOTAL} - 主系{major_required} - 通識{GE_REQUIRED_CREDITS}"
        f" - 體育{PE_REQUIRED_CREDITS} = {elective_required} 學分"
    )
    if major_result.get("found") is False or major_result.get("no_data"):
        note += "（主系資料不完整，選修缺口為估算值）"

    return {
        "graduation_total": TOTAL,
        "major_required": major_required,
        "ge_required": GE_REQUIRED_CREDITS,
        "pe_required": PE_REQUIRED_CREDITS,
        "elective_required": elective_required,
        "total_credits_earned": round(total_earned, 1),
        "major_earned": round(major_earned, 1),
        "ge_earned": round(ge_earned, 1),
        "pe_earned": round(pe_earned, 1),
        "elective_earned": round(elective_earned, 1),
        "elective_gap": round(elective_gap, 1),
        "note": note,
    }


def check_graduation(session: Session, student_id: int) -> dict:
    student = session.get(Student, student_id)
    if student is None:
        raise ValueError(f"Student id={student_id} 不存在")

    major_result = check_major(session, student)
    double_major_result = check_double_major(session, student)
    minor_results = [
        check_minor(session, student, m)
        for m in [student.minor1, student.minor2]
        if m and m.strip()
    ]
    ge_result = check_ge(session, student)
    pe_result = check_pe(session, student)

    incomplete_items = []
    if major_result.get("status") not in ("complete",):
        incomplete_items.append("主系必修")
    if double_major_result and double_major_result.get("status") not in ("complete",):
        incomplete_items.append("雙主修")
    for mr in minor_results:
        if mr.get("status") not in ("complete",):
            incomplete_items.append(f"輔系 {mr.get('dept_name', '')}")
    if ge_result.get("status") not in ("complete",):
        incomplete_items.append("通識")
    if pe_result.get("status") not in ("complete",):
        incomplete_items.append("體育必修")

    all_complete = len(incomplete_items) == 0
    elective_gap_info = _calc_elective_gap(student, major_result, ge_result, pe_result)

    return {
        "student": {
            "id": student.id,
            "student_number": student.student_number,
            "chinese_name": student.chinese_name,
            "entry_year": student.entry_year,
            "register_major": student.register_major,
            "register_double_major": student.register_double_major,
            "minor1": student.minor1,
            "minor2": student.minor2,
            "graduation_credit": float(student.graduation_credit) if student.graduation_credit else None,
            "total_credits": float(student.total_credits) if student.total_credits else None,
        },
        "major_check": major_result,
        "double_major_check": double_major_result,
        "minor_checks": minor_results,
        "ge_check": ge_result,
        "pe_check": pe_result,
        "summary": {
            "all_complete": all_complete,
            "incomplete_items": incomplete_items,
            "elective_credits": elective_gap_info,
        },
    }
