from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    UserUpdateRequest,
)
from app.schemas.common import MeResponse, TokenResponse, UserRead
from app.services.auth_service import AuthService
from app.services.organization_service import OrganizationService
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    return AuthService(db).register(payload, _client_ip(request))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    return AuthService(db).login(payload, _client_ip(request))


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return AuthService(db).refresh(payload.refresh_token)


@router.post("/logout", status_code=204)
def logout(payload: LogoutRequest, request: Request, db: Session = Depends(get_db)) -> None:
    AuthService(db).logout(payload.refresh_token, _client_ip(request))


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MeResponse:
    return MeResponse(user=UserRead.model_validate(user), organizations=OrganizationService(db).list_visible(user))


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    return AuthService(db).update_profile(user, payload)


@router.post("/change-password", status_code=204)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    AuthService(db).change_password(user, payload, _client_ip(request))
