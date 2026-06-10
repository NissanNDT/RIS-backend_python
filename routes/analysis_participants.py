from fastapi import APIRouter, Depends, HTTPException, status
from config.db import db_pool
from middlewares.auth import verify_token
from models.schemas import AnalysisParticipantCreate, AnalysisParticipantUpdate

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
def create_analysis_participant(payload: AnalysisParticipantCreate):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO analysis_participant (id_incident_format, participant_type, name, department, id_cost_center) VALUES (%s, %s, %s, %s, %s) RETURNING *",
                [payload.id_incident_format, payload.participant_type, payload.name, payload.department, payload.id_cost_center]
            )
            return cur.fetchone()

@router.put("/put/analysis-participant/{id}", dependencies=[Depends(verify_token)])
def update_analysis_participant(id: int, payload: AnalysisParticipantUpdate):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM analysis_participant WHERE id = %s", [id])
            current = cur.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="Participante de análisis no encontrado")
                
            participant_type = payload.participant_type if payload.participant_type is not None else current["participant_type"]
            name = payload.name if payload.name is not None else current["name"]
            department = payload.department if payload.department is not None else current["department"]
            id_cost_center = payload.id_cost_center if payload.id_cost_center is not None else current["id_cost_center"]
            
            cur.execute(
                "UPDATE analysis_participant SET participant_type = %s, name = %s, department = %s, id_cost_center = %s WHERE id = %s RETURNING *",
                [participant_type, name, department, id_cost_center, id]
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
