from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.auth import UserRegister, UserLogin, UserOut, TokenOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    svc = AuthService(db)
    user = svc.register(payload.username, payload.email, payload.phone, payload.full_name, payload.password)
    token = svc.create_token(user.id)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    svc = AuthService(db)
    user = svc.authenticate(payload.username, payload.password)
    token = svc.create_token(user.id)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(authorization: str = Header(...), db: Session = Depends(get_db)):
    token = authorization.replace("Bearer ", "")
    svc = AuthService(db)
    user_id = svc.decode_token(token)
    user = svc.get_user_by_id(user_id)
    return UserOut.model_validate(user)
