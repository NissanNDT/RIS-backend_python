from fastapi import APIRouter, Depends, HTTPException, status
from config.db import db_pool
from middlewares.auth import verify_token

router = APIRouter()

@router.get("/get/control-hierarchy", dependencies=[Depends(verify_token)])
def get_control_hierarchies():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM control_hierarchy ORDER BY id DESC")
            return cur.fetchall()

@router.get("/control-hierarchy/{id}", dependencies=[Depends(verify_token)])
def get_control_hierarchy_by_id(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM control_hierarchy WHERE id = %s", [id])
            res = cur.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Control hierarchy no encontrado")
            return res

@router.post("/control-hierarchy", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_control_hierarchy(payload: dict):
    name = payload.get("name")
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO control_hierarchy (name) VALUES (%s) RETURNING *",
                [name]
            )
            return cur.fetchone()

@router.put("/put/control-hierarchy/{id}", dependencies=[Depends(verify_token)])
def update_control_hierarchy(id: int, payload: dict):
    name = payload.get("name")
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM control_hierarchy WHERE id = %s", [id])
            current = cur.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="Control hierarchy no encontrado")
            name_val = name if name is not None else current["name"]
            cur.execute(
                "UPDATE control_hierarchy SET name = %s WHERE id = %s RETURNING *",
                [name_val, id]
            )
            return cur.fetchone()

@router.delete("/delete/control-hierarchy/{id}", dependencies=[Depends(verify_token)])
def delete_control_hierarchy(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM control_hierarchy WHERE id = %s RETURNING *", [id])
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail="Control hierarchy no encontrado")
            return {"message": "Control hierarchy eliminado"}
