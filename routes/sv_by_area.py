from fastapi import APIRouter, Depends, HTTPException, status
from config.db import query_db
from middlewares.auth import verify_token
from models.schemas import SvByAreaCreate, SvByAreaUpdate

router = APIRouter()

@router.get("/get/sv-by-area", dependencies=[Depends(verify_token)])
def get_sv_by_areas():
    sv_by_areas = query_db("SELECT * FROM sv_by_area ORDER BY id DESC", fetch_all=True)
    return sv_by_areas

@router.get("/sv-by-area/{id}", dependencies=[Depends(verify_token)])
def get_sv_by_area_by_id(id: int):
    sv_by_area = query_db("SELECT * FROM sv_by_area WHERE id = %s", [id], fetch_one=True)
    return sv_by_area

@router.post("/sv-by-area", dependencies=[Depends(verify_token)])
def create_sv_by_area(payload: SvByAreaCreate):
    sv_by_area = query_db(
        "INSERT INTO sv_by_area (id_plant, id_area, id_user) VALUES (%s, %s, %s) RETURNING *",
        [payload.id_plant, payload.id_area, payload.id_user],
        fetch_one=True
    )
    return sv_by_area

@router.put("/put/sv-by-area/{id}", dependencies=[Depends(verify_token)])
def update_sv_by_area(id: int, payload: SvByAreaUpdate):
    current = query_db("SELECT * FROM sv_by_area WHERE id = %s", [id], fetch_one=True)
    if not current:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
        
    id_plant = payload.id_plant if payload.id_plant is not None else current["id_plant"]
    id_area = payload.id_area if payload.id_area is not None else current["id_area"]
    id_user = payload.id_user if payload.id_user is not None else current["id_user"]
    
    updated = query_db(
        "UPDATE sv_by_area SET id_plant = %s, id_area = %s, id_user = %s WHERE id = %s RETURNING *",
        [id_plant, id_area, id_user, id],
        fetch_one=True
    )
    return updated

@router.delete("/delete/sv-by-area/{id}", dependencies=[Depends(verify_token)])
def delete_sv_by_area(id: int):
    query_db("DELETE FROM sv_by_area WHERE id = %s", [id])
    return {"message": "Registro eliminado"}
