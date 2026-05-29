from __future__ import annotations

import difflib
import json
import os as _os
import re
import unicodedata
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session

from src.models import Course, Enrollment, FieldOfStudy, Student

GE_CORE = 1 << 7
GE_HUMAN = 1 << 6
GE_SOCIAL = 1 << 5
GE_NATURAL = 1 << 4
GE_INFO = 1 << 3
GE_COLLEGE = 1 << 2
GE_FOREIGN = 1 << 1
GE_CHINESE = 1 << 0

_DATA_DIR = Path(_os.environ.get("DATA_DIR", "")) if _os.environ.get("DATA_DIR") else (
    Path(__file__).parent.parent.parent.parent / "data"
)


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


_FULLWIDTH_TO_HALF = str.maketrans(
    "".join(chr(0xFF01 + i) for i in range(94)),
    "".join(chr(0x21 + i) for i in range(94)),
)


def _normalize_name(name: str) -> str:
    s = (name or "").strip()
    s = s.translate(_FULLWIDTH_TO_HALF)
    s = unicodedata.normalize("NFC", s)
    # 保留數字括號（一）（二）...避免同系列課程名稱撞在一起
    s = re.sub(r"\((?![一二三四五六七八九十])[^)]*\)", "", s)
    s = re.sub(r"（(?![一二三四五六七八九十])[^）]*）", "", s)
    s = re.sub(r"\s+", "", s)
    return s.strip()


def _build_sc_by_code(student_courses: Sequence[Enrollment]) -> dict:
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
    student_courses: Sequence[Enrollment],
) -> tuple:
    code = (rule_code or "").strip()
    if code and code in sc_by_code:
        return sc_by_code[code], "exact"
    # 前綴比對：rule_code 較短時（如 000713），找第一個以它為前綴的選課
    if code and len(code) < 9:
        for sc_code, sc in sc_by_code.items():
            if sc_code.startswith(code):
                return sc, "exact_prefix"

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


