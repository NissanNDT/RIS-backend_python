from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from config.db import db_pool
from middlewares.auth import verify_token
from models.schemas import IncidentCreate, IncidentUpdate

router = APIRouter()

LEVEL_ORDER = ['G', 'U', 'R', 'FR1', 'FR0']

def expand_level(level: str) -> str:
    if level not in LEVEL_ORDER:
        raise HTTPException(status_code=400, detail="Level inválido")
    idx = LEVEL_ORDER.index(level)
    return ",".join(LEVEL_ORDER[idx:])

@router.get("/get/incidents")
def get_incidents():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM incident ORDER BY id DESC")
            return cur.fetchall()

@router.get("/incidents/{id}", dependencies=[Depends(verify_token)])
def get_incident_by_id(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM incident WHERE id = %s", [id])
            incident = cur.fetchone()
            if not incident:
                raise HTTPException(status_code=404, detail="Incidente no encontrado")
            return incident

def to_int_or_none(val):
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

@router.post("/incidents")
def create_incident(payload: dict, request: Request, user: dict = Depends(verify_token)):
    date_val = payload.get("date")
    time_val = payload.get("time")
    level_val = payload.get("level")
    location_val = payload.get("location")
    injury_val = payload.get("injury")
    desc_val = payload.get("description")
    id_area = to_int_or_none(payload.get("id_area"))
    id_plant = to_int_or_none(payload.get("id_plant"))
    mechanism = payload.get("incident_mechanism")
    root_cause = payload.get("root_cause")
    id_cost_center = to_int_or_none(payload.get("id_cost_center"))

    final_level = expand_level(level_val)

    with db_pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                # Find supervisor
                cur.execute(
                    "SELECT id_user FROM sv_by_area WHERE id_area = %s AND id_plant = %s LIMIT 1",
                    [id_area, id_plant]
                )
                sv = cur.fetchone()
                if not sv:
                    raise HTTPException(status_code=400, detail="No hay responsable asignado para esta área y planta")
                id_responsible_user = sv["id_user"]

                # Get junior / sv_general
                cur.execute(
                    "SELECT id_general_sv, id_junior FROM users WHERE id = %s",
                    [id_responsible_user]
                )
                user_info = cur.fetchone()
                id_general_sv = user_info["id_general_sv"] if user_info else None
                id_junior = user_info["id_junior"] if user_info else None

                cur.execute(
                    """INSERT INTO incident (
                        date, time, level, location, injury, description,
                        id_area, id_plant, id_responsible_user, id_general_sv, id_junior,
                        incident_mechanism, root_cause, id_cost_center
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id""",
                    [
                        date_val, time_val, final_level, location_val, injury_val, desc_val,
                        id_area, id_plant, id_responsible_user, id_general_sv, id_junior,
                        mechanism, root_cause, id_cost_center
                    ]
                )
                incident_id = cur.fetchone()["id"]

                # Area name
                cur.execute("SELECT name FROM area WHERE id = %s", [id_area])
                area = cur.fetchone()
                area_name = area["name"] if area else f"AREA-{id_area}"

                clean_date = date_val.replace("-", "")
                folio = f"INC-{area_name}-{clean_date}-{incident_id}"

                cur.execute(
                    "UPDATE incident SET incident_folio = %s WHERE id = %s RETURNING *",
                    [folio, incident_id]
                )
                return cur.fetchone()

@router.put("/put/incidents/{id}", dependencies=[Depends(verify_token)])
def update_incident(id: int, payload: dict):
    with db_pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM incident WHERE id = %s", [id])
                incident = cur.fetchone()
                if not incident:
                    raise HTTPException(status_code=404, detail="Incidente no encontrado")

                level_val = payload.get("level")
                final_level = expand_level(level_val) if level_val else incident["level"]

                id_plant_val = payload.get("id_plant")
                id_plant = to_int_or_none(id_plant_val) if id_plant_val is not None else incident["id_plant"]
                id_area_val = payload.get("id_area")
                id_area = to_int_or_none(id_area_val) if id_area_val is not None else incident["id_area"]
                
                date_val = payload.get("date")
                if date_val:
                    # Expect YYYY-MM-DD
                    if isinstance(date_val, datetime):
                        updated_date_str = date_val.strftime("%Y-%m-%d")
                    else:
                        updated_date_str = str(date_val).split(" ")[0]
                else:
                    if isinstance(incident["date"], (datetime, datetime.date)):
                        updated_date_str = incident["date"].strftime("%Y-%m-%d")
                    else:
                        updated_date_str = str(incident["date"])

                id_responsible_user = incident["id_responsible_user"]
                id_general_sv = incident["id_general_sv"]
                id_junior = incident["id_junior"]

                if id_plant != incident["id_plant"] or id_area != incident["id_area"]:
                    cur.execute(
                        "SELECT id_user FROM sv_by_area WHERE id_area = %s AND id_plant = %s LIMIT 1",
                        [id_area, id_plant]
                    )
                    sv = cur.fetchone()
                    if not sv:
                        raise HTTPException(status_code=400, detail="No hay responsable asignado para la nueva área y planta")
                    id_responsible_user = sv["id_user"]

                    cur.execute(
                        "SELECT id_general_sv, id_junior FROM users WHERE id = %s",
                        [id_responsible_user]
                    )
                    user_info = cur.fetchone()
                    id_general_sv = user_info["id_general_sv"] if user_info else None
                    id_junior = user_info["id_junior"] if user_info else None

                # Recalculate folio if area or date changes
                if id_area != incident["id_area"] or date_val is not None:
                    cur.execute("SELECT name FROM area WHERE id = %s", [id_area])
                    area = cur.fetchone()
                    area_name = area["name"] if area else f"AREA-{id_area}"
                    clean_date = updated_date_str.replace("-", "")
                    incident_folio = f"INC-{area_name}-{clean_date}-{id}"
                else:
                    incident_folio = incident["incident_folio"]

                time_val = payload.get("time", incident["time"])
                location_val = payload.get("location", incident["location"])
                injury_val = payload.get("injury", incident["injury"])
                desc_val = payload.get("description", incident["description"])
                mechanism = payload.get("incident_mechanism", incident["incident_mechanism"])
                root_cause = payload.get("root_cause", incident["root_cause"])
                id_cost_center_val = payload.get("id_cost_center")
                id_cost_center = to_int_or_none(id_cost_center_val) if id_cost_center_val is not None else incident["id_cost_center"]

                cur.execute(
                    """UPDATE incident SET
                        date = %s, time = %s, level = %s, location = %s, injury = %s, description = %s,
                        id_area = %s, id_plant = %s, id_responsible_user = %s, id_general_sv = %s, id_junior = %s,
                        incident_mechanism = %s, root_cause = %s, id_cost_center = %s, incident_folio = %s
                       WHERE id = %s RETURNING *""",
                    [
                        updated_date_str, time_val, final_level, location_val, injury_val, desc_val,
                        id_area, id_plant, id_responsible_user, id_general_sv, id_junior,
                        mechanism, root_cause, id_cost_center, incident_folio, id
                    ]
                )
                return cur.fetchone()

@router.delete("/delete/incidents/{id}")
def delete_incident(id: int, request: Request, user: dict = Depends(verify_token)):
    role = user.get("role")
    with db_pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                if role == "Admin":
                    # Get associated incident_format id
                    cur.execute("SELECT id FROM incident_format WHERE id_incident = %s", [id])
                    fmt = cur.fetchone()
                    if fmt:
                        fmt_id = fmt["id"]
                        cur.execute("DELETE FROM analysis_participant WHERE id_incident_format = %s", [fmt_id])
                        cur.execute("DELETE FROM countermeasure_plan WHERE id_incident_format = %s", [fmt_id])
                        cur.execute("DELETE FROM factor_tree WHERE id_incident_format = %s", [fmt_id])
                        cur.execute("DELETE FROM hazard_background WHERE id_incident_format = %s", [fmt_id])
                        cur.execute("DELETE FROM intervening_factors WHERE id_incident_format = %s", [fmt_id])
                        cur.execute("DELETE FROM incident_images WHERE id_incident_format = %s", [fmt_id])
                        cur.execute("DELETE FROM incident_format WHERE id = %s", [fmt_id])

                cur.execute("DELETE FROM incident WHERE id = %s RETURNING *", [id])
                deleted = cur.fetchone()
                if not deleted:
                    raise HTTPException(status_code=404, detail="Incidente no encontrado")
                return {"message": "Incidente eliminado"}
