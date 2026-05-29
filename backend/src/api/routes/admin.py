from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.exceptions import NotFoundException
from src.models import Student
from src.services.checker import check_graduation

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    total = db.execute(
        select(func.count(Student.student_id))
    ).scalar() or 0
    return {"total_students": total}


@router.get("/students")
def list_students(
    q: str | None = None,
    admission_year: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(Student)
    if q:
        like = f"%{q}%"
        query = query.where(
            Student.student_id.ilike(like) | Student.name.ilike(like)
        )
    if admission_year:
        query = query.where(Student.admission_year == admission_year)
    query = query.order_by(Student.student_id)
    students = db.execute(query).scalars().all()
    return [
        {
            "student_id": s.student_id,
            "name": s.name,
            "admission_year": s.admission_year,
        }
        for s in students
    ]


@router.get("/students/{sid}")
def get_student_detail(sid: str, db: Session = Depends(get_db)):
    student = db.get(Student, sid)
    if student is None:
        raise NotFoundException(f"Student id={sid} 不存在")
    return check_graduation(db, sid)
