from fastapi import APIRouter, Depends, HTTPException, status
from config.db import db_pool
from middlewares.auth import verify_token
from models.schemas import HazardBackgroundCreate, HazardBackgroundUpdate

router = APIRouter()

@router.get("/get/hazard-background", dependencies=[Depends(verify_token)])
def get_hazard_backgrounds():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM hazard_background ORDER BY id DESC")
            return cur.fetchall()

@router.get("/hazard-background/{id}", dependencies=[Depends(verify_token)])
def get_hazard_background_by_id(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM hazard_background WHERE id = %s", [id])
            res = cur.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Antecedente de peligro no encontrado")
            return res

@router.get("/hazard-background/incident-format/{id_incident_format}", dependencies=[Depends(verify_token)])
def get_hazard_background_by_incident_format(id_incident_format: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM hazard_background WHERE id_incident_format = %s", [id_incident_format])
            return cur.fetchall()

@router.post("/hazard-background", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_hazard_background(payload: HazardBackgroundCreate):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO hazard_background (id_incident_format, description) VALUES (%s, %s) RETURNING *",
                [payload.id_incident_format, payload.description]
            )
            return cur.fetchone()

@router.put("/put/hazard-background/{id}", dependencies=[Depends(verify_token)])
def update_hazard_background(id: int, payload: HazardBackgroundUpdate):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM hazard_background WHERE id = %s", [id])
            current = cur.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="Antecedente de peligro no encontrado")
                
            description = payload.description if payload.description is not None else current["description"]
            
            cur.execute(
                "UPDATE hazard_background SET description = %s WHERE id = %s RETURNING *",
                [description, id]
            )
            return cur.fetchone()

@router.delete("/delete/hazard-background/{id}", dependencies=[Depends(verify_token)])
def delete_hazard_background(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM hazard_background WHERE id = %s RETURNING *", [id])
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail="Antecedente de peligro no encontrado")
            return {"message": "Antecedente de peligro eliminado"}
