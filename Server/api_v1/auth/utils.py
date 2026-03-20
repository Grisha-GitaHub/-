import bcrypt
import jwt
from pathlib import Path
from src.dataBase.core.config import settings


def encode_jwt(
    payload: dict, 
    private_key: Path = settings.auth_JWT.private_key_path.read_text(), 
    algorithm: Path = settings.auth_JWT.algorithm
):
    encoded = jwt.encode(
        payload, 
        private_key, 
        algorithm=algorithm,
    )
    return encoded


def decoded_jwt(
    token: str | bytes, 
    public_key: str = settings.auth_JWT.public_key_path.read_text(), 
    algorithm: str = settings.auth_JWT.algorithm,
):
    
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=[algorithm]
    )
    return decoded


def hash_password(
    password: str,
) -> bytes:
    salt = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def validate_password(
    password: str,
    hashed_password: bytes,
) -> bool:
    return bcrypt.checkpw(
        password=password.encode(),
        hashed_password=hashed_password.encode('utf-8'),
    )