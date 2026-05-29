from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Course, Department, Enrollment, FieldOfStudy, Student


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


def _find_department_by_name(session: Session, name: str) -> Department | None:
    if not name:
        return None
    result = session.execute(
        select(Department).where(Department.name == name)
    ).scalar_one_or_none()
    if result:
        return result
    for d in session.execute(select(Department)).scalars().all():
        if name in d.name or d.name in name:
            return d
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

    student_id = str(about_me.get("studentNumber", "")).strip()
    register_major = about_me.get("registerMajor", "") or ""
    register_double_major = about_me.get("registerDoubleMajor") or None
    minor1 = about_me.get("minor1") or None
    minor2 = about_me.get("minor2") or None
    name = about_me.get("chineseName", "") or None

    admission_year = _entry_year_from_student_number(student_id)

    grade_record_list = acad.get("gradeRecordList", []) or []
    courses = []
    for year_block in grade_record_list:
        for rec in year_block.get("GradeRecords", []) or []:
            score_raw = rec.get("score")
            score_str = str(score_raw).strip() if score_raw is not None else None

            req_norm = _normalize_req(rec.get("requiredOrElectiveCourse", "選"))
            acad_year_raw = rec.get("academicYear")
            semester_raw = rec.get("semester")

            courses.append({
                "course_code": str(rec.get("courseCode", "")).strip(),
                "course_name": str(rec.get("courseName", "")).strip(),
                "credit": _to_decimal(rec.get("credit")) or 0,
                "score": score_str,
                "required_or_elective": req_norm,
                "remark": rec.get("remark") or None,
                "academic_year": str(acad_year_raw) if acad_year_raw else "0",
                "semester": str(semester_raw) if semester_raw else "0",
            })

    student_info = {
        "student_id": student_id,
        "name": name,
        "admission_year": admission_year,
        "register_major": register_major,
        "register_double_major": register_double_major,
        "minor1": minor1,
        "minor2": minor2,
    }
    return {"student_info": student_info, "courses": courses}


def upsert_student(
    session: Session, student_info: dict, user_id: uuid.UUID | None = None
) -> Student:
    student_id = student_info["student_id"]
    student = session.get(Student, student_id)

    if student is None:
        student = Student(
            student_id=student_id,
            user_id=user_id,
            name=student_info.get("name"),
            admission_year=student_info["admission_year"],
        )
        session.add(student)
    else:
        if user_id is not None:
            student.user_id = user_id
        if "name" in student_info:
            student.name = student_info.get("name")
        student.admission_year = student_info["admission_year"]

    session.flush()
    return student


def _sync_fields_of_study(session: Session, student: Student, student_info: dict) -> None:
    session.query(FieldOfStudy).filter_by(student_id=student.student_id).delete()

    fos_list = []

    major = student_info.get("register_major")
    if major:
        dept = _find_department_by_name(session, major)
        if dept:
            fos_list.append(FieldOfStudy(
                student_id=student.student_id,
                department_id=dept.id,
                program_type="主修",
            ))

    dm = student_info.get("register_double_major")
    if dm:
        dept = _find_department_by_name(session, dm)
        if dept:
            fos_list.append(FieldOfStudy(
                student_id=student.student_id,
                department_id=dept.id,
                program_type="雙主修",
            ))

    for minor_name in [student_info.get("minor1"), student_info.get("minor2")]:
        if minor_name:
            dept = _find_department_by_name(session, minor_name)
            if dept:
                fos_list.append(FieldOfStudy(
                    student_id=student.student_id,
                    department_id=dept.id,
                    program_type="輔系",
                ))

    for fos in fos_list:
        session.add(fos)


def _upsert_course(session: Session, c: dict) -> Course:
    course = session.get(Course, (c["course_code"], c["academic_year"], c["semester"]))
    if course is None:
        course = Course(
            course_code=c["course_code"],
            year=c["academic_year"],
            semester=c["semester"],
            name=c["course_name"],
            credits=c["credit"],
        )
        session.add(course)
        session.flush()
    return course


def upsert_enrollments(session: Session, student: Student, courses: list[dict]) -> int:
    session.query(Enrollment).filter_by(student_id=student.student_id).delete()
    if not courses:
        return 0

    for c in courses:
        _upsert_course(session, c)
        grade = c.get("score")
        session.add(Enrollment(
            student_id=student.student_id,
            course_code=c["course_code"],
            year=c["academic_year"],
            semester=c["semester"],
            grade=grade,
            is_passed=is_passed(grade),
            required_or_elective=c.get("required_or_elective"),
            remark=c.get("remark"),
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
    _sync_fields_of_study(session, student, parsed["student_info"])
    count = upsert_enrollments(session, student, parsed["courses"])
    session.commit()
    return student, count


def import_student_json(
    session: Session, json_path: str | Path
) -> tuple[Student, int]:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return import_student_json_from_dict(session, data)


parse_student_json = parse_student_data
