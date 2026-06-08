from fastapi import APIRouter, Depends, HTTPException, status
from config.db import query_db
from middlewares.auth import verify_token
from models.schemas import SubAreaCreate, SubAreaUpdate

router = APIRouter()

@router.get("/get/sub-areas", dependencies=[Depends(verify_token)])
def get_sub_areas():
    sub_areas = query_db("SELECT * FROM sub_area ORDER BY id DESC", fetch_all=True)
    return sub_areas

@router.get("/sub-areas/{id}", dependencies=[Depends(verify_token)])
def get_sub_area_by_id(id: int):
    sub_area = query_db("SELECT * FROM sub_area WHERE id = %s", [id], fetch_one=True)
    return sub_area

@router.post("/sub-areas", dependencies=[Depends(verify_token)])
def create_sub_area(payload: SubAreaCreate):
    sub_area = query_db(
        "INSERT INTO sub_area (id_area, name) VALUES (%s, %s) RETURNING *",
        [payload.id_area, payload.name],
        fetch_one=True
    )
    return sub_area

@router.put("/put/sub-areas/{id}", dependencies=[Depends(verify_token)])
def update_sub_area(id: int, payload: SubAreaUpdate):
    current = query_db("SELECT * FROM sub_area WHERE id = %s", [id], fetch_one=True)
    if not current:
        raise HTTPException(status_code=404, detail="Sub area no encontrada")
    
    id_area = payload.id_area if payload.id_area is not None else current["id_area"]
    name = payload.name if payload.name is not None else current["name"]
    
    updated = query_db(
        "UPDATE sub_area SET id_area = %s, name = %s WHERE id = %s RETURNING *",
        [id_area, name, id],
        fetch_one=True
    )
    return updated

@router.delete("/delete/sub-areas/{id}", dependencies=[Depends(verify_token)])
def delete_sub_area(id: int):
    query_db("DELETE FROM sub_area WHERE id = %s", [id])
    return {"message": "Sub_area eliminada"}
