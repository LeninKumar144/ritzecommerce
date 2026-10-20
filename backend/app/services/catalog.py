"""Catalog queries and writes."""

from decimal import Decimal, ROUND_HALF_UP

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import Category, OrderItem, Product, ProductImage, Review, User
from app.repositories.catalog import CategoryRepository, ProductRepository
from app.schemas.catalog import (
    CategoryCreate,
    CategoryPublic,
    CategoryUpdate,
    InventoryUpdate,
    ProductCard,
    ProductCreate,
    ProductDetail,
    ProductImageRead,
    ProductList,
    ProductUpdate,
    ReviewCard,
)
from app.utils.images import UploadRejected, delete_stored_file, save_image
from app.utils.slug import slugify


class CatalogError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail


def selling_price(price: Decimal, discount_percent: Decimal) -> Decimal:
    amount = price * (Decimal("100") - discount_percent) / Decimal("100")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _card(product: Product) -> ProductCard:
    images = sorted(product.images, key=lambda image: (not image.is_primary, image.sort_order, image.id))
    return ProductCard(
        id=product.id,
        name=product.name,
        slug=product.slug,
        brand=product.brand,
        image_url=images[0].url if images else None,
        list_price=product.price,
        selling_price=selling_price(product.price, product.discount_percent),
        discount_percent=product.discount_percent,
        in_stock=product.stock_quantity > 0,
    )


