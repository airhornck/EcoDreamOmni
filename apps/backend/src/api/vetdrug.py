"""VetDrugDB API — CRUD for veterinary drug entries + claim validation.

Wraps src/services/vetdrug_db_function.py.
"""

from typing import List, Optional

import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.core.database import get_db
from src.core.file_upload import save_upload_file
from src.services import vetdrug_db_function as vdf

router = APIRouter(prefix="/vetdrug", tags=["vetdrug"])


class VetDrugEntryCreate(BaseModel):
    approval_number: str
    product_name: str
    generic_name: Optional[str] = None
    english_name: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturer_address: Optional[str] = None
    ingredients: Optional[str] = None
    specifications: Optional[str] = None
    indications: Optional[str] = None
    usage_dosage: Optional[str] = None
    contraindications: Optional[str] = None
    adverse_reactions: Optional[str] = None
    precautions: Optional[str] = None
    drug_interactions: Optional[str] = None
    storage_conditions: Optional[str] = None
    category: Optional[str] = None
    drug_type: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    applicable_species: List[str] = []
    target_diseases: List[str] = []
    tags: List[str] = []
    brand_knowledge_id: Optional[str] = None
    status: str = "ACTIVE"
    data_source: str = "manual"


class VetDrugEntryOut(BaseModel):
    id: str
    approval_number: str
    product_name: str
    generic_name: Optional[str] = None
    english_name: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturer_address: Optional[str] = None
    ingredients: Optional[str] = None
    specifications: Optional[str] = None
    indications: Optional[str] = None
    usage_dosage: Optional[str] = None
    contraindications: Optional[str] = None
    adverse_reactions: Optional[str] = None
    precautions: Optional[str] = None
    drug_interactions: Optional[str] = None
    storage_conditions: Optional[str] = None
    category: Optional[str] = None
    drug_type: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    status: str
    applicable_species: List[str] = []
    target_diseases: List[str] = []
    tags: List[str] = []
    brand_knowledge_id: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    data_source: Optional[str] = None
    tenant_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VerifyClaimRequest(BaseModel):
    approval_number: str
    claimed_indications: List[str] = []
    claimed_effects: List[str] = []


