from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, File, Header, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    UnauthorizedException,
)
from src.models import Account, Student
from src.services.importer import import_parsed_for_student, parse_student_data

router = APIRouter(prefix="/check", tags=["student"])


@router.post("/upload")
async def upload_student_json(
    file: UploadFile = File(...),
    x_account_id: str | None = Header(None, alias="X-Account-ID"),
    db: Session = Depends(get_db),
) -> dict:
    # 上傳僅限已登入的學生本人：身分由 nginx 驗 token 後以 X-Account-ID 帶入。
    if not x_account_id:
        raise UnauthorizedException("請先登入後再上傳資料")
    try:
        account_id = uuid.UUID(x_account_id)
    except ValueError:
        raise UnauthorizedException("登入身分無效")

    account = db.get(Account, account_id)
    if account is None or account.role != "student":
        raise ForbiddenException("只有學生帳號可以上傳資料")

    student = db.execute(
        select(Student).where(Student.user_id == account_id)
    ).scalar_one_or_none()
    if student is None:
        raise ForbiddenException("找不到對應的學生資料，無法上傳")

    if not (file.filename or "").lower().endswith(".json"):
        raise BadRequestException("只接受 .json 格式的檔案")

    raw_bytes = await file.read()
    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise BadRequestException(f"JSON 格式錯誤：{e}")

    parsed = parse_student_data(data)
    uploaded_sid = parsed["student_info"].get("student_id")
    if uploaded_sid != student.student_id:
        raise ForbiddenException(
            f"上傳資料的學號（{uploaded_sid or '空白'}）與登入帳號（{student.student_id}）不符，無法匯入"
        )

    try:
        student, course_count = import_parsed_for_student(db, parsed, student)
    except ValueError as e:
        raise BadRequestException(str(e))

    return {
        "student_id": student.student_id,
        "student_number": student.student_id,
        "chinese_name": student.name,
        "course_count": course_count,
    }
