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
            "SELECT id, id_plant, full_name, email, created_at, id_role, id_general_sv, id_junior FROM users ORDER BY created_at DESC",
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
            "SELECT id, id_plant, full_name, email, created_at, id_role, id_general_sv, id_junior FROM users WHERE id = %s",
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
            """INSERT INTO users (id_plant, full_name, email, password, id_role, id_general_sv, id_junior)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               RETURNING id, id_plant, full_name, email, created_at, id_role, id_general_sv, id_junior""",
            [payload.id_plant, payload.full_name, payload.email, hashed_password, payload.id_role, payload.id_general_sv, payload.id_junior],
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
        updatable_fields = ["id_plant", "full_name", "email", "id_role", "id_general_sv", "id_junior"]
        for field in updatable_fields:
            if field in payload.model_fields_set:
                fields_to_update[field] = getattr(payload, field)
        
        if "password" in payload.model_fields_set and payload.password is not None:
            fields_to_update["password"] = bcrypt.hashpw(payload.password.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')

        if not fields_to_update:
            return {
                "id": current["id"],
                "id_plant": current["id_plant"],
                "full_name": current["full_name"],
                "email": current["email"],
                "created_at": current["created_at"],
                "id_role": current["id_role"],
                "id_general_sv": current["id_general_sv"],
                "id_junior": current["id_junior"]
            }

        set_clause = ", ".join(f"{k} = %s" for k in fields_to_update.keys())
        params = list(fields_to_update.values()) + [id]

        updated_user = query_db(
            f"UPDATE users SET {set_clause} WHERE id = %s RETURNING id, id_plant, full_name, email, created_at, id_role, id_general_sv, id_junior",
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
