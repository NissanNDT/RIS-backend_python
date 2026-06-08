from fastapi import APIRouter, Depends, HTTPException, status
from config.db import db_pool
from middlewares.auth import verify_token

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_incident_format(payload: dict):
    # Retrieve payload fields dynamically
    fields = [
        "id_incident", "employee_name", "employee_age", "employee_position",
        "employee_payroll_number", "employee_distribution", "employee_seniority",
        "employee_seniority_in_position", "accident_shift", "employee_type",
        "sv_seniority", "sv_seniority_in_position", "number_of_staff_under_sv",
        "attending_doctor", "recovery_forecast"
    ]
    
    values = [payload.get(field) for field in fields]
    
    placeholders = ", ".join(["%s"] * len(fields))
    columns = ", ".join(fields)
    
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO incident_format ({columns}) VALUES ({placeholders}) RETURNING *",
                values
            )
            return cur.fetchone()

@router.get("/{id_incident}", dependencies=[Depends(verify_token)])
def get_incident_format_by_incident(id_incident: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM incident_format WHERE id_incident = %s", [id_incident])
            fmt = cur.fetchone()
            if not fmt:
                raise HTTPException(status_code=404, detail="Incident format not found")
            
            # Fetch associated images
            cur.execute("SELECT * FROM incident_images WHERE id_incident_format = %s ORDER BY id ASC", [fmt["id"]])
            fmt["images"] = cur.fetchall()
            return fmt

@router.put("/put/{id_incident}", dependencies=[Depends(verify_token)])
def update_incident_format(id_incident: int, payload: dict):
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")
        
    set_clause = ", ".join(f"{k} = %s" for k in payload.keys())
    values = list(payload.values()) + [id_incident]
    
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE incident_format SET {set_clause} WHERE id_incident = %s RETURNING *",
                values
            )
            updated = cur.fetchone()
            if not updated:
                raise HTTPException(status_code=404, detail="Incident format not found")
            return updated

@router.delete("/delete/{id_incident}", dependencies=[Depends(verify_token)])
def delete_incident_format(id_incident: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM incident_format WHERE id_incident = %s RETURNING *", [id_incident])
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail="Incident format not found")
            return {"message": "Incident format deleted successfully"}
