from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from keycloak import KeycloakOpenID

keycloak_openid = KeycloakOpenID(
    server_url=settings.KEYCLOAK_SERVER_URL,
    client_id=settings.KEYCLOAK_CLIENT_ID,
    realm_name=settings.KEYCLOAK_REALM_NAME,
    client_secret_key=settings.KEYCLOAK_CLIENT_SECRET_KEY
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Security(oauth2_scheme)):
    try:
        user_claims = keycloak_openid.decode_token(token)
        if( not user_claims.get('sub')):
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "id": user_claims.get('sub'),
            "email": user_claims.get('email'),
            "name": user_claims.get('name'),
        }
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
