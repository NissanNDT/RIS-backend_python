from fastapi import APIRouter, Depends, HTTPException, status
from config.db import db_pool
from middlewares.auth import verify_token

router = APIRouter()

@router.get("/get/countermeasure-plan", dependencies=[Depends(verify_token)])
def get_countermeasure_plans():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM countermeasure_plan ORDER BY id DESC")
            return cur.fetchall()

@router.get("/countermeasure-plan/{id}", dependencies=[Depends(verify_token)])
def get_countermeasure_plan_by_id(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM countermeasure_plan WHERE id = %s", [id])
            res = cur.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Countermeasure plan no encontrado")
            return res

@router.get("/countermeasure-plan/incident-format/{id_incident_format}", dependencies=[Depends(verify_token)])
def get_countermeasure_plan_by_incident_format(id_incident_format: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM countermeasure_plan WHERE id_incident_format = %s", [id_incident_format])
            return cur.fetchall()

@router.post("/countermeasure-plan", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_countermeasure_plan(payload: dict):
    fields = [
        "id_incident_format", "id_control_hierarchy", "id_verification_method",
        "what", "why", "how", "where_place", "when_date", "who", "ok", "ng", "comment"
    ]
    values = [payload.get(field) for field in fields]
    placeholders = ", ".join(["%s"] * len(fields))
    columns = ", ".join(fields)
    
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO countermeasure_plan ({columns}) VALUES ({placeholders}) RETURNING *",
                values
            )
            return cur.fetchone()

@router.put("/put/countermeasure-plan/{id}", dependencies=[Depends(verify_token)])
def update_countermeasure_plan(id: int, payload: dict):
    with db_pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM countermeasure_plan WHERE id = %s", [id])
                current = cur.fetchone()
                if not current:
                    raise HTTPException(status_code=404, detail="Countermeasure plan no encontrado")
                    
                id_incident_format = payload.get("id_incident_format", current["id_incident_format"])
                id_control_hierarchy = payload.get("id_control_hierarchy", current["id_control_hierarchy"])
                id_verification_method = payload.get("id_verification_method", current["id_verification_method"])
                what = payload.get("what", current["what"])
                why = payload.get("why", current["why"])
                how = payload.get("how", current["how"])
                where_place = payload.get("where_place", current["where_place"])
                when_date = payload.get("when_date", current["when_date"])
                who = payload.get("who", current["who"])
                ok = payload.get("ok", current["ok"])
                ng = payload.get("ng", current["ng"])
                comment = payload.get("comment", current["comment"])
                
                cur.execute(
                    """UPDATE countermeasure_plan SET
                        id_incident_format = %s, id_control_hierarchy = %s, id_verification_method = %s,
                        what = %s, why = %s, how = %s, where_place = %s, when_date = %s, who = %s,
                        ok = %s, ng = %s, comment = %s
                       WHERE id = %s RETURNING *""",
                    [
                        id_incident_format, id_control_hierarchy, id_verification_method,
                        what, why, how, where_place, when_date, who, ok, ng, comment, id
                    ]
                )
                return cur.fetchone()

@router.delete("/delete/countermeasure-plan/{id}", dependencies=[Depends(verify_token)])
def delete_countermeasure_plan(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM countermeasure_plan WHERE id = %s RETURNING *", [id])
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail="Countermeasure plan no encontrado")
            return {"message": "Countermeasure plan eliminado"}
