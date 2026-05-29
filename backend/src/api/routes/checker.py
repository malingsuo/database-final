"""
src/api/routes/checker.py - 畢業學分檢核 API 端點

POST /api/check/upload   上傳 exportStudentData.json
GET  /api/check/{sid}    對已上傳學生執行學分檢核
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.exceptions import BadRequestException, NotFoundException
from src.models import Student
from src.services.checker import check_graduation
from src.services.importer import import_student_json_from_dict

router = APIRouter(prefix="/check", tags=["checker"])


@router.post("/upload")
async def upload_student_json(
    file: UploadFile = File(...),
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> dict:
    """
    上傳 exportStudentData.json。
    nginx 會把 JWT 解完的 user_id 放進 X-User-Id header。
    """
    if not (file.filename or "").lower().endswith(".json"):
        raise BadRequestException("只接受 .json 格式的檔案")

    raw_bytes = await file.read()
    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise BadRequestException(f"JSON 格式錯誤：{e}")

    try:
        user_id = uuid.UUID(x_user_id) if x_user_id else None
        student, course_count = import_student_json_from_dict(db, data, user_id=user_id)
    except ValueError as e:
        raise BadRequestException(str(e))

    return {
        "student_id": student.student_id,
        "student_number": student.student_id,
        "chinese_name": student.name,
        "course_count": course_count,
    }


@router.get("/{sid}")
def get_check_result(
    sid: str,
    db: Session = Depends(get_db),
) -> dict:
    """對學生 sid 執行完整畢業學分檢核。"""
    student = db.get(Student, sid)
    if student is None:
        raise NotFoundException(f"Student id={sid} 不存在")

    result = check_graduation(db, sid)
    return result
