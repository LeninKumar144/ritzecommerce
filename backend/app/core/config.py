"""Application settings loaded from the environment."""

from decimal import Decimal
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "product_shopping_db"
    db_username: str = ""
    db_password: str = ""
    jwt_secret: str = ""
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_minutes: int = 10080
    login_rate_limit: int = 20
    login_rate_window_seconds: int = 60
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"
    shop_name: str = "Ritz"
    default_tax_rate: Decimal = Decimal("18.00")
    delivery_fee: Decimal = Decimal("49.00")
    free_delivery_threshold: Decimal = Decimal("999.00")
    stock_reservation_minutes: int = 15
    upload_dir: str = "uploads"
    max_upload_bytes: int = 5_242_880
    admin_email: str = ""
    admin_password: str = ""
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle_seconds: int = 3600

    @property
    def database_url(self) -> str:
        username = quote_plus(self.db_username)
        password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{username}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
