"""Insert a small local catalog when those SKUs are not already present."""

import io
import struct
import zlib
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Category
from app.schemas.catalog import CategoryCreate, ProductCreate
from app.services.catalog import CatalogService


def _png(red: int, green: int, blue: int, size: int = 64) -> bytes:
    raw = b"".join(b"\x00" + bytes((red, green, blue)) * size for _ in range(size))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


class _BytesUpload:
    def __init__(self, content: bytes) -> None:
        self.file = io.BytesIO(content)


def main() -> None:
    groups = [
        (
            "Apparel",
            "apparel",
            "Shirts and everyday cotton.",
            (156, 78, 46),
            [
                ("Linen shirt", "RITZ-LINEN", "Ritz", "Breathable linen shirt.", {"fabric": "linen"}, Decimal("1899.00"), Decimal("10.00"), 12, True),
                ("Cotton tee", "RITZ-TEE", "Ritz", "Everyday cotton tee.", {"fabric": "cotton"}, Decimal("799.00"), Decimal("0.00"), 20, False),
            ],
        ),
        (
            "Home",
            "home",
            "Goods for the table.",
            (63, 83, 68),
            [
                ("Stoneware bowl", "RITZ-BOWL", "Hearth", "A bowl for fruit or rice.", {"material": "stoneware"}, Decimal("649.00"), Decimal("5.00"), 8, True),
            ],
        ),
    ]
    with SessionLocal() as session:
        service = CatalogService(session)
        for name, slug, description, color, products in groups:
            category = session.scalar(select(Category).where(Category.slug == slug))
            if category is None:
                category = service.create_category(CategoryCreate(name=name, slug=slug, description=description))
                upload = _BytesUpload(_png(*color))
                category.image_url = service._store_category_image(category.id, upload)  # noqa: SLF001
                session.commit()
            for product_name, sku, brand, body, specs, price, discount, stock, featured in products:
                if service.products.get_by_sku(sku):
                    continue
                created = service.create_product(
                    ProductCreate(
                        name=product_name,
                        sku=sku,
                        category_id=category.id,
                        brand=brand,
                        description=body,
                        specifications=specs,
                        price=price,
                        discount_percent=discount,
                        stock_quantity=stock,
                        is_featured=featured,
                    )
                )
                service.add_image(created.id, _BytesUpload(_png(*color)), product_name, True)
    print("Catalog seed complete")


if __name__ == "__main__":
    main()
