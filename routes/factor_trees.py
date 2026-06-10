from fastapi import APIRouter, Depends, HTTPException, status
from config.db import db_pool
from middlewares.auth import verify_token
from models.schemas import FactorTreeCreate, FactorTreeUpdate

router = APIRouter()

@router.get("/get/factor-tree", dependencies=[Depends(verify_token)])
def get_factor_trees():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM factor_tree ORDER BY id DESC")
            return cur.fetchall()

@router.get("/factor-tree/{id}", dependencies=[Depends(verify_token)])
def get_factor_tree_by_id(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM factor_tree WHERE id = %s", [id])
            res = cur.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Factor tree no encontrado")
            return res

@router.get("/factor-tree/incident-format/{id_incident_format}", dependencies=[Depends(verify_token)])
def get_factor_tree_by_incident_format(id_incident_format: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM factor_tree WHERE id_incident_format = %s", [id_incident_format])
            return cur.fetchall()

@router.post("/factor-tree", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_factor_tree(payload: FactorTreeCreate):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO factor_tree (id_incident_format, "4m", actual, factor, control_point, standard, met_standard, met_safety, comments)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                [payload.id_incident_format, payload.m4, payload.actual, payload.factor, payload.control_point, payload.standard, payload.met_standard, payload.met_safety, payload.comments]
            )
            return cur.fetchone()

@router.put("/put/factor-tree/{id}", dependencies=[Depends(verify_token)])
def update_factor_tree(id: int, payload: FactorTreeUpdate):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM factor_tree WHERE id = %s", [id])
            current = cur.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="Factor tree no encontrado")
                
            m4 = payload.m4 if payload.m4 is not None else current["4m"]
            actual = payload.actual if payload.actual is not None else current["actual"]
            factor = payload.factor if payload.factor is not None else current["factor"]
            control_point = payload.control_point if payload.control_point is not None else current["control_point"]
            standard = payload.standard if payload.standard is not None else current["standard"]
            met_standard = payload.met_standard if payload.met_standard is not None else current["met_standard"]
            met_safety = payload.met_safety if payload.met_safety is not None else current["met_safety"]
            comments = payload.comments if payload.comments is not None else current["comments"]
            
            cur.execute(
                """UPDATE factor_tree SET "4m" = %s, actual = %s, factor = %s, control_point = %s, standard = %s, met_standard = %s, met_safety = %s, comments = %s
                   WHERE id = %s RETURNING *""",
                [m4, actual, factor, control_point, standard, met_standard, met_safety, comments, id]
            )
            return cur.fetchone()

@router.delete("/delete/factor-tree/{id}", dependencies=[Depends(verify_token)])
def delete_factor_tree(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM factor_tree WHERE id = %s RETURNING *", [id])
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail="Factor tree no encontrado")
            return {"message": "Factor tree eliminado"}
