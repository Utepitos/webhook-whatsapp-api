from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    whatsapp_token: str = ""
    whatsapp_phone_id: str = ""
    whatsapp_verify_token: str = "beneficios_ya_verify_2024"
    port: int = 8000
    debug: bool = False
    documents_path: str = "./documents"

    model_config = {"env_file": ".env", "case_sensitive": False}

    @property
    def has_whatsapp(self) -> bool:
        return bool(self.whatsapp_token and self.whatsapp_phone_id)

    @property
    def has_claude(self) -> bool:
        return bool(self.anthropic_api_key and self.anthropic_api_key != "your_claude_api_key_here")

    @property
    def documents_dir(self) -> Path:
        return Path(self.documents_path)


settings = Settings()
