from fastapi import APIRouter, HTTPException, Response, status
from typing import Optional
from app.database import Database
from app.models.patient import PatientCreate
from fhir.resources.patient import Patient as FHIRPatient
from datetime import datetime
import traceback

router = APIRouter()

@router.get("/Patient/{patient_id}")
async def get_patient(patient_id: str):
    """Read a specific Patient resource"""
    db = Database.get_db()
    
    patient = await db.patients.find_one({"id": patient_id})
    if patient:
        return patient
    raise HTTPException(status_code=404, detail="Patient not found")

@router.get("/Patient")
async def search_patients(
    name: Optional[str] = None,
    gender: Optional[str] = None,
    birthdate: Optional[str] = None,
    _count: Optional[int] = 10,
    _offset: Optional[int] = 0
):
    """Search for Patient resources"""
    db = Database.get_db()
    
    # Build search query
    query = {}
    if name:
        query["name.family"] = {"$regex": name, "$options": "i"}
    if gender:
        query["gender"] = gender
    if birthdate:
        query["birthDate"] = birthdate

    # Execute search
    patients = []
    cursor = db.patients.find(query).skip(_offset).limit(_count)
    async for patient in cursor:
        patients.append(patient)
    
    total = await db.patients.count_documents(query)
    
    # Return FHIR Bundle
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": total,
        "entry": [{"resource": p} for p in patients]
    }

@router.post("/Patient", status_code=status.HTTP_201_CREATED)
async def create_patient(patient: PatientCreate):
    """Create a new Patient resource"""
    try:
        db = Database.get_db()
        
        # Convert patient to dict
        patient_dict = patient.dict(exclude_none=True)
        
        # Add an ID if not present
        if not patient_dict.get('id'):
            from uuid import uuid4
            patient_dict['id'] = str(uuid4())
        
        # Add metadata with proper ISO format
        patient_dict['meta'] = {
            "versionId": "1",
            "lastUpdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
        
        # Save to database
        result = await db.patients.insert_one(patient_dict)
        
        if result.inserted_id:
            created_patient = await db.patients.find_one({"_id": result.inserted_id})
            if created_patient:
                # Remove MongoDB's _id field from response
                created_patient.pop('_id', None)
                return created_patient
                
        raise HTTPException(status_code=400, detail="Failed to create patient")
    
    except Exception as e:
        print(f"Error creating patient: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.put("/Patient/{patient_id}")
async def update_patient(patient_id: str, patient: PatientCreate):
    """Update an existing Patient resource"""
    db = Database.get_db()
    
    # Check if patient exists
    existing_patient = await db.patients.find_one({"id": patient_id})
    if not existing_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Convert to FHIR resource
    fhir_patient = patient.to_fhir()
    
    # Update metadata
    current_version = int(existing_patient.get("meta", {}).get("versionId", "0"))
    fhir_patient.meta = {
        "versionId": str(current_version + 1),
        "lastUpdated": datetime.utcnow().isoformat()
    }
    
    # Update in database
    result = await db.patients.replace_one(
        {"id": patient_id},
        fhir_patient.dict()
    )
    
    if result.modified_count:
        return await db.patients.find_one({"id": patient_id})
    raise HTTPException(status_code=400, detail="Failed to update patient")

@router.patch("/Patient/{patient_id}")
async def patch_patient(patient_id: str, updates: dict):
    """Partially update a Patient resource"""
    db = Database.get_db()
    
    # Check if patient exists
    existing_patient = await db.patients.find_one({"id": patient_id})
    if not existing_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Update metadata
    current_version = int(existing_patient.get("meta", {}).get("versionId", "0"))
    updates["meta"] = {
        "versionId": str(current_version + 1),
        "lastUpdated": datetime.utcnow().isoformat()
    }
    
    # Update in database
    result = await db.patients.update_one(
        {"id": patient_id},
        {"$set": updates}
    )
    
    if result.modified_count:
        return await db.patients.find_one({"id": patient_id})
    raise HTTPException(status_code=400, detail="Failed to update patient")

@router.delete("/Patient/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete a Patient resource"""
    db = Database.get_db()
    
    # Check if patient exists
    existing_patient = await db.patients.find_one({"id": patient_id})
    if not existing_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Delete from database
    result = await db.patients.delete_one({"id": patient_id})
    
    if result.deleted_count:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=400, detail="Failed to delete patient") 