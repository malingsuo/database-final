"""
將 exportStudentData.json 裡的學生資料塞進 DB，用於測試 /check/{sid} endpoint。
用法：
  cd /Users/pengqize/Documents/code/db/database-final
  uv run python scripts/seed_test_student.py
"""
import json
import sys
import os

# 讓 backend src 可以 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from src.core.database import SessionLocal
from src.services.importer import parse_student_data, import_parsed_for_student
from src.models import Account, Student
from sqlalchemy import select
import uuid

DATA_PATH = os.path.expanduser(
    "~/Documents/code/NCCU-AI-SYSTEM/scheduling_test/data/exportStudentData.json"
)

def main():
    with open(DATA_PATH) as f:
        students_raw = json.load(f)

    db = SessionLocal()
    try:
        for raw in students_raw:
            parsed = parse_student_data(raw)
            info = parsed["student_info"]
            sid = info.get("student_id")
            if not sid:
                print(f"  skip: no student_id")
                continue

            # 確認/建立 account
            student = db.get(Student, sid)
            if student is None:
                account = Account(
                    id=uuid.uuid4(),
                    email=f"{sid}@test.nccu.edu.tw",
                    password_hash="$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$RdescudvJCsgt3ub+b27Gli694kX9aDMRA31tWBmVPU",
                    role="student",
                )
                db.add(account)
                db.flush()

                student = Student(
                    student_id=sid,
                    user_id=account.id,
                    name=info.get("chinese_name", ""),
                    admission_year=info.get("entry_year", 112),
                )
                db.add(student)
                db.flush()

            count, _ = import_parsed_for_student(db, parsed, student)
            db.commit()
            print(f"  ✅ {sid} {info.get('chinese_name','')} — {count} 筆 enrollment")

    except Exception as e:
        db.rollback()
        print(f"  ❌ {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