class CatalogService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.categories = CategoryRepository(session)
        self.products = ProductRepository(session)

    def list_categories(self, *, include_inactive: bool) -> list[CategoryPublic]:
        statement = select(Category).order_by(Category.name)
        if not include_inactive:
            statement = statement.where(Category.is_active.is_(True))
        rows = self.session.scalars(statement)
        return [CategoryPublic.model_validate(row, from_attributes=True) for row in rows]

    def get_category(self, slug: str, *, include_inactive: bool) -> Category:
        category = self.session.scalar(select(Category).where(Category.slug == slug))
        if category is None or (not category.is_active and not include_inactive):
            raise CatalogError(404, "Category not found")
        return category

    def create_category(self, data: CategoryCreate, upload: UploadFile | None = None) -> Category:
        self._ensure_category_available(data.name, data.slug)
        category = Category(
            name=data.name.strip(),
            slug=self._unique_category_slug(data.slug or slugify(data.name)),
            description=data.description,
            image_url=data.image_url,
            is_active=data.is_active,
        )
        self.categories.add(category)
        self.session.flush()
        if upload is not None:
            category.image_url = self._store_category_image(category.id, upload)
        self._commit()
        self.session.refresh(category)
        return category

    def update_category(self, category_id: int, data: CategoryUpdate, upload: UploadFile | None = None) -> Category:
        category = self._category_by_id(category_id)
        changes = data.model_dump(exclude_unset=True)
        if "name" in changes and changes["name"] != category.name:
            self._ensure_category_available(changes["name"], None, ignore_id=category.id)
            category.name = changes["name"].strip()
        if "slug" in changes and changes["slug"]:
            category.slug = self._unique_category_slug(changes["slug"], ignore_id=category.id)
        if "description" in changes:
            category.description = changes["description"]
        if "image_url" in changes:
            category.image_url = changes["image_url"]
        if "is_active" in changes:
            category.is_active = changes["is_active"]
        if upload is not None:
            delete_stored_file(category.image_url)
            category.image_url = self._store_category_image(category.id, upload)
        self._commit()
        self.session.refresh(category)
        return category

    def delete_category(self, category_id: int) -> None:
        category = self._category_by_id(category_id)
        product_count = self.session.scalar(
            select(func.count()).select_from(Product).where(Product.category_id == category.id)
        )
        if product_count:
            raise CatalogError(409, "Category still has products")
        delete_stored_file(category.image_url)
        self.session.delete(category)
        self._commit()

    def list_brands(self) -> list[str]:
        statement = (
            select(Product.brand)
            .where(Product.is_active.is_(True))
            .distinct()
            .order_by(Product.brand)
        )
        return list(self.session.scalars(statement))

    def list_products(
        self,
        *,
        search: str | None,
        category: str | None,
        brand: str | None,
        min_price: Decimal | None,
        max_price: Decimal | None,
        in_stock: bool | None,
        featured: bool | None,
        sort: str,
        page: int,
        page_size: int,
    ) -> ProductList:
        statement = select(Product).join(Category).where(Product.is_active.is_(True), Category.is_active.is_(True))
        statement = self._apply_product_filters(
            statement,
            search=search,
            category=category,
            brand=brand,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            featured=featured,
        )
        total = self.session.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
        page_statement = (
            self._apply_sort(statement, sort)
            .options(selectinload(Product.images))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [_card(product) for product in self.session.scalars(page_statement).unique()]
        return ProductList(items=items, page=page, page_size=page_size, total=total)

    def get_product(self, slug: str, *, include_inactive: bool, review_page: int, review_page_size: int) -> ProductDetail:
        statement = select(Product).options(selectinload(Product.images)).where(Product.slug == slug)
        product = self.session.scalar(statement)
        if product is None or (not product.is_active and not include_inactive):
            raise CatalogError(404, "Product not found")
        review_total = self.session.scalar(
            select(func.count()).select_from(Review).where(Review.product_id == product.id)
        ) or 0
        review_rows = self.session.execute(
            select(Review, User.full_name)
            .join(User, Review.user_id == User.id)
            .where(Review.product_id == product.id)
            .order_by(Review.created_at.desc())
            .offset((review_page - 1) * review_page_size)
            .limit(review_page_size)
        ).all()
        card = _card(product)
        gallery = [
            ProductImageRead.model_validate(image, from_attributes=True)
            for image in sorted(product.images, key=lambda image: (image.sort_order, image.id))
        ]
        return ProductDetail(
            **card.model_dump(),
            sku=product.sku,
            description=product.description,
            specifications=product.specifications or {},
            tax_rate=product.tax_rate,
            stock_quantity=product.stock_quantity,
            gallery=gallery,
            reviews=[
                ReviewCard(
                    id=review.id,
                    rating=review.rating,
                    title=review.title,
                    body=review.body,
                    author_name=author_name,
                )
                for review, author_name in review_rows
            ],
            review_page=review_page,
            review_total=review_total,
        )

    def create_product(self, data: ProductCreate) -> Product:
        self._category_by_id(data.category_id)
        self._ensure_sku(data.sku)
        product = Product(
            category_id=data.category_id,
            name=data.name.strip(),
            slug=self._unique_product_slug(data.slug or slugify(data.name, 220)),
            sku=data.sku.strip(),
            brand=data.brand.strip(),
            description=data.description,
            specifications=data.specifications,
            price=data.price,
            discount_percent=data.discount_percent,
            tax_rate=data.tax_rate,
            stock_quantity=data.stock_quantity,
            is_active=data.is_active,
            is_featured=data.is_featured,
        )
        self.products.add(product)
        self._commit()
        self.session.refresh(product)
        return product

    def update_product(self, product_id: int, data: ProductUpdate) -> Product:
        product = self._product_by_id(product_id)
        changes = data.model_dump(exclude_unset=True)
        if "category_id" in changes:
            self._category_by_id(changes["category_id"])
            product.category_id = changes["category_id"]
        if "sku" in changes and changes["sku"] != product.sku:
            self._ensure_sku(changes["sku"], ignore_id=product.id)
            product.sku = changes["sku"].strip()
        if "slug" in changes and changes["slug"]:
            product.slug = self._unique_product_slug(changes["slug"], ignore_id=product.id)
        for field in (
            "name",
            "brand",
            "description",
            "specifications",
            "price",
            "discount_percent",
            "tax_rate",
            "stock_quantity",
            "is_active",
            "is_featured",
        ):
            if field in changes:
                setattr(product, field, changes[field])
        self._commit()
        self.session.refresh(product)
        return product

    def retire_product(self, product_id: int) -> Product | None:
        product = self._product_by_id(product_id)
        order_count = self.session.scalar(
            select(func.count()).select_from(OrderItem).where(OrderItem.product_id == product.id)
        )
        if order_count:
            product.is_active = False
            self._commit()
            self.session.refresh(product)
            return product
        for image in list(product.images):
            delete_stored_file(image.url)
        self.session.delete(product)
        self._commit()
        return None

    def update_inventory(self, product_id: int, data: InventoryUpdate) -> Product:
        product = self._product_by_id(product_id)
        product.stock_quantity = data.stock_quantity
        self._commit()
        self.session.refresh(product)
        return product

    def add_image(self, product_id: int, upload: UploadFile, alt_text: str | None, is_primary: bool) -> ProductImage:
        product = self._product_by_id(product_id)
        url = self._store_product_image(product.id, upload)
        if is_primary or not product.images:
            for image in product.images:
                image.is_primary = False
            is_primary = True
        image = ProductImage(
            product_id=product.id,
            url=url,
            alt_text=alt_text,
            sort_order=len(product.images),
            is_primary=is_primary,
        )
        self.session.add(image)
        self._commit()
        self.session.refresh(image)
        return image

    def delete_image(self, product_id: int, image_id: int) -> None:
        product = self._product_by_id(product_id)
        image = next((item for item in product.images if item.id == image_id), None)
        if image is None:
            raise CatalogError(404, "Image not found")
        was_primary = image.is_primary
        delete_stored_file(image.url)
        self.session.delete(image)
        self.session.flush()
        if was_primary:
            replacement = self.session.scalar(
                select(ProductImage)
                .where(ProductImage.product_id == product.id)
                .order_by(ProductImage.sort_order, ProductImage.id)
            )
            if replacement is not None:
                replacement.is_primary = True
        self._commit()

    def _apply_product_filters(self, statement, **filters):
        price = Product.price * (100 - Product.discount_percent) / 100
        if filters["search"]:
            term = f"%{filters['search'].strip()}%"
            statement = statement.where(or_(Product.name.like(term), Product.brand.like(term), Product.sku.like(term)))
        if filters["category"]:
            statement = statement.where(Category.slug == filters["category"])
        if filters["brand"]:
            statement = statement.where(Product.brand == filters["brand"])
        if filters["min_price"] is not None:
            statement = statement.where(price >= filters["min_price"])
        if filters["max_price"] is not None:
            statement = statement.where(price <= filters["max_price"])
        if filters["in_stock"] is True:
            statement = statement.where(Product.stock_quantity > 0)
        elif filters["in_stock"] is False:
            statement = statement.where(Product.stock_quantity == 0)
        if filters["featured"] is True:
            statement = statement.where(Product.is_featured.is_(True))
        return statement

    def _apply_sort(self, statement, sort: str):
        price = Product.price * (100 - Product.discount_percent) / 100
        if sort == "price_asc":
            return statement.order_by(price.asc(), Product.id.asc())
        if sort == "price_desc":
            return statement.order_by(price.desc(), Product.id.asc())
        if sort == "name":
            return statement.order_by(Product.name.asc(), Product.id.asc())
        if sort == "popular":
            review_count = (
                select(func.count(Review.id))
                .where(Review.product_id == Product.id)
                .correlate(Product)
                .scalar_subquery()
            )
            return statement.order_by(review_count.desc(), Product.created_at.desc())
        return statement.order_by(Product.created_at.desc(), Product.id.desc())

    def _store_category_image(self, category_id: int, upload: UploadFile) -> str:
        try:
            return save_image(upload, f"categories/{category_id}")
        except UploadRejected as exc:
            raise CatalogError(400, exc.detail) from exc

    def _store_product_image(self, product_id: int, upload: UploadFile) -> str:
        try:
            return save_image(upload, f"products/{product_id}")
        except UploadRejected as exc:
            raise CatalogError(400, exc.detail) from exc

    def _category_by_id(self, category_id: int) -> Category:
        category = self.session.get(Category, category_id)
        if category is None:
            raise CatalogError(404, "Category not found")
        return category

    def _product_by_id(self, product_id: int) -> Product:
        product = self.session.scalar(
            select(Product).options(selectinload(Product.images)).where(Product.id == product_id)
        )
        if product is None:
            raise CatalogError(404, "Product not found")
        return product

    def _ensure_category_available(self, name: str, slug: str | None, ignore_id: int | None = None) -> None:
        existing = self.session.scalar(select(Category).where(Category.name == name))
        if existing is not None and existing.id != ignore_id:
            raise CatalogError(409, "Category name already exists")
        if slug:
            taken = self.session.scalar(select(Category).where(Category.slug == slug))
            if taken is not None and taken.id != ignore_id:
                raise CatalogError(409, "Slug already exists")

    def _ensure_sku(self, sku: str, ignore_id: int | None = None) -> None:
        existing = self.products.get_by_sku(sku)
        if existing is not None and existing.id != ignore_id:
            raise CatalogError(409, "SKU already exists")

    def _unique_category_slug(self, slug: str, ignore_id: int | None = None) -> str:
        base = slugify(slug)
        return self._unique_slug(Category.slug, Category.id, base, ignore_id)

    def _unique_product_slug(self, slug: str, ignore_id: int | None = None) -> str:
        base = slugify(slug, 220)
        return self._unique_slug(Product.slug, Product.id, base, ignore_id)

    def _unique_slug(self, column, id_column, base: str, ignore_id: int | None) -> str:
        candidate = base
        suffix = 2
        while True:
            existing = self.session.scalar(select(id_column).where(column == candidate))
            if existing is None or existing == ignore_id:
                return candidate
            trimmed = base[: max(1, len(base) - len(str(suffix)) - 1)]
            candidate = f"{trimmed}-{suffix}"
            suffix += 1

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise CatalogError(409, "Catalog record already exists") from exc
