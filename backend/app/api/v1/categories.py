"""Public category routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.db.session import get_db
from app.models import User
from app.models.enums import RoleName
from app.schemas.catalog import CategoryPublic
from app.services.catalog import CatalogError, CatalogService

router = APIRouter(prefix="/categories", tags=["categories"])


def _is_admin(user: User | None) -> bool:
    return user is not None and user.role.name == RoleName.ADMIN.value


@router.get("", response_model=list[CategoryPublic])
def list_categories(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> list[CategoryPublic]:
    return CatalogService(db).list_categories(include_inactive=_is_admin(user))


@router.get("/{slug}", response_model=CategoryPublic)
def get_category(
    slug: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> CategoryPublic:
    try:
        category = CatalogService(db).get_category(slug, include_inactive=_is_admin(user))
    except CatalogError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return CategoryPublic.model_validate(category, from_attributes=True)
