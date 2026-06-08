from fastapi import APIRouter, Depends, HTTPException, status
from config.db import query_db
from middlewares.auth import verify_token
from models.schemas import PlantRequest

router = APIRouter()

@router.post("/plants", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_plant(payload: PlantRequest):
    try:
        nueva_planta = query_db(
            "INSERT INTO plant (name) VALUES (%s) RETURNING *",
            [payload.name],
            fetch_one=True
        )
        return {
            "mensaje": "Planta creada correctamente",
            "plant": nueva_planta
        }
    except Exception as error:
        err_msg = str(error)
        if "duplicate key" in err_msg or "23505" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "La planta ya existe"}
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al crear planta", "detalle": err_msg}
        )

@router.get("/get/plants")
def get_plants():
    try:
        plants = query_db("SELECT * FROM plant", fetch_all=True)
        return plants
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al obtener plantas", "detalle": str(error)}
        )

@router.get("/plants/{id}", dependencies=[Depends(verify_token)])
def get_plant_by_id(id: int):
    try:
        plant = query_db("SELECT * FROM plant WHERE id = %s", [id], fetch_one=True)
        if not plant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Planta no encontrada"}
            )
        return plant
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al obtener planta", "detalle": str(error)}
        )

@router.put("/put/plants/{id}", dependencies=[Depends(verify_token)])
def update_plant(id: int, payload: PlantRequest):
    try:
        planta_actualizada = query_db(
            "UPDATE plant SET name = %s WHERE id = %s RETURNING *",
            [payload.name, id],
            fetch_one=True
        )
        if not planta_actualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Planta no encontrada"}
            )
        return {
            "mensaje": "Planta actualizada correctamente",
            "plant": planta_actualizada
        }
    except HTTPException:
        raise
    except Exception as error:
        err_msg = str(error)
        if "duplicate key" in err_msg or "23505" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "La planta ya existe"}
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al actualizar planta", "detalle": err_msg}
        )

@router.delete("/delete/plants/{id}", dependencies=[Depends(verify_token)])
def delete_plant(id: int):
    try:
        plant = query_db("DELETE FROM plant WHERE id = %s RETURNING *", [id], fetch_one=True)
        if not plant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Planta no encontrada"}
            )
        return {
            "mensaje": "Planta eliminada definitivamente",
            "plant": plant
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Error al eliminar planta", "detalle": str(error)}
        )
