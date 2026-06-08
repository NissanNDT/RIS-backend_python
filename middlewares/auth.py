import os
import jwt
from fastapi import Request, HTTPException, status

JWT_SECRET = os.getenv("JWT_SECRET", "mi_clave_super_segura")

def verify_token(request: Request):
    """
    Dependency that verifies the Authorization header token.
    Stores the decoded payload in request.state.user.
    """
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Token no proporcionado"}
        )
    
    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Token inválido o expirado"}
        )
    
    token = parts[1]
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        request.state.user = decoded
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Token inválido o expirado"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Token inválido o expirado"}
        )
