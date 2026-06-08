import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from config.db import query_db
from middlewares.auth import verify_token
from models.schemas import UserCreate, UserUpdate

router = APIRouter()

@router.get("/get/users", dependencies=[Depends(verify_token)])
def get_users():
    try:
        users = query_db(
            "SELECT id, id_plant, full_name, email, created_at, id_role FROM users ORDER BY created_at DESC",
            fetch_all=True
        )
        return users
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al obtener usuarios", "detalle": str(error)}
        )

@router.get("/users/{id}", dependencies=[Depends(verify_token)])
def get_user_by_id(id: int):
    try:
        user = query_db(
            "SELECT id, id_plant, full_name, email, created_at, id_role FROM users WHERE id = %s",
            [id],
            fetch_one=True
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Usuario no encontrado"}
            )
        return user
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al obtener usuario", "detalle": str(error)}
        )

@router.post("/users", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_user(payload: UserCreate):
    try:
        hashed_password = bcrypt.hashpw(payload.password.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')
        user = query_db(
            """INSERT INTO users (id_plant, full_name, email, password, id_role)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id, id_plant, full_name, email, created_at, id_role""",
            [payload.id_plant, payload.full_name, payload.email, hashed_password, payload.id_role],
            fetch_one=True
        )
        return {
            "mensaje": "Usuario creado correctamente",
            "usuario": user
        }
    except Exception as error:
        err_msg = str(error)
        if "duplicate key" in err_msg or "23505" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "El correo ya está registrado"}
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al registrar usuario", "detalle": err_msg}
        )

@router.put("/put/users/{id}", dependencies=[Depends(verify_token)])
def update_user(id: int, payload: UserUpdate):
    try:
        current = query_db("SELECT * FROM users WHERE id = %s", [id], fetch_one=True)
        if not current:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Usuario no encontrado"}
            )

        fields_to_update = {}
        if payload.id_plant is not None:
            fields_to_update["id_plant"] = payload.id_plant
        if payload.full_name is not None:
            fields_to_update["full_name"] = payload.full_name
        if payload.email is not None:
            fields_to_update["email"] = payload.email
        if payload.id_role is not None:
            fields_to_update["id_role"] = payload.id_role
        if payload.password is not None:
            fields_to_update["password"] = bcrypt.hashpw(payload.password.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')

        if not fields_to_update:
            # Just return current user fields (excluding password)
            return {
                "id": current["id"],
                "id_plant": current["id_plant"],
                "full_name": current["full_name"],
                "email": current["email"],
                "created_at": current["created_at"],
                "id_role": current["id_role"]
            }

        set_clause = ", ".join(f"{k} = %s" for k in fields_to_update.keys())
        params = list(fields_to_update.values()) + [id]

        updated_user = query_db(
            f"UPDATE users SET {set_clause} WHERE id = %s RETURNING id, id_plant, full_name, email, created_at, id_role",
            params,
            fetch_one=True
        )
        return updated_user
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al actualizar usuario", "detalle": str(error)}
        )

@router.delete("/delete/users/{id}", dependencies=[Depends(verify_token)])
def delete_user(id: int):
    try:
        user = query_db(
            "DELETE FROM users WHERE id = %s RETURNING id, id_plant, full_name, email",
            [id],
            fetch_one=True
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Usuario no encontrado"}
            )
        return {
            "mensaje": "Usuario eliminado definitivamente",
            "usuario": user
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al eliminar usuario", "detalle": str(error)}
        )
