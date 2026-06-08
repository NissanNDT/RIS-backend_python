from fastapi import APIRouter, Depends, HTTPException, status
from config.db import query_db
from middlewares.auth import verify_token
from models.schemas import RoleRequest

router = APIRouter()

@router.post("/roles", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_role(payload: RoleRequest):
    try:
        nuevo_role = query_db(
            "INSERT INTO role (name) VALUES (%s) RETURNING *",
            [payload.name],
            fetch_one=True
        )
        return {
            "mensaje": "Role creado correctamente",
            "role": nuevo_role
        }
    except Exception as error:
        err_msg = str(error)
        if "duplicate key" in err_msg or "23505" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "El role ya existe"}
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al crear role", "detalle": err_msg}
        )

@router.get("/get/roles", dependencies=[Depends(verify_token)])
def get_roles():
    try:
        roles = query_db("SELECT * FROM role", fetch_all=True)
        return roles
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al obtener roles", "detalle": str(error)}
        )

@router.get("/roles/{id}", dependencies=[Depends(verify_token)])
def get_role_by_id(id: int):
    try:
        role = query_db("SELECT * FROM role WHERE id = %s", [id], fetch_one=True)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Role no encontrado"}
            )
        return role
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al obtener role", "detalle": str(error)}
        )

@router.put("/put/roles/{id}", dependencies=[Depends(verify_token)])
def update_role(id: int, payload: RoleRequest):
    try:
        role_actualizado = query_db(
            "UPDATE role SET name = %s WHERE id = %s RETURNING *",
            [payload.name, id],
            fetch_one=True
        )
        if not role_actualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Role no encontrado"}
            )
        return {
            "mensaje": "Role actualizado correctamente",
            "role": role_actualizado
        }
    except HTTPException:
        raise
    except Exception as error:
        err_msg = str(error)
        if "duplicate key" in err_msg or "23505" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "El role ya existe"}
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al actualizar role", "detalle": err_msg}
        )

@router.delete("/delete/roles/{id}", dependencies=[Depends(verify_token)])
def delete_role(id: int):
    try:
        role = query_db("DELETE FROM role WHERE id = %s RETURNING *", [id], fetch_one=True)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Role no encontrado"}
            )
        return {
            "mensaje": "Role eliminado definitivamente",
            "role": role
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al eliminar role", "detalle": str(error)}
        )
