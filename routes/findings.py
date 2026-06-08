import re
import unicodedata
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from config.db import db_pool
from middlewares.auth import verify_token
from models.schemas import FindingCreate, FindingUpdate

router = APIRouter()

ALLOWED_LEVELS = ['A', 'B', 'C', 'Otros']
ALLOWED_STATUS = ['Abierto', 'En revisión', 'Cerrado', 'Rechazado']
ALLOWED_FINDING_CATEGORY = ['Acto Inseguro', 'Condición Insegura', 'Condición NG']

def clean_for_folio(s: str) -> str:
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = "".join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.upper()
    s = re.sub(r'[^A-Z0-9\s-]', '', s)
    s = s.strip()
    s = re.sub(r'\s+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s

@router.get("/get/findings")
def get_findings():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM finding ORDER BY id DESC")
            return cur.fetchall()

@router.get("/findings/{id}")
def get_finding_by_id(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM finding WHERE id = %s", [id])
            finding = cur.fetchone()
            if not finding:
                raise HTTPException(status_code=404, detail="Finding no encontrado")
            return finding

@router.get("/findings/audit/{id}")
def get_findings_by_audit_id(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM finding WHERE id_audit = %s ORDER BY id DESC", [id])
            return cur.fetchall()

@router.post("/findings")
def create_finding(payload: FindingCreate, request: Request, user: dict = Depends(verify_token)):
    created_by = user.get("name")
    
    if payload.finding_category not in ALLOWED_FINDING_CATEGORY:
        raise HTTPException(
            status_code=400,
            detail=f"finding_category inválido. Valores permitidos: {', '.join(ALLOWED_FINDING_CATEGORY)}"
        )
        
    with db_pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                # Find supervisor
                cur.execute(
                    "SELECT id_user FROM sv_by_area WHERE id_area = %s AND id_plant = %s LIMIT 1",
                    [payload.id_area, payload.id_plant]
                )
                sv = cur.fetchone()
                if not sv:
                    raise HTTPException(
                        status_code=400,
                        detail="No hay responsable asignado para esta área y planta"
                    )
                id_responsible_user = sv["id_user"]
                status_val = "Abierto"
                finding_folio = None

                # Rule 1: Audit finding
                if payload.id_audit is not None:
                    cur.execute("SELECT name FROM audit WHERE id = %s", [payload.id_audit])
                    audit = cur.fetchone()
                    if not audit:
                        raise HTTPException(status_code=400, detail="La auditoría especificada no existe")
                    audit_name = audit["name"] or f"AUDIT-{payload.id_audit}"
                    clean_audit_name = clean_for_folio(audit_name)

                    cur.execute("SELECT COUNT(*) FROM finding WHERE id_audit = %s", [payload.id_audit])
                    count = cur.fetchone()["count"]
                    is_unique = False
                    while not is_unique:
                        consecutive = str(count + 1).zfill(3)
                        finding_folio = f"{clean_audit_name}-{consecutive}"
                        cur.execute("SELECT id FROM finding WHERE finding_folio = %s", [finding_folio])
                        if not cur.fetchone():
                            is_unique = True
                        else:
                            count += 1

                # Empty strings to None
                f_img = None if payload.finding_image_path == "" else payload.finding_image_path
                c_img = None if payload.countermeasure_image_path == "" else payload.countermeasure_image_path

                # Insert finding
                cur.execute(
                    """INSERT INTO finding (
                        description, location, status, id_area, id_plant, id_responsible_user,
                        finding_category, level, reference_to_the_standard, verification_date,
                        corrective_action, id_audit, conclusion_date, created_by, finding_type,
                        finding_image_path, countermeasure_image_path, finding_folio
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                    [
                        payload.description, payload.location, status_val, payload.id_area, payload.id_plant,
                        id_responsible_user, payload.finding_category, payload.level, payload.reference_to_the_standard,
                        payload.verification_date, payload.corrective_action, payload.id_audit, payload.conclusion_date,
                        created_by, payload.finding_type, f_img, c_img, finding_folio
                    ]
                )
                inserted = cur.fetchone()

                # Rule 2: Non-audit finding
                if finding_folio is None:
                    cur.execute("SELECT name FROM area WHERE id = %s", [payload.id_area])
                    area = cur.fetchone()
                    area_name = area["name"] if area else f"AREA-{payload.id_area}"
                    clean_area_name = clean_for_folio(area_name)

                    today = datetime.now()
                    date_str = today.strftime("%Y%m%d")
                    finding_folio = f"{clean_area_name}-{date_str}-{inserted['id']}"

                    # Unique check fallback
                    cur.execute("SELECT id FROM finding WHERE finding_folio = %s", [finding_folio])
                    if cur.fetchone():
                        import random
                        finding_folio = f"{clean_area_name}-{date_str}-{inserted['id']}-{random.randint(0, 999)}"

                    cur.execute(
                        "UPDATE finding SET finding_folio = %s WHERE id = %s RETURNING *",
                        [finding_folio, inserted["id"]]
                    )
                    inserted = cur.fetchone()

                return inserted

@router.put("/put/findings/{id}")
def update_finding(id: int, payload: FindingUpdate):
    with db_pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM finding WHERE id = %s", [id])
                finding = cur.fetchone()
                if not finding:
                    raise HTTPException(status_code=404, detail="Finding no encontrado")

                if payload.level is not None and payload.level not in ALLOWED_LEVELS:
                    raise HTTPException(status_code=400, detail=f"Level inválido. Valores permitidos: {', '.join(ALLOWED_LEVELS)}")
                if payload.status is not None and payload.status not in ALLOWED_STATUS:
                    raise HTTPException(status_code=400, detail=f"Estatus inválido. Valores permitidos: {', '.join(ALLOWED_STATUS)}")
                if payload.finding_category is not None and payload.finding_category not in ALLOWED_FINDING_CATEGORY:
                    raise HTTPException(status_code=400, detail=f"finding_category inválido. Valores permitidos: {', '.join(ALLOWED_FINDING_CATEGORY)}")

                updated_plant = payload.id_plant if payload.id_plant is not None else finding["id_plant"]
                updated_area = payload.id_area if payload.id_area is not None else finding["id_area"]
                id_responsible_user = finding["id_responsible_user"]

                if updated_plant != finding["id_plant"] or updated_area != finding["id_area"]:
                    cur.execute(
                        "SELECT id_user FROM sv_by_area WHERE id_area = %s AND id_plant = %s LIMIT 1",
                        [updated_area, updated_plant]
                    )
                    sv = cur.fetchone()
                    if not sv:
                        raise HTTPException(status_code=400, detail="No hay responsable para la nueva área y planta")
                    id_responsible_user = sv["id_user"]

                desc = payload.description if payload.description is not None else finding["description"]
                loc = payload.location if payload.location is not None else finding["location"]
                status_val = payload.status if payload.status is not None else finding["status"]
                cat = payload.finding_category if payload.finding_category is not None else finding["finding_category"]
                level_val = payload.level if payload.level is not None else finding["level"]
                ref = payload.reference_to_the_standard if payload.reference_to_the_standard is not None else finding["reference_to_the_standard"]
                v_date = payload.verification_date if payload.verification_date is not None else finding["verification_date"]
                c_act = payload.corrective_action if payload.corrective_action is not None else finding["corrective_action"]
                audit_id = payload.id_audit if payload.id_audit is not None else finding["id_audit"]
                c_date = payload.conclusion_date if payload.conclusion_date is not None else finding["conclusion_date"]

                f_img = finding["finding_image_path"]
                if payload.finding_image_path is not None:
                    f_img = None if payload.finding_image_path == "" else payload.finding_image_path

                c_img = finding["countermeasure_image_path"]
                if payload.countermeasure_image_path is not None:
                    c_img = None if payload.countermeasure_image_path == "" else payload.countermeasure_image_path

                cur.execute(
                    """UPDATE finding SET
                        description = %s, location = %s, status = %s, id_area = %s, id_plant = %s,
                        id_responsible_user = %s, finding_category = %s, level = %s, reference_to_the_standard = %s,
                        verification_date = %s, corrective_action = %s, id_audit = %s, conclusion_date = %s,
                        finding_image_path = %s, countermeasure_image_path = %s
                       WHERE id = %s RETURNING *""",
                    [
                        desc, loc, status_val, updated_area, updated_plant, id_responsible_user,
                        cat, level_val, ref, v_date, c_act, audit_id, c_date, f_img, c_img, id
                    ]
                )
                return cur.fetchone()

@router.delete("/delete/findings/{id}")
def delete_finding(id: int):
    with db_pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("DELETE FROM finding WHERE id = %s RETURNING *", [id])
                deleted = cur.fetchone()
                if not deleted:
                    raise HTTPException(status_code=404, detail="Finding no encontrado")
                return {"message": "Finding eliminado"}
