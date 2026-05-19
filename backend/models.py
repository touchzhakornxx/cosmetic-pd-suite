from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any


class ScrapeRequest(BaseModel):
    url: HttpUrl


class Ingredient(BaseModel):
    name: str
    percentage: Optional[float] = None


class ScrapeResult(BaseModel):
    job_id: str
    url: HttpUrl
    raw_html: Optional[str]
    parsed: List[Ingredient]
    errors: Optional[List[str]] = None


class MaterialCreate(BaseModel):
    trade_name: str
    inci_name: str
    supplier: Optional[str] = None
    function_category: Optional[str] = None
    price_per_kg: float = 0.0
    cas_number: Optional[str] = None
    is_active: bool = True


class MaterialPatch(BaseModel):
    price_per_kg: Optional[float] = None
    cas_number: Optional[str] = None
    trade_name: Optional[str] = None
    supplier: Optional[str] = None
    function_category: Optional[str] = None
    is_active: Optional[bool] = None


class ComplianceIngredient(BaseModel):
    inci_name: str
    percentage: float = 0.0
    material_id: Optional[str] = None
    trade_name: Optional[str] = None


class ComplianceCheckRequest(BaseModel):
    ingredients: List[ComplianceIngredient]


class FormulaIngredientInput(BaseModel):
    material_id: str
    phase: str
    percentage: float


class FormulaCreate(BaseModel):
    formula_code: str
    product_name: str
    target_skin_type: str
    batch_size_g: float = 100.0
    loss_percentage: float = 0.0
    ingredients: List[FormulaIngredientInput] = []
