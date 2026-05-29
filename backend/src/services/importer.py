"""
src/services/importer.py - 解析 exportStudentData.json 並 upsert student/student_course
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from src.models import Student, StudentCourse, User


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
    key = str(raw).strip()
    return REQ_MAP.get(key, "選")


def _to_decimal(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def parse_student_data(json_data: dict) -> dict:
    if isinstance(json_data, list):
        raw = json_data[0]
    elif "data" in json_data and isinstance(json_data["data"], list):
        raw = json_data["data"][0]
    else:
        raw = json_data

    acad = raw.get("課業學習", {})
    about_me = acad.get("aboutMe", {})

    student_number = str(about_me.get("studentNumber", "")).strip()
    register_major = about_me.get("registerMajor", "") or ""
    register_double_major = about_me.get("registerDoubleMajor") or None
    minor1 = about_me.get("minor1") or None
    minor2 = about_me.get("minor2") or None
    chinese_name = about_me.get("chineseName", "") or None

    entry_year = _entry_year_from_student_number(student_number)

    course_plan = acad.get("coursePlan", {})
    graduation_credit = _to_decimal(course_plan.get("graduationCredit"))
    required_point = _to_decimal(course_plan.get("requiredPoint"))
    group_point = _to_decimal(course_plan.get("groupPoint"))
    total_credits = _to_decimal(acad.get("totalCredits"))

    grade_record_list = acad.get("gradeRecordList", []) or []
    courses = []
    for year_block in grade_record_list:
        for rec in year_block.get("GradeRecords", []) or []:
            score_raw = rec.get("score")
            score_str = str(score_raw).strip() if score_raw is not None else None

            req_norm = _normalize_req(rec.get("requiredOrElectiveCourse", "選"))
            acad_year_raw = rec.get("academicYear")
            semester_raw = rec.get("semester")
            acad_year_sem = str(rec.get("academicYearSemester", "")).strip()
            if not acad_year_sem and acad_year_raw and semester_raw:
                acad_year_sem = f"{acad_year_raw}{semester_raw}"

            courses.append(
                {
                    "course_code": str(rec.get("courseCode", "")).strip(),
                    "course_name": str(rec.get("courseName", "")).strip(),
                    "credit": _to_decimal(rec.get("credit")) or 0,
                    "score": score_str,
                    "required_or_elective": req_norm,
                    "remark": rec.get("remark") or None,
                    "academic_year": int(acad_year_raw) if acad_year_raw else 0,
                    "semester": int(semester_raw) if semester_raw else 0,
                    "academic_year_semester": acad_year_sem,
                }
            )

    student_info = {
        "student_number": student_number,
        "chinese_name": chinese_name,
        "entry_year": entry_year,
        "register_major": register_major,
        "register_double_major": register_double_major,
        "minor1": minor1,
        "minor2": minor2,
        "graduation_credit": graduation_credit,
        "total_credits": total_credits,
        "required_point": required_point,
        "group_point": group_point,
    }
    return {"student_info": student_info, "courses": courses}


def upsert_student(session: Session, student_info: dict, user_id: int | None = None) -> Student:
    student_number = student_info["student_number"]

    if user_id is None:
        user = session.query(User).filter_by(account=student_number, role="student").first()
        user_id = user.id if user else None

    student = session.query(Student).filter_by(student_number=student_number).first()

    if student is None:
        info = {**student_info}
        if user_id is not None:
            info["user_id"] = user_id
        student = Student(**info)
        session.add(student)
    else:
        for key, value in student_info.items():
            setattr(student, key, value)
        if user_id is not None:
            student.user_id = user_id

    session.flush()
    return student


def upsert_student_courses(session: Session, student: Student, courses: list[dict]) -> int:
    session.query(StudentCourse).filter_by(student_id=student.id).delete()
    if not courses:
        return 0
    new_records = [
        StudentCourse(
            student_id=student.id,
            course_code=c["course_code"],
            course_name=c["course_name"],
            credit=c["credit"],
            score=c["score"],
            required_or_elective=c["required_or_elective"],
            remark=c["remark"],
            academic_year=c["academic_year"],
            semester=c["semester"],
            academic_year_semester=c["academic_year_semester"],
        )
        for c in courses
    ]
    session.bulk_save_objects(new_records)
    return len(new_records)


def import_student_json_from_dict(session: Session, data: dict) -> tuple[Student, int]:
    parsed = parse_student_data(data)
    entry_year = parsed["student_info"].get("entry_year")
    if entry_year != 112:
        raise ValueError(
            f"目前系統僅支援 112 學年度入學學生（偵測到入學年：{entry_year}），"
            "請確認上傳的是正確的 exportStudentData.json。"
        )
    student = upsert_student(session, parsed["student_info"])
    count = upsert_student_courses(session, student, parsed["courses"])
    session.commit()
    return student, count


def import_student_json(session: Session, json_path: str | Path) -> tuple[Student, int]:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return import_student_json_from_dict(session, data)


parse_student_json = parse_student_data
