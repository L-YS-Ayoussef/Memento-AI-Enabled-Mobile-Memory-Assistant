from jose import JWTError, jwt
from app.settings import settings
import datetime
from ..schemas import schemas
from fastapi import HTTPException, status, Depends, WebSocket
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_EXPIRATION_TIME



# ==================== HTTP Requests ==================== #

def create_access_token(data: dict):
    to_encode = data.copy()

    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(weeks=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expires})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def verify_access_token(token: str, credentials_exception) -> Optional[schemas.TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = str(payload.get("user_id"))
        if user_id is None:
            raise credentials_exception
        user_data = schemas.TokenData(user_id=user_id)
        return user_data
    except JWTError:
        raise credentials_exception


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_access_token(token, credentials_exception)


# ==================== WebSockets ==================== #

async def verify_access_token_ws(token: str, websocket: WebSocket) -> Optional[schemas.TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = str(payload.get("user_id"))
        if user_id is None:
            await websocket.send_json({"error": "Invalid token: missing user_id"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        return schemas.TokenData(user_id=user_id)

    except JWTError:
        await websocket.send_json({"error": "Invalid or expired token"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None


async def get_current_user_ws(websocket: WebSocket) -> Optional[schemas.TokenData]:
    token = websocket.headers.get("Authorization")
    if not token:
        await websocket.send_json({"error": "Authorization header missing"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    token = token.split(" ")[1]  # Extract the token part after "Bearer"
    
    return await verify_access_token_ws(token, websocket)