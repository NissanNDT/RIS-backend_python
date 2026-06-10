from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

# Auth
class LoginRequest(BaseModel):
    email: str
    password: str

# Users
class UserCreate(BaseModel):
    id_plant: int
    full_name: str
    email: str
    password: str
    id_role: int
    id_general_sv: Optional[int] = None
    id_junior: Optional[int] = None

class UserUpdate(BaseModel):
    id_plant: Optional[int] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    id_role: Optional[int] = None
    id_general_sv: Optional[int] = None
    id_junior: Optional[int] = None

# Area
class AreaRequest(BaseModel):
    area: str

# Plant
class PlantRequest(BaseModel):
    name: str

# Role
class RoleRequest(BaseModel):
    name: str

# SubArea
class SubAreaCreate(BaseModel):
    id_area: int
    name: str

class SubAreaUpdate(BaseModel):
    id_area: Optional[int] = None
    name: Optional[str] = None

# SvByArea
class SvByAreaCreate(BaseModel):
    id_plant: int
    id_area: int
    id_user: int

class SvByAreaUpdate(BaseModel):
    id_plant: Optional[int] = None
    id_area: Optional[int] = None
    id_user: Optional[int] = None

# CostCenter
class CostCenterCreate(BaseModel):
    name: str

class CostCenterUpdate(BaseModel):
    name: Optional[str] = None

# Audit
class AuditCreate(BaseModel):
    name: str
    id_user: int
    date: date
    auditors: str
    status: str

class AuditUpdate(BaseModel):
    name: Optional[str] = None
    id_user: Optional[int] = None
    date: Optional[date] = None
    auditors: Optional[str] = None
    status: Optional[str] = None

# Finding
class FindingCreate(BaseModel):
    description: str
    location: str
    id_area: int
    id_plant: int
    finding_category: str
    level: Optional[str] = None
    reference_to_the_standard: Optional[str] = None
    verification_date: Optional[date] = None
    corrective_action: Optional[str] = None
    id_audit: Optional[int] = None
    conclusion_date: Optional[date] = None
    finding_type: Optional[str] = None
    finding_image_path: Optional[str] = None
    countermeasure_image_path: Optional[str] = None

class FindingUpdate(BaseModel):
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    id_area: Optional[int] = None
    id_plant: Optional[int] = None
    finding_category: Optional[str] = None
    level: Optional[str] = None
    reference_to_the_standard: Optional[str] = None
    verification_date: Optional[date] = None
    corrective_action: Optional[str] = None
    id_audit: Optional[int] = None
    conclusion_date: Optional[date] = None
    finding_image_path: Optional[str] = None
    countermeasure_image_path: Optional[str] = None

# Incident
class IncidentCreate(BaseModel):
    folio: str
    level: str
    id_area: int
    id_sub_area: int
    id_plant: int
    date: date
    time: str
    status: Optional[str] = "Abierto"

class IncidentUpdate(BaseModel):
    folio: Optional[str] = None
    level: Optional[str] = None
    id_area: Optional[int] = None
    id_sub_area: Optional[int] = None
    id_plant: Optional[int] = None
    date: Optional[date] = None
    time: Optional[str] = None
    status: Optional[str] = None

# IncidentFormat
class IncidentFormatCreate(BaseModel):
    id_incident: int
    place: str
    cost_center_id: int
    shift: str
    affected_name: str
    affected_age: int
    affected_seniority: str
    affected_gender: str
    activity: str
    immediat_supervisor: str
    work_time_hours: float
    description: str
    injury_nature: str
    affected_body_part: str
    first_aid: bool
    recordable: bool
    lost_time: bool
    days_lost: int
    work_relapse: bool
    risk_level: str
    actions_taken: str

class IncidentFormatUpdate(BaseModel):
    place: Optional[str] = None
    cost_center_id: Optional[int] = None
    shift: Optional[str] = None
    affected_name: Optional[str] = None
    affected_age: Optional[int] = None
    affected_seniority: Optional[str] = None
    affected_gender: Optional[str] = None
    activity: Optional[str] = None
    immediat_supervisor: Optional[str] = None
    work_time_hours: Optional[float] = None
    description: Optional[str] = None
    injury_nature: Optional[str] = None
    affected_body_part: Optional[str] = None
    first_aid: Optional[bool] = None
    recordable: Optional[bool] = None
    lost_time: Optional[bool] = None
    days_lost: Optional[int] = None
    work_relapse: Optional[bool] = None
    risk_level: Optional[str] = None
    actions_taken: Optional[str] = None

