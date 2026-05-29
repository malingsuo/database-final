from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models import Department

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/departments")
def list_departments(db: Session = Depends(get_db)):
    depts = db.execute(
        select(Department).order_by(Department.college, Department.name)
    ).scalars().all()
    return [
        {"id": d.id, "college": d.college, "name": d.name}
        for d in depts
    ]
