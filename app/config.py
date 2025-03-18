from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения с настройками базы данных.

    Атрибуты:
        DATABASE_URL (str): URL основной базы данных.
        TEST_DATABASE_URL (str): URL тестовой базы данных.
    """
    DATABASE_URL: str
    TEST_DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