# IncidentImage
class IncidentImageCreate(BaseModel):
    id_incident_format: int
    incident_image_path: str

# FactorTree
class FactorTreeCreate(BaseModel):
    id_incident_format: int
    m4: str
    actual: Optional[str] = None
    factor: Optional[str] = None
    control_point: Optional[str] = None
    standard: Optional[str] = None
    met_standard: Optional[bool] = None
    met_safety: Optional[bool] = None
    comments: Optional[str] = None

class FactorTreeUpdate(BaseModel):
    m4: Optional[str] = None
    actual: Optional[str] = None
    factor: Optional[str] = None
    control_point: Optional[str] = None
    standard: Optional[str] = None
    met_standard: Optional[bool] = None
    met_safety: Optional[bool] = None
    comments: Optional[str] = None

# InterveningFactor
class InterveningFactorCreate(BaseModel):
    id_incident_format: int
    name: str

class InterveningFactorUpdate(BaseModel):
    name: Optional[str] = None

# HazardBackground
class HazardBackgroundCreate(BaseModel):
    id_incident_format: int
    previous_fr1_incidents_presented: Optional[bool] = None
    existing_processes_or_areas_potential_for_incident: Optional[bool] = None
    processes_or_areas_potential_for_incident: Optional[str] = None
    risk_assessed_and_identified: Optional[bool] = None
    incident_category: Optional[str] = None
    horizontal_review: Optional[bool] = None
    horizontal_review_comment: Optional[str] = None
    new_risk_assessment_needed: Optional[bool] = None
    safety_dojo_reception_date: Optional[date] = None
    genba_dojo_reception_date: Optional[date] = None
    negligence_type: Optional[str] = None
    labor_report: Optional[bool] = None

class HazardBackgroundUpdate(BaseModel):
    previous_fr1_incidents_presented: Optional[bool] = None
    existing_processes_or_areas_potential_for_incident: Optional[bool] = None
    processes_or_areas_potential_for_incident: Optional[str] = None
    risk_assessed_and_identified: Optional[bool] = None
    incident_category: Optional[str] = None
    horizontal_review: Optional[bool] = None
    horizontal_review_comment: Optional[str] = None
    new_risk_assessment_needed: Optional[bool] = None
    safety_dojo_reception_date: Optional[date] = None
    genba_dojo_reception_date: Optional[date] = None
    negligence_type: Optional[str] = None
    labor_report: Optional[bool] = None

# CountermeasurePlan
class CountermeasurePlanCreate(BaseModel):
    id_incident_format: int
    what: str
    why: str
    how: str
    who: str
    when: date
    where: str
    id_control_hierarchy: int
    id_verification_method: int
    progress: int
    status: str
    evidence_image_path: Optional[str] = None

class CountermeasurePlanUpdate(BaseModel):
    what: Optional[str] = None
    why: Optional[str] = None
    how: Optional[str] = None
    who: Optional[str] = None
    when: Optional[date] = None
    where: Optional[str] = None
    id_control_hierarchy: Optional[int] = None
    id_verification_method: Optional[int] = None
    progress: Optional[int] = None
    status: Optional[str] = None
    evidence_image_path: Optional[str] = None

# ControlHierarchy
class ControlHierarchyCreate(BaseModel):
    name: str

class ControlHierarchyUpdate(BaseModel):
    name: Optional[str] = None

# VerificationMethod
class VerificationMethodCreate(BaseModel):
    name: str

class VerificationMethodUpdate(BaseModel):
    name: Optional[str] = None

# AnalysisParticipant
class AnalysisParticipantCreate(BaseModel):
    id_incident_format: int
    participant_type: str
    name: str
    department: str
    id_cost_center: Optional[int] = None

class AnalysisParticipantUpdate(BaseModel):
    participant_type: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None
    id_cost_center: Optional[int] = None

