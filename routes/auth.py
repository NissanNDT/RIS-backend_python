import os
from datetime import datetime, timedelta
import bcrypt
import jwt
from fastapi import APIRouter, HTTPException, status
from config.db import query_db
from models.schemas import LoginRequest

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "mi_clave_super_segura")

@router.post("/login")
def login(payload: LoginRequest):
    # Retrieve user
    user = query_db("SELECT * FROM users WHERE email = %s", [payload.email], fetch_one=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Credenciales inválidas"}
        )
    
    # Check bcrypt password
    try:
        pw_hash = user['password']
        if isinstance(pw_hash, memoryview):
            pw_hash = pw_hash.tobytes().decode('utf-8')
        elif isinstance(pw_hash, bytes):
            pw_hash = pw_hash.decode('utf-8')
            
        is_valid = bcrypt.checkpw(payload.password.encode('utf-8'), pw_hash.encode('utf-8'))
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Credenciales inválidas"}
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Credenciales inválidas"}
        )
        
    # Get role name
    role = query_db("SELECT name FROM role WHERE id = %s", [user['id_role']], fetch_one=True)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Rol no encontrado"}
        )
        
    # Build JWT token payload
    # Expires in 1 hour
    exp_time = datetime.utcnow() + timedelta(hours=1)
    jwt_payload = {
        "id": user['id'],
        "email": user['email'],
        "role": role['name'],
        "name": user['full_name'],
        "exp": exp_time
    }
    
    token = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")
    
    return {
        "message": "Login exitoso",
        "user": {
            "id": user['id'],
            "role": role['name'],
            "name": user['full_name']
        },
        "token": token
    }

@router.post("/logout")
def logout():
    return {"message": "Sesión cerrada"}
