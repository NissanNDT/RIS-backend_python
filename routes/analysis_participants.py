from fastapi import APIRouter, Depends, HTTPException, status
from config.db import db_pool
from middlewares.auth import verify_token

router = APIRouter()

@router.get("/get/analysis-participant", dependencies=[Depends(verify_token)])
def get_all_analysis_participants():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM analysis_participant ORDER BY id DESC")
            return cur.fetchall()

@router.get("/analysis-participant/{id}", dependencies=[Depends(verify_token)])
def get_analysis_participant_by_id(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM analysis_participant WHERE id = %s", [id])
            res = cur.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Participante de análisis no encontrado")
            return res

@router.get("/analysis-participant/incident-format/{id_incident_format}", dependencies=[Depends(verify_token)])
def get_analysis_participants_by_incident_format(id_incident_format: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM analysis_participant WHERE id_incident_format = %s", [id_incident_format])
            return cur.fetchall()

@router.post("/analysis-participant", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_analysis_participant(payload: dict):
    id_incident_format = payload.get("id_incident_format")
    department = payload.get("department")
    name = payload.get("name")
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO analysis_participant (id_incident_format, department, name) VALUES (%s, %s, %s) RETURNING *",
                [id_incident_format, department, name]
            )
            return cur.fetchone()

@router.put("/put/analysis-participant/{id}", dependencies=[Depends(verify_token)])
def update_analysis_participant(id: int, payload: dict):
    department = payload.get("department")
    name = payload.get("name")
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM analysis_participant WHERE id = %s", [id])
            current = cur.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="Participante de análisis no encontrado")
            dept_val = department if department is not None else current["department"]
            name_val = name if name is not None else current["name"]
            cur.execute(
                "UPDATE analysis_participant SET department = %s, name = %s WHERE id = %s RETURNING *",
                [dept_val, name_val, id]
            )
            return cur.fetchone()

@router.delete("/delete/analysis-participant/{id}", dependencies=[Depends(verify_token)])
def delete_analysis_participant(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM analysis_participant WHERE id = %s RETURNING *", [id])
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail="Participante de análisis no encontrado")
            return {"message": "Participante de análisis eliminado"}
