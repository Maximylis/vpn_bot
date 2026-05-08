from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    vpn_manager_api_token: str

    wg_interface: str = "wg0"
    wg_server_public_key: str
    wg_endpoint: str
    wg_client_dns: str = "1.1.1.1"
    wg_client_allowed_ips: str = "0.0.0.0/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
