from fastapi import APIRouter, Depends, HTTPException, status
from config.db import db_pool
from middlewares.auth import verify_token
from models.schemas import InterveningFactorCreate, InterveningFactorUpdate

router = APIRouter()

@router.get("/get/intervening-factors", dependencies=[Depends(verify_token)])
def get_intervening_factors():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM intervening_factors ORDER BY id DESC")
            return cur.fetchall()

@router.get("/intervening-factors/{id}", dependencies=[Depends(verify_token)])
def get_intervening_factor_by_id(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM intervening_factors WHERE id = %s", [id])
            res = cur.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Factor interviniente no encontrado")
            return res

@router.get("/intervening-factors/incident-format/{id_incident_format}", dependencies=[Depends(verify_token)])
def get_intervening_factors_by_incident_format(id_incident_format: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM intervening_factors WHERE id_incident_format = %s", [id_incident_format])
            return cur.fetchall()

@router.post("/intervening-factors", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_intervening_factor(payload: InterveningFactorCreate):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO intervening_factors (id_incident_format, name) VALUES (%s, %s) RETURNING *",
                [payload.id_incident_format, payload.name]
            )
            return cur.fetchone()

@router.put("/put/intervening-factors/{id}", dependencies=[Depends(verify_token)])
def update_intervening_factor(id: int, payload: InterveningFactorUpdate):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM intervening_factors WHERE id = %s", [id])
            current = cur.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="Factor interviniente no encontrado")
                
            name = payload.name if payload.name is not None else current["name"]
            
            cur.execute(
                "UPDATE intervening_factors SET name = %s WHERE id = %s RETURNING *",
                [name, id]
            )
            return cur.fetchone()

@router.delete("/delete/intervening-factors/{id}", dependencies=[Depends(verify_token)])
def delete_intervening_factor(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM intervening_factors WHERE id = %s RETURNING *", [id])
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail="Factor interviniente no encontrado")
            return {"message": "Factor interviniente eliminado"}
