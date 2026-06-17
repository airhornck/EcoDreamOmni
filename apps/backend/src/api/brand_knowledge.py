"""BrandKnowledge API — CRUD for brand knowledge entries.

Wraps src/services/brand_knowledge_function.py.
"""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.core.database import get_db
from src.core import document_parser
from src.services import brand_knowledge_function as bkf

router = APIRouter(prefix="/brand-knowledge", tags=["brand-knowledge"])


class BrandKnowledgeEntryCreate(BaseModel):
    entry_type: str
    name: str
    content: str
    product_id: Optional[str] = None
    approval_number: Optional[str] = None
    sku_code: Optional[str] = None
    brand_name: Optional[str] = None
    prohibited_claims: List[str] = []
    required_disclaimers: List[str] = []
    asset_ids: List[str] = []


class BrandKnowledgeEntryOut(BaseModel):
    id: str
    entry_type: str
    name: str
    content: str
    product_id: Optional[str] = None
    approval_number: Optional[str] = None
    sku_code: Optional[str] = None
    brand_name: Optional[str] = None
    prohibited_claims: List[str] = []
    required_disclaimers: List[str] = []
    version: int
    is_latest: bool
    parent_id: Optional[str] = None
    asset_ids: List[str] = []
    created_by: str
    updated_by: Optional[str] = None
    change_reason: Optional[str] = None
    tenant_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@router.get("/entries")
async def list_entries(
    entry_type: Optional[str] = None,
    brand_name: Optional[str] = None,
    product_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if search:
        items = await bkf.search_by_content(db, query_text=search, entry_type=entry_type)
    else:
        result = await bkf.list_entries(
            db, entry_type=entry_type, brand_name=brand_name, limit=limit, offset=offset
        )
        items = result["items"]

    if product_id:
        items = [item for item in items if getattr(item, "product_id", None) == product_id]

    total = len(items)
    return {
        "items": [bkf.entry_to_dict(item) for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/entries", status_code=201, response_model=BrandKnowledgeEntryOut)
async def create_entry(
    data: BrandKnowledgeEntryCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    entry = await bkf.create_entry(
        db=db,
        entry_type=data.entry_type,
        name=data.name,
        content=data.content,
        product_id=data.product_id,
        approval_number=data.approval_number,
        sku_code=data.sku_code,
        brand_name=data.brand_name,
        prohibited_claims=data.prohibited_claims,
        required_disclaimers=data.required_disclaimers,
        asset_ids=data.asset_ids,
        created_by=user.email if hasattr(user, "email") else "user",
    )
    await db.commit()
    return BrandKnowledgeEntryOut(**bkf.entry_to_dict(entry))


@router.get("/entries/{entry_id}", response_model=BrandKnowledgeEntryOut)
async def get_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    entry = await bkf.get_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return BrandKnowledgeEntryOut(**bkf.entry_to_dict(entry))


@router.put("/entries/{entry_id}", response_model=BrandKnowledgeEntryOut)
async def update_entry(
    entry_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    entry = await bkf.update_entry(
        db=db,
        entry_id=entry_id,
        updated_by=user.email if hasattr(user, "email") else "user",
        **data,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.commit()
    return BrandKnowledgeEntryOut(**bkf.entry_to_dict(entry))


@router.delete("/entries/{entry_id}", status_code=204)
async def delete_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not await bkf.delete_entry(db, entry_id):
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.commit()
    return None


@router.post("/bulk-import")
async def bulk_import_entries(
    file: UploadFile = File(...),
    entry_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Bulk import brand knowledge entries from CSV / PDF / Word / Excel.

    - CSV: columns entry_type, name, content (+ optional product_id, approval_number, sku_code, brand_name, prohibited_claims, required_disclaimers)
    - PDF: one entry per page
    - Word (docx): one entry for the whole document
    - Excel (xlsx): one entry per row (first row = headers)
    """
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()

    if ext not in {".csv", ".pdf", ".docx", ".doc", ".xlsx", ".xls"}:
        raise HTTPException(
            status_code=400,
            detail="Supported formats: .csv, .pdf, .docx, .xls, .xlsx",
        )

    items: List[dict] = []

    if ext == ".csv":
        content = await file.read()
        text = content.decode("utf-8-sig")
        try:
            items = document_parser.parse_csv_text(text)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        from src.core.file_upload import save_upload_file

        saved = await save_upload_file(file, subdir="brand_knowledge")
        try:
            parsed = document_parser.parse_document(saved["file_path"])
            for p in parsed:
                items.append(
                    {
                        "entry_type": entry_type or "brand_info",
                        "name": p["name"],
                        "content": p["content"],
                    }
                )
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Parse failed: {str(e)}")

    imported = 0
    errors = []
    for item in items:
        try:
            await bkf.create_entry(
                db=db,
                entry_type=item["entry_type"],
                name=item["name"],
                content=item["content"],
                product_id=item.get("product_id"),
                approval_number=item.get("approval_number"),
                sku_code=item.get("sku_code"),
                brand_name=item.get("brand_name"),
                prohibited_claims=item.get("prohibited_claims"),
                required_disclaimers=item.get("required_disclaimers"),
                created_by=user.email if hasattr(user, "email") else "user",
            )
            imported += 1
        except Exception as e:
            errors.append({"name": item.get("name"), "error": str(e)})

    await db.commit()
    return {"imported_count": imported, "errors": errors}
