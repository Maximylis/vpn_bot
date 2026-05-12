from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    vpn_manager_api_token: str

    wg_apply_changes: bool = False
    wg_interface: str = "wg0"
    wg_network: str = "10.0.0.0/24"
    wg_server_public_key: str
    wg_endpoint: str
    wg_client_dns: str = "1.1.1.1"
    wg_client_allowed_ips: str = "0.0.0.0/0"
    wg_state_dir: str = "/var/lib/vpn-manager/peers"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
