from typing import Optional
from pydantic import BaseModel, Field
from fhir.resources.patient import Patient as FHIRPatient

class PatientCreate(BaseModel):
    resourceType: str = "Patient"
    id: Optional[str] = None
    active: bool = True
    name: list = Field(default_factory=list)
    gender: Optional[str] = None
    birthDate: Optional[str] = None

    def to_fhir(self) -> FHIRPatient:
        return FHIRPatient.parse_obj(self.dict(exclude_none=True))