@router.get("/drugs")
async def list_drugs(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await vdf.list_drugs(
        db, product_name=search, status=status, limit=limit, offset=offset
    )
    return {
        "items": [vdf.drug_to_dict(item) for item in result["items"]],
        "total": result["total"],
        "limit": result["limit"],
        "offset": result["offset"],
    }


@router.post("/drugs", status_code=201, response_model=VetDrugEntryOut)
async def create_drug(
    data: VetDrugEntryCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        drug = await vdf.create_drug(
            db=db,
            approval_number=data.approval_number,
            product_name=data.product_name,
            generic_name=data.generic_name,
            english_name=data.english_name,
            manufacturer=data.manufacturer,
            manufacturer_address=data.manufacturer_address,
            ingredients=data.ingredients,
            specifications=data.specifications,
            indications=data.indications,
            usage_dosage=data.usage_dosage,
            contraindications=data.contraindications,
            adverse_reactions=data.adverse_reactions,
            precautions=data.precautions,
            drug_interactions=data.drug_interactions,
            storage_conditions=data.storage_conditions,
            category=data.category,
            drug_type=data.drug_type,
            issue_date=data.issue_date,
            expiry_date=data.expiry_date,
            applicable_species=data.applicable_species,
            target_diseases=data.target_diseases,
            tags=data.tags,
            brand_knowledge_id=data.brand_knowledge_id,
            status=data.status,
            data_source=data.data_source,
            created_by=user.email if hasattr(user, "email") else "user",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.commit()
    return VetDrugEntryOut(**vdf.drug_to_dict(drug))


@router.get("/drugs/{drug_id}", response_model=VetDrugEntryOut)
async def get_drug(
    drug_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    drug = await vdf.get_drug(db, drug_id)
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")
    return VetDrugEntryOut(**vdf.drug_to_dict(drug))


@router.put("/drugs/{drug_id}", response_model=VetDrugEntryOut)
async def update_drug(
    drug_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    drug = await vdf.update_drug(db=db, drug_id=drug_id, **data)
    if not drug:
        raise HTTPException(status_code=404, detail="Drug not found")
    await db.commit()
    return VetDrugEntryOut(**vdf.drug_to_dict(drug))


@router.delete("/drugs/{drug_id}", status_code=204)
async def delete_drug(
    drug_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not await vdf.delete_drug(db, drug_id):
        raise HTTPException(status_code=404, detail="Drug not found")
    await db.commit()
    return None


@router.post("/validate-claim")
async def validate_claim(
    data: VerifyClaimRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await vdf.verify_claims(
        db=db,
        approval_number=data.approval_number,
        claimed_indications=data.claimed_indications,
        claimed_effects=data.claimed_effects,
    )
    return result


@router.post("/bulk-import")
async def bulk_import_drugs(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Bulk import veterinary drug entries from CSV or Excel (.xlsx).

    CSV columns: approval_number, product_name, generic_name, manufacturer,
    ingredients, indications, usage_dosage, expiry_date, category, drug_type

    Excel columns: supports both Chinese (批准文号, 通用名称, 商品名称, ...)
    and English headers. See document_parser.parse_vetdrug_excel for full mapping.
    """
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()

    if ext not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(
            status_code=400,
            detail="Supported formats: .csv, .xls, .xlsx",
        )

    items: List[dict] = []

    if ext == ".csv":
        content = await file.read()
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        required = {"approval_number", "product_name"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise HTTPException(
                status_code=400, detail=f"CSV must contain columns: {required}"
            )
        for row in reader:
            item = {
                "approval_number": row["approval_number"].strip(),
                "product_name": row["product_name"].strip(),
            }
            for optional in (
                "generic_name",
                "manufacturer",
                "manufacturer_address",
                "ingredients",
                "specifications",
                "indications",
                "usage_dosage",
                "contraindications",
                "adverse_reactions",
                "precautions",
                "drug_interactions",
                "storage_conditions",
                "category",
                "drug_type",
                "expiry_date",
            ):
                val = row.get(optional, "").strip()
                if val:
                    item[optional] = val
            for list_col in ("applicable_species", "target_diseases", "tags"):
                val = row.get(list_col, "").strip()
                if val:
                    delim = ";" if ";" in val else ","
                    item[list_col] = [v.strip() for v in val.split(delim) if v.strip()]
            items.append(item)
    else:
        from src.core import document_parser as dp

        saved = await save_upload_file(file, subdir="vetdrug_imports")
        try:
            items = dp.parse_vetdrug_excel(saved["file_path"])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    imported = 0
    errors = []
    for item in items:
        try:
            await vdf.create_drug(
                db=db,
                approval_number=item["approval_number"],
                product_name=item["product_name"],
                generic_name=item.get("generic_name"),
                manufacturer=item.get("manufacturer"),
                manufacturer_address=item.get("manufacturer_address"),
                ingredients=item.get("ingredients"),
                specifications=item.get("specifications"),
                indications=item.get("indications"),
                usage_dosage=item.get("usage_dosage"),
                contraindications=item.get("contraindications"),
                adverse_reactions=item.get("adverse_reactions"),
                precautions=item.get("precautions"),
                drug_interactions=item.get("drug_interactions"),
                storage_conditions=item.get("storage_conditions"),
                category=item.get("category"),
                drug_type=item.get("drug_type"),
                expiry_date=item.get("expiry_date"),
                applicable_species=item.get("applicable_species"),
                target_diseases=item.get("target_diseases"),
                tags=item.get("tags"),
                created_by=user.email if hasattr(user, "email") else "user",
                data_source="excel_import" if ext != ".csv" else "csv_import",
            )
            imported += 1
        except Exception as e:
            errors.append(
                {"approval_number": item.get("approval_number"), "error": str(e)}
            )

    await db.commit()
    return {"imported_count": imported, "errors": errors}


@router.get("/expiry-warnings")
async def get_expiry_warnings(
    days_ahead: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """返回即将过期的兽药批文列表（默认提前90天预警）."""
    warnings = await vdf.get_expiry_warnings(db, days_ahead=days_ahead)
    return {
        "warnings": [vdf.drug_to_dict(d) for d in warnings],
        "count": len(warnings),
        "days_ahead": days_ahead,
    }