def _match_courses_from_rules(
    rule_courses: list[dict],
    student_courses: Sequence[Enrollment],
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
                "course_type": dc.get("type"),
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


def _expand_group_courses(rule_courses: list[dict], group_course_codes: dict) -> list[dict]:
    """把群B/C/D/E 佔位條目展開成實際課程清單，群A 條目名稱已具體不需展開。"""
    if not group_course_codes:
        return rule_courses

    expanded = []
    for dc in rule_courses:
        grp = str(dc.get("type") or "")
        if not grp.startswith("群"):
            expanded.append(dc)
            continue

        actual = group_course_codes.get(grp)
        # 群A 條目已是具體課名（資訊專題A/B/C/D），直接保留
        # 其他群若有 actual 清單就展開
        if not actual or grp == "群A":
            expanded.append(dc)
            continue

        for c in actual:
            expanded.append({
                "name": c["name"],
                "type": grp,
                "course_code_required": c.get("course_code") or "無",
                "credits": dc.get("credits", 3),
                "recognition": dc.get("recognition", "需為本系開課"),
                "note": dc.get("note", ""),
            })

    return expanded


def check_major(session: Session, student: Student, major_name: str | None) -> dict:
    if not major_name:
        return _not_found_result("未設定主修")

    rules = _find_rules("graduation", student.admission_year, major_name)
    if rules is None:
        return _not_found_result(major_name)

    all_courses = rules.get("courses", [])
    rule_courses = [c for c in all_courses if c.get("type") in ("必修", "群修") or str(c.get("type") or "").startswith("群")]

    # 若規則有 group_course_codes，展開群B/C/D/E 佔位條目為實際課程
    group_course_codes = rules.get("group_course_codes", {})
    rule_courses = _expand_group_courses(rule_courses, group_course_codes)

    if not rule_courses and rules.get("total_credits_required") is None:
        return _no_data_result(rules.get("dept_name", major_name))

    student_courses = (
        session.execute(
            select(Enrollment).options(joinedload(Enrollment.course))
            .where(Enrollment.student_id == student.student_id)
        )
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
        "dept_name": rules.get("dept_name", major_name),
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


def check_double_major(session: Session, student: Student, dm_name: str | None, major_name: str | None) -> dict | None:
    if not dm_name:
        return None

    dm_name = dm_name.strip()
    is_cs = "資訊科學" in (major_name or "")

    rules = _find_double_major_rules(student.admission_year, dm_name, is_cs)
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

    rule_courses = [c for c in all_courses if c.get("type") in ("必修", "群修") or str(c.get("type") or "").startswith("群")]

    student_courses = (
        session.execute(
            select(Enrollment).options(joinedload(Enrollment.course))
            .where(Enrollment.student_id == student.student_id)
        )
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


def check_minor(session: Session, student: Student, minor_name: str) -> dict:
    rules = _find_rules("minor", student.admission_year, minor_name)
    if rules is None:
        return _not_found_result(minor_name)

    rule_courses = rules.get("courses", [])
    student_courses = (
        session.execute(
            select(Enrollment).options(joinedload(Enrollment.course))
            .where(Enrollment.student_id == student.student_id)
        )
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


def check_ge(session: Session, student: Student) -> dict:
    student_courses = (
        session.execute(
            select(Enrollment).options(joinedload(Enrollment.course))
            .where(Enrollment.student_id == student.student_id)
        )
        .scalars()
        .all()
    )

    category_defs = {
        "中文通": {"name": "中國語文領域", "min": 3.0, "max": 6.0},
        "外文通": {"name": "外國語文領域", "min": 6.0, "max": 6.0},
        "人文通": {"name": "人文學通識", "min": 3.0, "max": 7.0},
        "社會通": {"name": "社會科學通識", "min": 3.0, "max": 7.0},
        "自然通": {"name": "自然科學通識", "min": 3.0, "max": 7.0},
        "資訊通": {"name": "資訊通識", "min": 2.0, "max": 3.0},
        "書院通": {"name": "書院通識", "min": 0.0, "max": 3.0},
    }

    fos_list = session.execute(
        select(FieldOfStudy).options(joinedload(FieldOfStudy.department))
        .where(FieldOfStudy.student_id == student.student_id, FieldOfStudy.program_type == "主修")
    ).scalars().all()

    cs_like_majors = {
        "統計學系", "資訊管理學系", "地政學系土地測量與資訊組",
        "應用數學系", "資訊科學系", "創新國際學院學士班",
    }
    for fos in fos_list:
        dept_name = fos.department.name if fos.department else ""
        if dept_name in cs_like_majors:
            category_defs["資訊通"]["min"] = 0.0
            break

    bit_to_category = {
        GE_HUMAN: "人文通",
        GE_SOCIAL: "社會通",
        GE_NATURAL: "自然通",
        GE_INFO: "資訊通",
        GE_COLLEGE: "書院通",
    }
    domain_bits = tuple(bit_to_category)

    fixed: dict[str, list[dict]] = {k: [] for k in category_defs}
    cross_courses: list[dict] = []

    for sc in student_courses:
        if _score_status(sc.score) != "passed":
            continue
        cred = float(sc.credit or 0)
        ge_label = int(getattr(sc.course, "ge_label", 0) or 0)
        if not ge_label:
            ge_label = _ge_label_from_legacy_remark(sc)
        if not ge_label:
            continue

        entry = {
            "course_name": sc.course_name,
            "course_code": sc.course_code,
            "credits": cred,
            "score": sc.score,
            "ge_label": ge_label,
        }

        if ge_label & GE_CHINESE:
            fixed["中文通"].append({**entry, "allocated_category": "中文通"})
            continue
        if ge_label & GE_FOREIGN:
            fixed["外文通"].append({**entry, "allocated_category": "外文通"})
            continue

        categories = [
            bit_to_category[bit] for bit in domain_bits if ge_label & bit
        ]
        if not categories:
            continue
        if len(categories) == 1:
            fixed[categories[0]].append({**entry, "allocated_category": categories[0]})
        else:
            cross_courses.append({**entry, "candidate_categories": categories})

    allocation = _best_ge_allocation(category_defs, fixed, cross_courses)
    category_results = []
    for key, cfg in category_defs.items():
        courses = allocation["courses"].get(key, [])
        earned = min(sum(c["credits"] for c in courses), cfg["max"])
        complete = earned >= cfg["min"]
        category_results.append({
            "category_name": cfg["name"],
            "remark_code": key,
            "credits_required_min": cfg["min"],
            "credits_required_max": cfg["max"],
            "earned_credits": round(earned, 1),
            "missing_credits": round(max(0.0, cfg["min"] - earned), 1),
            "courses": courses,
            "status": "complete" if complete else "incomplete",
        })

    total_earned = min(sum(c["earned_credits"] for c in category_results), GE_REQUIRED_CREDITS)
    core_domains = allocation["core_domains"]
    all_complete = (
        total_earned >= GE_REQUIRED_CREDITS
        and all(c["status"] == "complete" for c in category_results)
        and len(core_domains) >= 2
    )

    return {
        "categories": category_results,
        "total_required_credits": GE_REQUIRED_CREDITS,
        "earned_credits": round(total_earned, 1),
        "missing_credits": round(max(0.0, GE_REQUIRED_CREDITS - total_earned), 1),
        "core_domains": sorted(core_domains),
        "core_domains_required": 2,
        "cross_domain_courses": cross_courses,
        "status": "complete" if all_complete else "incomplete",
    }


def _ge_label_from_legacy_remark(sc: Enrollment) -> int:
    remark_text = sc.remark or ""
    name_text = sc.course_name or ""
    code = sc.course_code or ""
    label = 0
    if code.startswith("031") or "中文通" in remark_text or name_text.startswith("國文"):
        label |= GE_CHINESE
    if code.startswith("032") or "外文通" in remark_text or "大學英文" in name_text:
        label |= GE_FOREIGN
    if code.startswith("045") or "書院通" in remark_text:
        label |= GE_COLLEGE
    if "人文" in remark_text:
        label |= GE_HUMAN
    if "社會" in remark_text:
        label |= GE_SOCIAL
    if "自然" in remark_text:
        label |= GE_NATURAL
    if "資訊" in remark_text:
        label |= GE_INFO
    if "核心" in remark_text:
        label |= GE_CORE
    return label


def _best_ge_allocation(
    category_defs: dict[str, dict],
    fixed: dict[str, list[dict]],
    cross_courses: list[dict],
) -> dict:
    best = None

    def evaluate(choice_map: dict[int, str]) -> dict:
        courses = {key: [dict(c) for c in vals] for key, vals in fixed.items()}
        for idx, course in enumerate(cross_courses):
            key = choice_map[idx]
            courses[key].append({**course, "allocated_category": key})

        earned = {
            key: min(sum(c["credits"] for c in vals), category_defs[key]["max"])
            for key, vals in courses.items()
        }
        missing = sum(max(0.0, category_defs[key]["min"] - earned[key]) for key in earned)
        total = min(sum(earned.values()), GE_REQUIRED_CREDITS)
        core_domains = set()
        for key in ("人文通", "社會通", "自然通"):
            for course in courses[key]:
                if int(course.get("ge_label", 0) or 0) & GE_CORE:
                    core_domains.add(key)
        return {
            "courses": courses,
            "earned": earned,
            "missing": missing,
            "total": total,
            "core_domains": core_domains,
            "score": (
                total,
                -missing,
                len(core_domains),
                -sum(len(v) for v in courses.values()),
            ),
        }

    def dfs(idx: int, choice_map: dict[int, str]) -> None:
        nonlocal best
        if idx == len(cross_courses):
            result = evaluate(choice_map)
            if best is None or result["score"] > best["score"]:
                best = result
            return
        for key in cross_courses[idx]["candidate_categories"]:
            choice_map[idx] = key
            dfs(idx + 1, choice_map)
        choice_map.pop(idx, None)

    dfs(0, {})
    return best or evaluate({})


def check_pe(session: Session, student: Student) -> dict:
    pe_courses = (
        session.execute(
            select(Enrollment).options(joinedload(Enrollment.course))
            .where(Enrollment.student_id == student.student_id)
        )
        .scalars()
        .all()
    )
    pe_courses = [
        sc for sc in pe_courses
        if (
            (getattr(sc.course, "type", None) == "體育")
            or (sc.course_code or "").startswith("002")
            or ("體育" in (sc.course_name or ""))
        )
    ]

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


GRADUATION_TOTAL_CREDITS = 128
GE_REQUIRED_CREDITS = 28
PE_REQUIRED_CREDITS = 4


def _calc_elective_gap(
    total_credits: float,
    major_result: dict,
    ge_result: dict,
    pe_result: dict,
) -> dict:
    TOTAL = GRADUATION_TOTAL_CREDITS
    required_lists = (
        major_result.get("passed_courses", [])
        + major_result.get("in_progress_courses", [])
        + major_result.get("missing_courses", [])
    )
    major_required = sum(
        float(c.get("credits", 0) or 0)
        for c in required_lists
        if c.get("group_label") == "必修" or c.get("course_type") == "必修"
    )
    major_earned = sum(
        float(c.get("credits", 0) or 0)
        for c in major_result.get("passed_courses", [])
        if c.get("group_label") == "必修" or c.get("course_type") == "必修"
    )
    if major_required == 0:
        major_required = major_result.get("total_credits_required") or 0
        major_earned = major_result.get("earned_credits") or 0.0

    ge_earned = ge_result.get("earned_credits")
    if ge_earned is None:
        ge_earned = sum(cat.get("earned_credits", 0.0) for cat in ge_result.get("categories", []))
        ge_earned = min(ge_earned, float(GE_REQUIRED_CREDITS))

    pe_passed = len(pe_result.get("passed_courses", []))
    pe_earned = float(min(pe_passed, PE_REQUIRED_CREDITS))

    elective_required = max(0, TOTAL - major_required - GE_REQUIRED_CREDITS - PE_REQUIRED_CREDITS)
    total_earned = total_credits
    elective_earned = max(0.0, total_earned - major_earned - ge_earned - pe_earned)
    elective_gap = max(0.0, elective_required - elective_earned)

    note = (
        f"選修應修 = {TOTAL} - 必修{major_required} - 通識{GE_REQUIRED_CREDITS}"
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


def check_graduation(session: Session, student_id: str) -> dict:
    student = session.get(Student, student_id)
    if student is None:
        raise ValueError(f"Student id={student_id} 不存在")

    fos_list = session.execute(
        select(FieldOfStudy).options(joinedload(FieldOfStudy.department))
        .where(FieldOfStudy.student_id == student.student_id)
    ).scalars().all()

    register_major = None
    register_double_major = None
    minors = []
    for fos in fos_list:
        dept_name = fos.department.name if fos.department else fos.department_id
        if fos.program_type == "主修":
            register_major = dept_name
        elif fos.program_type == "雙主修":
            register_double_major = dept_name
        elif fos.program_type == "輔系":
            minors.append(dept_name)

    major_result = check_major(session, student, register_major)
    double_major_result = check_double_major(session, student, register_double_major, register_major)
    minor_results = [check_minor(session, student, m) for m in minors]
    ge_result = check_ge(session, student)
    pe_result = check_pe(session, student)

    enrollments = session.execute(
        select(Enrollment).options(joinedload(Enrollment.course))
        .where(Enrollment.student_id == student.student_id)
    ).scalars().all()
    total_credits = sum(
        float(e.course.credits) for e in enrollments
        if e.is_passed and e.course
    )

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
    elective_gap_info = _calc_elective_gap(total_credits, major_result, ge_result, pe_result)

    return {
        "student": {
            "id": student.student_id,
            "student_number": student.student_id,
            "chinese_name": student.name,
            "entry_year": student.admission_year,
            "register_major": register_major,
            "register_double_major": register_double_major,
            "minor1": minors[0] if len(minors) > 0 else None,
            "minor2": minors[1] if len(minors) > 1 else None,
            "graduation_credit": None,
            "total_credits": round(total_credits, 1),
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


def check_physical_education(session: Session, student: Student) -> dict:
    return check_pe(session, student)


def check_general_education(session: Session, student: Student) -> dict:
    return check_ge(session, student)


def _student_program_names(session: Session, student: Student) -> dict:
    fos_list = session.execute(
        select(FieldOfStudy).options(joinedload(FieldOfStudy.department))
        .where(FieldOfStudy.student_id == student.student_id)
    ).scalars().all()

    result = {"major": None, "double_major": None, "minors": []}
    for fos in fos_list:
        dept_name = fos.department.name if fos.department else fos.department_id
        if fos.program_type == "主修":
            result["major"] = dept_name
        elif fos.program_type == "雙主修":
            result["double_major"] = dept_name
        elif fos.program_type == "輔系":
            result["minors"].append(dept_name)
    return result


def check_required_courses(session: Session, student: Student) -> dict:
    program_names = _student_program_names(session, student)
    major = check_major(session, student, program_names["major"])
    for key in ("passed_courses", "in_progress_courses", "missing_courses"):
        major[key] = [
            c for c in major.get(key, [])
            if c.get("group_label") == "必修" or c.get("course_type") == "必修"
        ]
    return major


def check_group_courses(session: Session, student: Student) -> dict:
    program_names = _student_program_names(session, student)
    major = check_major(session, student, program_names["major"])
    for key in ("passed_courses", "in_progress_courses", "missing_courses"):
        major[key] = [
            c for c in major.get(key, [])
            if c.get("group_label") == "群修" or c.get("course_type") == "群修"
        ]
    return major


def check_total_credits(session: Session, student: Student) -> dict:
    program_names = _student_program_names(session, student)
    major_result = check_major(session, student, program_names["major"])
    ge_result = check_ge(session, student)
    pe_result = check_pe(session, student)
    enrollments = session.execute(
        select(Enrollment).options(joinedload(Enrollment.course))
        .where(Enrollment.student_id == student.student_id)
    ).scalars().all()
    total_credits = sum(
        float(e.course.credits) for e in enrollments
        if e.is_passed and e.course
    )
    return _calc_elective_gap(total_credits, major_result, ge_result, pe_result)
