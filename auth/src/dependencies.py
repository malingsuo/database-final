import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .cache import token_get, token_set
from .database import AsyncSessionLocal
from .tables import Account, Token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_account(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> Account:
    account_id = await token_get(token)
    if account_id:
        account = await session.get(Account, uuid.UUID(account_id))
        if account:
            return account

    result = await session.execute(
        select(Account).join(Token, Token.account_id == Account.id).where(Token.token == token)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    await token_set(token, str(account.id))
    return account
