from fastapi import APIRouter, Depends, HTTPException, status
from config.db import db_pool
from middlewares.auth import verify_token

router = APIRouter()

@router.get("/get/verification-method", dependencies=[Depends(verify_token)])
def get_verification_methods():
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM verification_method ORDER BY id DESC")
            return cur.fetchall()

@router.get("/verification-method/{id}", dependencies=[Depends(verify_token)])
def get_verification_method_by_id(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM verification_method WHERE id = %s", [id])
            res = cur.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Verification method no encontrado")
            return res

@router.post("/verification-method", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_verification_method(payload: dict):
    name = payload.get("name")
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO verification_method (name) VALUES (%s) RETURNING *",
                [name]
            )
            return cur.fetchone()

@router.put("/put/verification-method/{id}", dependencies=[Depends(verify_token)])
def update_verification_method(id: int, payload: dict):
    name = payload.get("name")
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM verification_method WHERE id = %s", [id])
            current = cur.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="Verification method no encontrado")
            name_val = name if name is not None else current["name"]
            cur.execute(
                "UPDATE verification_method SET name = %s WHERE id = %s RETURNING *",
                [name_val, id]
            )
            return cur.fetchone()

@router.delete("/delete/verification-method/{id}", dependencies=[Depends(verify_token)])
def delete_verification_method(id: int):
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM verification_method WHERE id = %s RETURNING *", [id])
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail="Verification method no encontrado")
            return {"message": "Verification method eliminado"}
