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
    fields = [
        "id_incident_format", "previous_fr1_incidents_presented", "existing_processes_or_areas_potential_for_incident",
        "processes_or_areas_potential_for_incident", "risk_assessed_and_identified", "incident_category",
        "horizontal_review", "horizontal_review_comment", "new_risk_assessment_needed",
        "safety_dojo_reception_date", "genba_dojo_reception_date", "negligence_type", "labor_report"
    ]
    values = [getattr(payload, field) for field in fields]
    columns = ", ".join(fields)
    placeholders = ", ".join(["%s"] * len(fields))
    
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO hazard_background ({columns}) VALUES ({placeholders}) RETURNING *",
                values
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
                
            fields = [
                "id_incident_format", "previous_fr1_incidents_presented", "existing_processes_or_areas_potential_for_incident",
                "processes_or_areas_potential_for_incident", "risk_assessed_and_identified", "incident_category",
                "horizontal_review", "horizontal_review_comment", "new_risk_assessment_needed",
                "safety_dojo_reception_date", "genba_dojo_reception_date", "negligence_type", "labor_report"
            ]
            
            updates = []
            values = []
            for field in fields:
                if hasattr(payload, field):
                    val = getattr(payload, field)
                    if val is not None:
                        updates.append(f"{field} = %s")
                        values.append(val)
                        continue
                updates.append(f"{field} = %s")
                values.append(current[field])
            
            values.append(id)
            set_clause = ", ".join(updates)
            
            cur.execute(
                f"UPDATE hazard_background SET {set_clause} WHERE id = %s RETURNING *",
                values
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
