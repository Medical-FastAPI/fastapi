from fastapi import FastAPI
from app.database import Database
from app.routes import patient

app = FastAPI(title="FHIR Server")

@app.on_event("startup")
async def startup():
    await Database.connect_db()
    await Database.create_indexes()

@app.on_event("shutdown")
async def shutdown():
    await Database.close_db()

app.include_router(patient.router, prefix="/fhir", tags=["FHIR"]) 