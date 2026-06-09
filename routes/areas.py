from fastapi import APIRouter, Depends, HTTPException, status
from config.db import query_db
from middlewares.auth import verify_token
from models.schemas import AreaRequest

router = APIRouter()

@router.post("/areas", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_area(payload: AreaRequest):
    try:
        nueva_area = query_db(
            "INSERT INTO area (name) VALUES (%s) RETURNING *",
            [payload.area],
            fetch_one=True
        )
        return {
            "mensaje": "Área creada correctamente",
            "area": nueva_area
        }
    except Exception as error:
        err_msg = str(error)
        if "duplicate key" in err_msg or "23505" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "El área ya existe"}
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al crear área", "detalle": err_msg}
        )

@router.get("/get/areas")
def get_areas():
    try:
        areas = query_db("SELECT * FROM area", fetch_all=True)
        return areas
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al obtener áreas", "detalle": str(error)}
        )

@router.get("/areas/{id}", dependencies=[Depends(verify_token)])
def get_area_by_id(id: int):
    try:
        area = query_db("SELECT * FROM area WHERE id = %s", [id], fetch_one=True)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Área no encontrada"}
            )
        return area
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al obtener área", "detalle": str(error)}
        )

@router.put("/put/areas/{id}", dependencies=[Depends(verify_token)])
def update_area(id: int, payload: AreaRequest):
    try:
        area_actualizada = query_db(
            "UPDATE area SET name = %s WHERE id = %s RETURNING *",
            [payload.area, id],
            fetch_one=True
        )
        if not area_actualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Área no encontrada"}
            )
        return {
            "mensaje": "Área actualizada correctamente",
            "area": area_actualizada
        }
    except HTTPException:
        raise
    except Exception as error:
        err_msg = str(error)
        if "duplicate key" in err_msg or "23505" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "El área ya existe"}
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al actualizar área", "detalle": err_msg}
        )

@router.delete("/delete/areas/{id}", dependencies=[Depends(verify_token)])
def delete_area(id: int):
    try:
        area = query_db("DELETE FROM area WHERE id = %s RETURNING *", [id], fetch_one=True)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Área no encontrada"}
            )
        return {
            "mensaje": "Área eliminada definitivamente",
            "area": area
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al eliminar área", "detalle": str(error)}
        )
