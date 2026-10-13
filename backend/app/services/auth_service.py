from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db import User
from app.exceptions import PlatformError, ConflictError, NotFoundError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "irctc-platform-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, username: str, email: str, phone: str, full_name: str, password: str) -> User:
        if self.db.query(User).filter(User.username == username).first():
            raise ConflictError(f"Username '{username}' already taken")
        if self.db.query(User).filter(User.email == email).first():
            raise ConflictError(f"Email '{email}' already registered")
        user = User(
            username=username,
            email=email,
            phone=phone,
            full_name=full_name,
            hashed_password=pwd_context.hash(password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, username: str, password: str) -> User:
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not pwd_context.verify(password, user.hashed_password):
            raise PlatformError("Invalid username or password", status_code=401)
        return user

    def get_user_by_id(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        return user

    @staticmethod
    def create_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> int:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return int(payload["sub"])
        except jwt.ExpiredSignatureError:
            raise PlatformError("Token expired", status_code=401)
        except jwt.InvalidTokenError:
            raise PlatformError("Invalid token", status_code=401)
