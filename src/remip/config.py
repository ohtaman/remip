from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REMIP_")

    solver_path: str = "scip"

settings = Settings()
