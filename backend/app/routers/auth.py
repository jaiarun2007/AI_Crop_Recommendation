from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["authentication"])
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    email = auth_service.decode_access_token(credentials.credentials)
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = auth_service.get_user_by_email(db, email)
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Create an account (bcrypt-hashed password) and return a JWT",
)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    if auth_service.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = auth_service.create_user(db, payload.email, payload.password, payload.full_name)
    token = auth_service.create_access_token(user.email)
    return {"access_token": token, "user": user}


@router.post("/login", response_model=TokenResponse, summary="Exchange email/password for a JWT")
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = auth_service.create_access_token(user.email)
    return {"access_token": token, "user": user}


@router.get("/me", response_model=UserResponse, summary="Get the current authenticated user")
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
