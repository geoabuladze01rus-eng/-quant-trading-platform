from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    paper_trading: bool = True
    max_daily_loss_pct: float = 2.0
    max_portfolio_exposure_pct: float = 60.0
    max_position_pct: float = 10.0


settings = Settings()
