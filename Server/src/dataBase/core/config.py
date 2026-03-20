

from pydantic import BaseModel
from pydantic_settings import BaseSettings
from pathlib import Path


class AuthJWT(BaseModel):
    private_key_path: Path = Path("Server\certs\jwt-private.pem")
    public_key_path: Path = Path("Server\certs\jwt-public.pem")
    algorithm: str = "RS256"
    TOKEN_TYPE: str = "Bearer"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 21

class Setting(BaseSettings):
    api_v1_prefix: str = "/api/v1"

    db_url: str = "sqlite+aiosqlite:///./db.sqlite3"
    db_echo: bool = True
    
    auth_JWT: AuthJWT = AuthJWT()
    
settings = Setting()