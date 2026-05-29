from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.exceptions import NotFoundException
from src.models import Student
from src.services.checker import check_graduation

router = APIRouter(tags=["shared"])


@router.get("/check/{sid}")
def get_check_result(
    sid: str,
    db: Session = Depends(get_db),
) -> dict:
    student = db.get(Student, sid)
    if student is None:
        raise NotFoundException(f"Student id={sid} 不存在")
    return check_graduation(db, sid)
