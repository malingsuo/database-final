from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import and_, case, exists, func, select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.exceptions import BadRequestException, NotFoundException
from src.models import Course, Enrollment, FieldOfStudy, Student
from src.services.checker import GRADUATION_TOTAL_CREDITS, check_graduation

router = APIRouter(prefix="/admin", tags=["admin"])


class StudentAdminUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


def _profile_query():
    """每位學生的彙總資料（修課學分/通過/未通過/雙主修），供列表與詳情共用。"""
    passed_credits = func.coalesce(
        func.sum(case((Enrollment.is_passed.is_(True), Course.credits), else_=0.0)), 0.0
    )
    passed_count = func.coalesce(
        func.sum(case((Enrollment.is_passed.is_(True), 1), else_=0)), 0
    )
    failed_count = func.coalesce(
        func.sum(case((Enrollment.is_passed.is_(False), 1), else_=0)), 0
    )
    double_major = exists().where(
        and_(
            FieldOfStudy.student_id == Student.student_id,
            FieldOfStudy.program_type == "雙主修",
        )
    )
    return (
        select(
            Student.student_id,
            Student.name,
            Student.admission_year,
            Student.advisor_status,
            Student.advisor_notes,
            passed_credits.label("total_credits"),
            passed_count.label("completed_courses"),
            failed_count.label("failed_courses"),
            double_major.label("double_major"),
        )
        .select_from(Student)
        .outerjoin(Enrollment, Enrollment.student_id == Student.student_id)
        .outerjoin(
            Course,
            and_(
                Course.course_code == Enrollment.course_code,
                Course.year == Enrollment.year,
                Course.semester == Enrollment.semester,
            ),
        )
        .group_by(Student.student_id)
    )


def _row_to_profile(row) -> dict:
    return {
        "student_id": row.student_id,
        "name": row.name,
        "admission_year": row.admission_year,
        "status": row.advisor_status,
        "notes": row.advisor_notes,
        "double_major": bool(row.double_major),
        "total_credits": round(float(row.total_credits or 0), 1),
        "required_credits": GRADUATION_TOTAL_CREDITS,
        "completed_courses": int(row.completed_courses or 0),
        "failed_courses": int(row.failed_courses or 0),
    }


def _load_profiles(
    db: Session,
    *,
    q: str | None = None,
    admission_year: int | None = None,
    status: str | None = None,
    sid: str | None = None,
) -> list[dict]:
    query = _profile_query()
    if sid:
        query = query.where(Student.student_id == sid)
    if q:
        like = f"%{q}%"
        query = query.where(Student.student_id.ilike(like) | Student.name.ilike(like))
    if admission_year:
        query = query.where(Student.admission_year == admission_year)
    if status in ("on_track", "at_risk"):
        query = query.where(Student.advisor_status == status)
    query = query.order_by(Student.student_id)
    return [_row_to_profile(row) for row in db.execute(query).all()]


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    total = db.execute(select(func.count(Student.student_id))).scalar() or 0
    on_track = db.execute(
        select(func.count(Student.student_id)).where(Student.advisor_status == "on_track")
    ).scalar() or 0
    at_risk = total - on_track
    pass_rate = round(on_track / total * 100) if total else 0

    risk_students = [
        p for p in _load_profiles(db, status="at_risk")
    ]
    risk_students.sort(
        key=lambda p: (p["total_credits"] / p["required_credits"]) if p["required_credits"] else 0
    )
    risk_students = risk_students[:5]

    difficult_courses = _difficult_courses(db)

    return {
        "total_students": total,
        "on_track_students": on_track,
        "at_risk_students": at_risk,
        "pass_rate": pass_rate,
        "risk_students": risk_students,
        "difficult_courses": difficult_courses,
    }


def _difficult_courses(db: Session, limit: int = 3) -> list[dict]:
    total_count = func.count()
    failed_count = func.coalesce(
        func.sum(case((Enrollment.is_passed.is_(False), 1), else_=0)), 0
    )
    rows = db.execute(
        select(
            Course.name.label("name"),
            total_count.label("total"),
            failed_count.label("failed"),
        )
        .select_from(Enrollment)
        .join(
            Course,
            and_(
                Course.course_code == Enrollment.course_code,
                Course.year == Enrollment.year,
                Course.semester == Enrollment.semester,
            ),
        )
        .group_by(Course.name)
        .having(failed_count > 0)
    ).all()
    courses = [
        {
            "name": r.name,
            "total": int(r.total),
            "failed": int(r.failed),
            "fail_rate": round(int(r.failed) / int(r.total) * 100) if r.total else 0,
        }
        for r in rows
    ]
    courses.sort(key=lambda c: (c["fail_rate"], c["failed"]), reverse=True)
    return courses[:limit]


@router.get("/students")
def list_students(
    q: str | None = None,
    admission_year: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return _load_profiles(db, q=q, admission_year=admission_year, status=status)


@router.get("/students/{sid}")
def get_student_detail(sid: str, db: Session = Depends(get_db)):
    profiles = _load_profiles(db, sid=sid)
    if not profiles:
        raise NotFoundException(f"Student id={sid} 不存在")
    return {"profile": profiles[0], "check": check_graduation(db, sid)}


@router.patch("/students/{sid}")
def update_student_admin(
    sid: str,
    body: StudentAdminUpdate,
    db: Session = Depends(get_db),
):
    student = db.get(Student, sid)
    if student is None:
        raise NotFoundException(f"Student id={sid} 不存在")
    if body.status is not None:
        if body.status not in ("on_track", "at_risk"):
            raise BadRequestException("status 只能是 on_track 或 at_risk")
        student.advisor_status = body.status
    if body.notes is not None:
        student.advisor_notes = body.notes
    db.commit()
    return _load_profiles(db, sid=sid)[0]
