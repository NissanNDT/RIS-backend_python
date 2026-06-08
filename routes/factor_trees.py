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
                """INSERT INTO factor_tree (id_incident_format, unsafe_act, unsafe_condition, personal_factor, work_factor, root_cause)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING *""",
                [payload.id_incident_format, payload.unsafe_act, payload.unsafe_condition, payload.personal_factor, payload.work_factor, payload.root_cause]
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
                
            unsafe_act = payload.unsafe_act if payload.unsafe_act is not None else current["unsafe_act"]
            unsafe_condition = payload.unsafe_condition if payload.unsafe_condition is not None else current["unsafe_condition"]
            personal_factor = payload.personal_factor if payload.personal_factor is not None else current["personal_factor"]
            work_factor = payload.work_factor if payload.work_factor is not None else current["work_factor"]
            root_cause = payload.root_cause if payload.root_cause is not None else current["root_cause"]
            
            cur.execute(
                """UPDATE factor_tree SET unsafe_act = %s, unsafe_condition = %s, personal_factor = %s, work_factor = %s, root_cause = %s
                   WHERE id = %s RETURNING *""",
                [unsafe_act, unsafe_condition, personal_factor, work_factor, root_cause, id]
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
