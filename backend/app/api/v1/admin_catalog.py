"""Admin catalog management."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import User
from app.schemas.catalog import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    InventoryUpdate,
    ProductCreate,
    ProductImageRead,
    ProductRead,
    ProductUpdate,
)
from app.services.catalog import CatalogError, CatalogService

router = APIRouter(prefix="/admin", tags=["admin-catalog"], dependencies=[Depends(require_admin)])


def _raise(exc: CatalogError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


async def _category_form(request: Request) -> tuple[dict, UploadFile | None]:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type:
        return await request.json(), None
    form = await request.form()
    payload = {
        "name": form.get("name"),
        "description": form.get("description") or None,
        "image_url": form.get("image_url") or None,
        "is_active": str(form.get("is_active", "true")).lower() not in {"false", "0"},
    }
    slug = form.get("slug")
    if slug:
        payload["slug"] = slug
    upload = form.get("file")
    if upload is not None and not hasattr(upload, "read"):
        upload = None
    return payload, upload


@router.post("/categories", response_model=CategoryRead, status_code=201)
async def create_category(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> CategoryRead:
    payload, upload = await _category_form(request)
    try:
        category = CatalogService(db).create_category(CategoryCreate.model_validate(payload), upload)
    except CatalogError as exc:
        _raise(exc)
    return CategoryRead.model_validate(category, from_attributes=True)


@router.patch("/categories/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> CategoryRead:
    content_type = request.headers.get("content-type", "")
    upload = None
    if "multipart/form-data" in content_type:
        payload, upload = await _category_form(request)
        data = CategoryUpdate.model_validate(payload)
    else:
        data = CategoryUpdate.model_validate(await request.json())
    try:
        category = CatalogService(db).update_category(category_id, data, upload)
    except CatalogError as exc:
        _raise(exc)
    return CategoryRead.model_validate(category, from_attributes=True)


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> Response:
    try:
        CatalogService(db).delete_category(category_id)
    except CatalogError as exc:
        _raise(exc)
    return Response(status_code=204)


@router.post("/products", response_model=ProductRead, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> ProductRead:
    try:
        product = CatalogService(db).create_product(data)
    except CatalogError as exc:
        _raise(exc)
    return ProductRead.model_validate(product, from_attributes=True)


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ProductRead:
    try:
        product = CatalogService(db).update_product(product_id, data)
    except CatalogError as exc:
        _raise(exc)
    return ProductRead.model_validate(product, from_attributes=True)


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    try:
        product = CatalogService(db).retire_product(product_id)
    except CatalogError as exc:
        _raise(exc)
    if product is None:
        return Response(status_code=204)
    return ProductRead.model_validate(product, from_attributes=True)


@router.patch("/products/{product_id}/inventory", response_model=ProductRead)
def update_inventory(
    product_id: int,
    data: InventoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ProductRead:
    try:
        product = CatalogService(db).update_inventory(product_id, data)
    except CatalogError as exc:
        _raise(exc)
    return ProductRead.model_validate(product, from_attributes=True)


@router.post("/products/{product_id}/images", response_model=ProductImageRead, status_code=201)
def add_image(
    product_id: int,
    file: UploadFile = File(...),
    alt_text: str | None = Form(default=None),
    is_primary: bool = Form(default=False),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ProductImageRead:
    try:
        image = CatalogService(db).add_image(product_id, file, alt_text, is_primary)
    except CatalogError as exc:
        _raise(exc)
    return ProductImageRead.model_validate(image, from_attributes=True)


@router.delete("/products/{product_id}/images/{image_id}", status_code=204)
def delete_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Response:
    try:
        CatalogService(db).delete_image(product_id, image_id)
    except CatalogError as exc:
        _raise(exc)
    return Response(status_code=204)
