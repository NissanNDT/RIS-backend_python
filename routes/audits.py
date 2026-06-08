from fastapi import APIRouter, Depends, HTTPException, status
from config.db import db_pool
from middlewares.auth import verify_token

router = APIRouter()

@router.get("/get/audits", dependencies=[Depends(verify_token)])
def get_audits():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM audit ORDER BY id DESC")
            return cur.fetchall()

@router.get("/get/public-audits")
def get_public_audits():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM audit ORDER BY id DESC")
            return cur.fetchall()

@router.get("/audits/{id}", dependencies=[Depends(verify_token)])
def get_audit_by_id(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM audit WHERE id = %s", [id])
            audit = cur.fetchone()
            if not audit:
                raise HTTPException(status_code=404, detail="Auditoría no encontrada")
            return audit

@router.get("/audits/user/{id_user}", dependencies=[Depends(verify_token)])
def get_audits_by_user(id_user: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM audit WHERE id_audit_user = %s ORDER BY created_at DESC", [id_user])
            return cur.fetchall()

@router.post("/audits", dependencies=[Depends(verify_token)])
def create_audit(payload: dict):
    # payload has: name, id_plant, id_area, type
    name = payload.get("name")
    id_plant = payload.get("id_plant")
    id_area = payload.get("id_area")
    audit_type = payload.get("type")

    if audit_type not in ["SES", "FPES"]:
        raise HTTPException(status_code=400, detail="Tipo de auditoría inválido")

    with db_pool.connection() as conn:
        # A transaction block
        with conn.transaction():
            with conn.cursor() as cur:
                # Find supervisor
                cur.execute(
                    "SELECT id_user FROM sv_by_area WHERE id_area = %s AND id_plant = %s LIMIT 1",
                    [id_area, id_plant]
                )
                sv = cur.fetchone()
                if not sv:
                    raise HTTPException(
                        status_code=400,
                        detail="No hay usuario responsable asignado para esta área en esta planta"
                    )
                id_audit_user = sv["id_user"]

                # Insert
                cur.execute(
                    "INSERT INTO audit (name, id_plant, id_area, id_audit_user, type) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    [name, id_plant, id_area, id_audit_user, audit_type]
                )
                audit_id = cur.fetchone()["id"]

                # Get area name
                cur.execute("SELECT name FROM area WHERE id = %s", [id_area])
                area = cur.fetchone()
                area_name = area["name"] if area else f"AREA-{id_area}"

                audit_folio = f"{audit_type}-{id_plant}-{area_name}-{audit_id}"

                # Update folio
                cur.execute(
                    "UPDATE audit SET audit_folio = %s WHERE id = %s RETURNING *",
                    [audit_folio, audit_id]
                )
                return cur.fetchone()

@router.put("/put/audits/{id}", dependencies=[Depends(verify_token)])
def update_audit(id: int, payload: dict):
    with db_pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM audit WHERE id = %s", [id])
                audit = cur.fetchone()
                if not audit:
                    raise HTTPException(status_code=404, detail="Auditoría no encontrada")

                name = payload.get("name", audit["name"])
                id_plant = payload.get("id_plant", audit["id_plant"])
                id_area = payload.get("id_area", audit["id_area"])
                audit_type = payload.get("type", audit["type"])

                if audit_type not in ["SES", "FPES"]:
                    raise HTTPException(status_code=400, detail="Tipo de auditoría inválido")

                id_audit_user = audit["id_audit_user"]
                if id_plant != audit["id_plant"] or id_area != audit["id_area"]:
                    cur.execute(
                        "SELECT id_user FROM sv_by_area WHERE id_plant = %s AND id_area = %s LIMIT 1",
                        [id_plant, id_area]
                    )
                    sv = cur.fetchone()
                    if not sv:
                        raise HTTPException(
                            status_code=400,
                            detail="No hay responsable asignado para la nueva área y planta"
                        )
                    id_audit_user = sv["id_user"]

                if audit_type != audit["type"] or id_area != audit["id_area"] or id_plant != audit["id_plant"]:
                    # get area name
                    cur.execute("SELECT name FROM area WHERE id = %s", [id_area])
                    area = cur.fetchone()
                    area_name = area["name"] if area else f"AREA-{id_area}"
                    audit_folio = f"{audit_type}-{id_plant}-{area_name}-{id}"
                else:
                    audit_folio = audit["audit_folio"]

                cur.execute(
                    """UPDATE audit SET name = %s, type = %s, id_plant = %s, id_area = %s, id_audit_user = %s, audit_folio = %s
                       WHERE id = %s RETURNING *""",
                    [name, audit_type, id_plant, id_area, id_audit_user, audit_folio, id]
                )
                return cur.fetchone()

@router.delete("/delete/audits/{id}", dependencies=[Depends(verify_token)])
def delete_audit(id: int):
    with db_pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("DELETE FROM finding WHERE id_audit = %s", [id])
                cur.execute("DELETE FROM audit WHERE id = %s RETURNING *", [id])
                deleted = cur.fetchone()
                if not deleted:
                    raise HTTPException(status_code=404, detail="Auditoría no encontrada")
                return {"message": "Auditoría eliminada"}
