from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Account, Course, Department, Enrollment, FieldOfStudy, Student

GE_CORE = 1 << 7
GE_HUMAN = 1 << 6
GE_SOCIAL = 1 << 5
GE_NATURAL = 1 << 4
GE_INFO = 1 << 3
GE_COLLEGE = 1 << 2
GE_FOREIGN = 1 << 1
GE_CHINESE = 1 << 0


def is_passed(score: str | None) -> bool:
    if score is None:
        return False
    s = str(score).strip()
    if s == "通過":
        return True
    if not s or s == "成績未到或無成績":
        return False
    try:
        return float(s) >= 60
    except ValueError:
        return False


def is_in_progress(score: str | None) -> bool:
    if score is None:
        return True
    s = str(score).strip()
    return not s or s == "成績未到或無成績"


def _entry_year_from_student_number(student_number: str) -> int:
    try:
        return int(str(student_number)[:3])
    except (ValueError, TypeError):
        return 112


REQ_MAP = {
    "必": "必",
    "必修": "必",
    "群": "群",
    "群修": "群",
    "選": "選",
    "選修": "選",
}


def _normalize_req(raw: str | None) -> str:
    if not raw:
        return "選"
    return REQ_MAP.get(str(raw).strip(), "選")


def _to_decimal(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _course_type(course_code: str, course_name: str, req: str, ge_label: int) -> str:
    if course_code.startswith("002") or "體育" in course_name:
        return "體育"
    if ge_label:
        return "通識"
    if req == "必":
        return "必修"
    if req == "群":
        return "群修"
    return "選修"


def infer_ge_label(course_code: str, course_name: str, remark: str | None) -> int:
    label = 0
    remark_text = remark or ""
    name_text = course_name or ""

    if course_code.startswith("031") or "中文通" in remark_text or name_text.startswith("國文"):
        label |= GE_CHINESE
    if course_code.startswith("032") or "外文通" in remark_text or "大學英文" in name_text:
        label |= GE_FOREIGN
    if course_code.startswith("045") or "書院通" in remark_text:
        label |= GE_COLLEGE

    for keyword, bit in {"人文": GE_HUMAN, "社會": GE_SOCIAL, "自然": GE_NATURAL, "資訊": GE_INFO}.items():
        if keyword in remark_text:
            label |= bit

    if "核心" in remark_text:
        label |= GE_CORE
    return label


def parse_student_data(json_data: dict) -> dict:
    if isinstance(json_data, list):
        raw = json_data[0]
    elif "data" in json_data and isinstance(json_data["data"], list):
        raw = json_data["data"][0]
    else:
        raw = json_data

    acad = raw.get("課業學習", {})
    about_me = acad.get("aboutMe", {})

    student_id = str(about_me.get("studentNumber", "")).strip()
    register_major = about_me.get("registerMajor", "") or ""
    register_double_major = about_me.get("registerDoubleMajor") or None
    minor1 = about_me.get("minor1") or None
    minor2 = about_me.get("minor2") or None
    name = about_me.get("chineseName", "") or None

    admission_year = _entry_year_from_student_number(student_id)

    courses = []
    for year_block in acad.get("gradeRecordList", []) or []:
        for rec in year_block.get("GradeRecords", []) or []:
            score_raw = rec.get("score")
            score_str = str(score_raw).strip() if score_raw is not None else None
            req_norm = _normalize_req(rec.get("requiredOrElectiveCourse", "選"))
            acad_year_raw = rec.get("academicYear")
            semester_raw = rec.get("semester")
            course_code = str(rec.get("courseCode", "")).strip()
            course_name = str(rec.get("courseName", "")).strip()
            remark = rec.get("remark") or None
            ge_label = infer_ge_label(course_code, course_name, remark)

            courses.append({
                "course_code": course_code,
                "course_name": course_name,
                "credit": _to_decimal(rec.get("credit")) or 0,
                "score": score_str,
                "required_or_elective": req_norm,
                "remark": remark,
                "academic_year": str(acad_year_raw or "0"),
                "semester": str(semester_raw or "0"),
                "course_type": _course_type(course_code, course_name, req_norm, ge_label),
                "ge_label": ge_label,
            })

    return {
        "student_info": {
            "student_id": student_id,
            "name": name,
            "admission_year": admission_year,
            "register_major": register_major,
            "register_double_major": register_double_major,
            "minor1": minor1,
            "minor2": minor2,
        },
        "courses": courses,
    }


def _find_or_create_account(session: Session, student_id: str, user_id: uuid.UUID | None) -> Account:
    account = session.get(Account, user_id) if user_id else None
    if account is None:
        account = session.execute(
            select(Account).where(Account.email == f"{student_id}@student.local")
        ).scalar_one_or_none()
    if account is None:
        account = Account(
            id=user_id or uuid.uuid4(),
            email=f"{student_id}@student.local",
            password_hash="imported",
            role="student",
        )
        session.add(account)
        session.flush()
    return account


def _fallback_department_id(name: str, student_id: str, offset: int) -> str:
    dep = student_id[3:6] if len(student_id) >= 6 else ""
    if dep and dep.isdigit():
        return dep
    token = re.sub(r"\W+", "", name or "")[:6]
    return token or f"UNK{offset}"


def _find_or_create_department(session: Session, name: str, student_id: str, offset: int) -> Department:
    dept = session.execute(select(Department).where(Department.name == name)).scalar_one_or_none()
    if dept:
        return dept
    dept_id = _fallback_department_id(name, student_id, offset)
    dept = session.get(Department, dept_id)
    if dept is None:
        dept = Department(id=dept_id, college="未知", name=name)
        session.add(dept)
        session.flush()
    return dept


def upsert_student(session: Session, student_info: dict, user_id: uuid.UUID | None = None) -> Student:
    student_id = student_info["student_id"]
    account = _find_or_create_account(session, student_id, user_id)

    student = session.get(Student, student_id)
    if student is None:
        student = Student(
            student_id=student_id,
            user_id=account.id,
            name=student_info.get("name"),
            admission_year=student_info["admission_year"],
        )
        session.add(student)
    else:
        student.user_id = account.id
        student.name = student_info.get("name")
        student.admission_year = student_info["admission_year"]
    session.flush()

    session.query(FieldOfStudy).filter_by(student_id=student.student_id).delete()
    for idx, (program_type, dept_name) in enumerate([
        ("主修", student_info.get("register_major")),
        ("雙主修", student_info.get("register_double_major")),
        ("輔系", student_info.get("minor1")),
        ("輔系", student_info.get("minor2")),
    ], start=1):
        if not dept_name:
            continue
        dept = _find_or_create_department(session, dept_name, student_id, idx)
        session.add(FieldOfStudy(
            student_id=student.student_id,
            department_id=dept.id,
            program_type=program_type,
            enrollment_year=student.admission_year,
        ))
    session.flush()
    return student


def upsert_student_courses(session: Session, student: Student, courses: list[dict]) -> int:
    session.query(Enrollment).filter_by(student_id=student.student_id).delete()
    session.flush()

    for c in courses:
        course = session.get(Course, (c["course_code"], c["academic_year"], c["semester"]))
        if course is None:
            course = Course(
                course_code=c["course_code"],
                year=c["academic_year"],
                semester=c["semester"],
                name=c["course_name"],
                credits=c["credit"],
                type=c["course_type"],
                ge_label=c["ge_label"],
            )
            session.add(course)
        else:
            if not course.ge_label and c["ge_label"]:
                course.ge_label = c["ge_label"]
            if not course.type or course.type == "選修":
                course.type = c["course_type"]

        session.add(Enrollment(
            student_id=student.student_id,
            course_code=c["course_code"],
            year=c["academic_year"],
            semester=c["semester"],
            grade=c["score"],
            is_passed=is_passed(c["score"]),
            required_or_elective=c["required_or_elective"],
            remark=c["remark"],
        ))
    return len(courses)


def import_student_json_from_dict(
    session: Session, data: dict, user_id: uuid.UUID | None = None
) -> tuple[Student, int]:
    parsed = parse_student_data(data)
    admission_year = parsed["student_info"].get("admission_year")
    if admission_year != 112:
        raise ValueError(
            f"目前系統僅支援 112 學年度入學學生（偵測到入學年：{admission_year}），"
            "請確認上傳的是正確的 exportStudentData.json。"
        )
    student = upsert_student(session, parsed["student_info"], user_id)
    count = upsert_student_courses(session, student, parsed["courses"])
    session.commit()
    return student, count


def import_student_json(
    session: Session, json_path: str | Path
) -> tuple[Student, int]:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return import_student_json_from_dict(session, data)


parse_student_json = parse_student_data
