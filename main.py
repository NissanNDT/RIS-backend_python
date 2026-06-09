from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import all routers
from routes import (
    auth, users, areas, plants, roles, sub_areas, sv_by_area,
    audits, findings, incidents, incident_formats, incident_images,
    factor_trees, intervening_factors, hazard_backgrounds,
    countermeasure_plans, control_hierarchies, verification_methods,
    analysis_participants, cost_centers, excel
)

app = FastAPI(title="RIS Python Backend", version="1.0.0")

# CORS Configuration matching Express app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handler to bypass default detail wrapping
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

# Mount Routers under the /api prefix
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(areas.router, prefix="/api", tags=["Areas"])
app.include_router(plants.router, prefix="/api", tags=["Plants"])
app.include_router(roles.router, prefix="/api", tags=["Roles"])
app.include_router(sub_areas.router, prefix="/api", tags=["Sub Areas"])
app.include_router(sv_by_area.router, prefix="/api", tags=["Supervisor by Area"])
app.include_router(audits.router, prefix="/api", tags=["Audits"])
app.include_router(findings.router, prefix="/api", tags=["Findings"])
app.include_router(incidents.router, prefix="/api", tags=["Incidents"])
app.include_router(incident_formats.router, prefix="/api", tags=["Incident Formats"])
app.include_router(incident_images.router, prefix="/api", tags=["Incident Images"])
app.include_router(factor_trees.router, prefix="/api", tags=["Factor Trees"])
app.include_router(intervening_factors.router, prefix="/api", tags=["Intervening Factors"])
app.include_router(hazard_backgrounds.router, prefix="/api", tags=["Hazard Backgrounds"])
app.include_router(countermeasure_plans.router, prefix="/api", tags=["Countermeasure Plans"])
app.include_router(control_hierarchies.router, prefix="/api", tags=["Control Hierarchies"])
app.include_router(verification_methods.router, prefix="/api", tags=["Verification Methods"])
app.include_router(analysis_participants.router, prefix="/api", tags=["Analysis Participants"])
app.include_router(cost_centers.router, prefix="/api", tags=["Cost Centers"])
app.include_router(excel.router, prefix="/api", tags=["Excel"])

# Base Home Endpoint matching Express '/' route
@app.get("/")
@app.head("/")
def home():
    return PlainTextResponse("API funcionando ")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
