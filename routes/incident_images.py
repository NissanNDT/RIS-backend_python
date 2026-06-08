from fastapi import APIRouter, Depends, HTTPException, status
from config.db import db_pool
from middlewares.auth import verify_token
from models.schemas import IncidentImageCreate

router = APIRouter()

@router.post("/incident-images", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_incident_image(payload: IncidentImageCreate):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO incident_images (id_incident_format, incident_image_path) VALUES (%s, %s) RETURNING *",
                [payload.id_incident_format, payload.incident_image_path]
            )
            return cur.fetchone()

@router.get("/incident-images/incident-format/{id_incident_format}", dependencies=[Depends(verify_token)])
def get_images_by_incident_format(id_incident_format: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM incident_images WHERE id_incident_format = %s ORDER BY id ASC",
                [id_incident_format]
            )
            return cur.fetchall()

@router.delete("/delete/incident-images/{id}", dependencies=[Depends(verify_token)])
def delete_incident_image(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM incident_images WHERE id = %s RETURNING *", [id])
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail="Imagen de incidente no encontrada")
            return {"message": "Imagen de incidente eliminada", "data": deleted}
