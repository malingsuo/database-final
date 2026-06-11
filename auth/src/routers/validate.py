import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..cache import token_get, token_set
from ..dependencies import get_session, oauth2_scheme
from ..tables import Account, Token

router = APIRouter()


@router.get("/auth/validate")
async def validate(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
):
    account_id = await token_get(token)
    if account_id:
        return JSONResponse(
            content={"status": "ok"},
            headers={"X-Account-ID": account_id},
        )

    result = await session.execute(
        select(Account).join(Token, Token.account_id == Account.id).where(Token.token == token)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    await token_set(token, str(account.id))
    return JSONResponse(
        content={"status": "ok"},
        headers={"X-Account-ID": str(account.id)},
    )
