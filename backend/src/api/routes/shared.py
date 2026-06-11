from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.cache import cache_delete, cache_get, cache_set
from src.core.database import get_db
from src.core.exceptions import NotFoundException
from src.models import Student
from src.services.checker import check_graduation

router = APIRouter(tags=["shared"])

_CACHE_PREFIX = "check:"


@router.get("/check/{sid}")
def get_check_result(
    sid: str,
    db: Session = Depends(get_db),
) -> dict:
    student = db.get(Student, sid)
    if student is None:
        raise NotFoundException(f"Student id={sid} 不存在")

    key = f"{_CACHE_PREFIX}{sid}"
    cached = cache_get(key)
    if cached is not None:
        return cached

    result = check_graduation(db, sid)
    cache_set(key, result)
    return result


def invalidate_check_cache(sid: str) -> None:
    cache_delete(f"{_CACHE_PREFIX}{sid}")
