from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and return an access token",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    service.register(email=payload.email, password=payload.password, full_name=payload.full_name)
    token = service.authenticate(email=payload.email, password=payload.password)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse, summary="Exchange credentials for a token")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    token = AuthService(db).authenticate(email=payload.email, password=payload.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse, summary="Current authenticated user")
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
