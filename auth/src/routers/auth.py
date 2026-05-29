import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_account, get_session, oauth2_scheme
from ..models import AccountInfo, AdminRegisterRequest, LoginRequest, StudentRegisterRequest, TokenResponse
from ..tables import Account, Administrator, Student, Token

router = APIRouter()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Account).where(Account.email == body.email))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token_str = secrets.token_urlsafe(32)
    session.add(Token(account_id=account.id, token=token_str))
    await session.commit()
    return {"access_token": token_str, "role": account.role}


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
):
    await session.execute(delete(Token).where(Token.token == token))
    await session.commit()
    return {"message": "Logged out"}


@router.post("/register/student", response_model=AccountInfo, status_code=status.HTTP_201_CREATED)
async def register_student(body: StudentRegisterRequest, session: AsyncSession = Depends(get_session)):
    account = Account(
        email=body.email,
        password_hash=pwd_context.hash(body.password),
        role="student",
    )
    session.add(account)
    try:
        await session.flush()
        session.add(Student(
            student_id=body.student_id,
            user_id=account.id,
            name=body.name,
            admission_year=body.admission_year,
        ))
        await session.commit()
        await session.refresh(account)
        return AccountInfo.model_validate(account)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Email or student ID already exists")


@router.post("/register/admin", response_model=AccountInfo, status_code=status.HTTP_201_CREATED)
async def register_admin(body: AdminRegisterRequest, session: AsyncSession = Depends(get_session)):
    account = Account(
        email=body.email,
        password_hash=pwd_context.hash(body.password),
        role="admin",
    )
    session.add(account)
    try:
        await session.flush()
        session.add(Administrator(id=account.id, department_id=body.department_id))
        await session.commit()
        await session.refresh(account)
        return AccountInfo.model_validate(account)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Email already exists or department not found")


@router.get("/status", response_model=AccountInfo)
async def get_status(current: Account = Depends(get_current_account)):
    return AccountInfo.model_validate(current)


@router.delete("/user/{account_id}")
async def delete_user(
    account_id: uuid.UUID,
    current: Account = Depends(get_current_account),
    session: AsyncSession = Depends(get_session),
):
    if current.id != account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    await session.delete(current)
    await session.commit()
    return {"message": "Account deleted"}
