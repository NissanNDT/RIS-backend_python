from fastapi import APIRouter, Depends, HTTPException, status
from config.db import query_db
from middlewares.auth import verify_token
from models.schemas import CostCenterCreate, CostCenterUpdate

router = APIRouter()

@router.get("/get/cost-center", dependencies=[Depends(verify_token)])
def get_cost_centers():
    cost_centers = query_db("SELECT * FROM cost_center ORDER BY id DESC", fetch_all=True)
    return cost_centers

@router.get("/cost-center/{id}", dependencies=[Depends(verify_token)])
def get_cost_center_by_id(id: int):
    cost_center = query_db("SELECT * FROM cost_center WHERE id = %s", [id], fetch_one=True)
    if not cost_center:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost center no encontrado")
    return cost_center

@router.post("/cost-center", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
def create_cost_center(payload: CostCenterCreate):
    cost_center = query_db(
        "INSERT INTO cost_center (name) VALUES (%s) RETURNING *",
        [payload.name],
        fetch_one=True
    )
    return cost_center

@router.put("/put/cost-center/{id}", dependencies=[Depends(verify_token)])
def update_cost_center(id: int, payload: CostCenterUpdate):
    current = query_db("SELECT * FROM cost_center WHERE id = %s", [id], fetch_one=True)
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost center no encontrado")
        
    name = payload.name if payload.name is not None else current["name"]
    
    updated = query_db(
        "UPDATE cost_center SET name = %s WHERE id = %s RETURNING *",
        [name, id],
        fetch_one=True
    )
    return updated

@router.delete("/delete/cost-center/{id}", dependencies=[Depends(verify_token)])
def delete_cost_center(id: int):
    deleted = query_db("DELETE FROM cost_center WHERE id = %s RETURNING *", [id], fetch_one=True)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost center no encontrado")
    return {"message": "Cost center eliminado correctamente"}
