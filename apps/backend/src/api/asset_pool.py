"""
AssetPool API routes — ORM持久化版本 (W14).

Switched from in-memory dict storage to PostgreSQL/SQLAlchemy ORM.
Aligned with PRD V3.1 §AssetPool / TASK_V2.7.1 FUNC-1.
"""
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.core.file_upload import save_upload_file
from src.models.user import User
from src.services import asset_pool_function as apf

try:
    from PIL import Image  # noqa: F401
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

import os
import uuid

from src.services.stock_photo_client import stock_client

router = APIRouter(prefix="/assets", tags=["assets"])


class AssetUploadRequest(BaseModel):
    """素材上传请求"""
    filename: str
    file_url: str
    source_type: str = "OPERATOR_UPLOAD"
    license_type: str = "OWNED"
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    description: Optional[str] = None
    copyright_holder: Optional[str] = None
    copyright_year: Optional[int] = None
    usage_rights: Optional[List[str]] = None
    stock_source: Optional[str] = None
    stock_id: Optional[str] = None
    license_expiry: Optional[str] = None
    ai_model: Optional[str] = None
    ai_prompt: Optional[str] = None
    series_id: Optional[str] = None
    generate_thumbnail: bool = True


class AssetUpdateRequest(BaseModel):
    """素材更新请求"""
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    description: Optional[str] = None
    copyright_holder: Optional[str] = None
    usage_rights: Optional[List[str]] = None
    ai_disclosure: Optional[bool] = None


class AssetRecommendRequest(BaseModel):
    """素材推荐请求"""
    content_title: str
    content_body: str = ""
    content_tags: Optional[List[str]] = None
    series_id: Optional[str] = None
    target_count: int = 3


# Note: Define specific paths before generic ones to avoid routing conflicts

@router.get("/stats")
async def get_asset_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取素材统计"""
    stats = await apf.get_statistics(db)
    return stats


@router.post("/recommend")
async def get_recommendations(
    request: AssetRecommendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取素材推荐"""
    result = await apf.recommend_assets(
        db=db,
        content_title=request.content_title,
        content_body=request.content_body,
        content_tags=request.content_tags,
        series_id=request.series_id,
        target_count=request.target_count,
    )
    return result


@router.post("/upload", status_code=201)
async def upload_asset(
    request: AssetUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传素材"""
    asset = await apf.create_asset(
        db=db,
        filename=request.filename,
        file_url=request.file_url,
        source_type=request.source_type,
        license_type=request.license_type,
        tags=request.tags,
        category=request.category,
        description=request.description,
        copyright_holder=request.copyright_holder,
        copyright_year=request.copyright_year,
        usage_rights=request.usage_rights,
        stock_source=request.stock_source,
        stock_id=request.stock_id,
        license_expiry=request.license_expiry,
        ai_model=request.ai_model,
        ai_prompt=request.ai_prompt,
        series_id=request.series_id,
        uploaded_by=current_user.email,
        generate_thumbnail=request.generate_thumbnail,
    )
    await db.commit()
    return _asset_to_dict(asset)


def _generate_thumbnail(image_path: str, max_size: tuple = (300, 300)) -> str:
    """Generate a thumbnail for an image file. Returns thumbnail file URL."""
    if not HAS_PILLOW:
        return ""
    try:
        from pathlib import Path
        from PIL import Image  # noqa: F401
        import io
        from src.core.storage import get_storage

        path = Path(image_path)
        with Image.open(path) as img:
            img.thumbnail(max_size)
            buf = io.BytesIO()
            img.save(buf, format=img.format or "JPEG")
            thumb_bytes = buf.getvalue()

        # Upload thumbnail via storage layer (local or OSS)
        storage = get_storage()
        thumb_name = f"thumb_{path.name}"

        if hasattr(storage, "save_bytes"):
            result = storage.save_bytes(thumb_bytes, thumb_name, subdir="assets")
            return result["file_url"]
        # Fallback for protocols without save_bytes
        return ""
    except Exception:
        return ""


@router.post("/upload-file", status_code=201)
async def upload_asset_file(
    file: UploadFile = File(...),
    tags: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Multipart file upload for assets — saves to local storage + generates thumbnail."""
    # Save uploaded file
    upload_info = await save_upload_file(file, subdir="assets")

    # Generate thumbnail for images
    thumbnail_url = ""
    if upload_info["file_type"] == "image":
        thumbnail_url = _generate_thumbnail(upload_info["file_path"])

    # Parse tags from comma-separated string
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    asset = await apf.create_asset(
        db=db,
        filename=upload_info["original_name"],
        file_url=upload_info["file_url"],
        source_type="OPERATOR_UPLOAD",
        license_type="OWNED",
        tags=tag_list,
        category=category or "GENERAL_PET",
        description=description,
        uploaded_by=current_user.email,
        generate_thumbnail=False,
        meta_mime_type=upload_info["mime_type"],
    )
    # Manually set thumbnail if generated
    if thumbnail_url and hasattr(asset, "thumbnail_url"):
        asset.thumbnail_url = thumbnail_url
    await db.commit()
    return _asset_to_dict(asset)


# ─── Stock Photo API Integration ───


class StockSearchRequest(BaseModel):
    query: str
    source: str = "unsplash"
    per_page: int = 20


class StockSearchResponse(BaseModel):
    results: List[Dict]
    total: int


class StockImportRequest(BaseModel):
    stock_source: str
    stock_id: str
    download_url: str
    preview_url: str
    description: Optional[str] = None
    author_name: Optional[str] = None
    author_username: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


@router.post("/search-stock", response_model=StockSearchResponse)
async def search_stock(
    req: StockSearchRequest,
    user: User = Depends(get_current_user),
):
    """Search stock photos via external API (Unsplash)."""
    if req.source == "unsplash":
        results = await stock_client.search_unsplash(req.query, per_page=req.per_page)
        return StockSearchResponse(results=results, total=len(results))
    return StockSearchResponse(results=[], total=0)


@router.post("/import-stock", status_code=201)
async def import_stock(
    req: StockImportRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Import a selected stock photo into AssetPool."""
    # Download image and store via storage layer (OSS or local)
    safe_name = f"stock_{req.stock_source}_{req.stock_id}_{uuid.uuid4().hex[:8]}.jpg"

    import aiohttp
    from src.core.storage import get_storage

    async with aiohttp.ClientSession() as session:
        async with session.get(req.download_url) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=502, detail="Failed to download image from stock API")
            image_bytes = await resp.read()

    storage = get_storage()
    storage_result = storage.save_bytes(image_bytes, safe_name, subdir="stock")
    file_url = storage_result["file_url"]

    # Generate attribution metadata
    attribution = stock_client.get_attribution({
        "stock_source": req.stock_source,
        "stock_id": req.stock_id,
        "author_name": req.author_name,
        "author_username": req.author_username,
    })

    # Create asset record
    asset = await apf.create_asset(
        db=db,
        filename=req.description or f"{req.stock_source}_{req.stock_id}",
        file_url=file_url,
        thumbnail_url=file_url,
        source_type="STOCK_API",
        license_type="LICENSED",
        category=req.category,
        tags=req.tags or ["stock", req.stock_source],
        description=req.description,
        stock_source=req.stock_source,
        stock_id=req.stock_id,
        license_ref=str(attribution),
        copyright_validated=True,
        uploaded_by=user.email if hasattr(user, "email") else "system",
    )
    await db.commit()
    return _asset_to_dict(asset)


@router.get("")
async def get_assets(
    source_type: Optional[str] = Query(None),
    license_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    status: str = Query("ACTIVE"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取素材列表"""
    result = await apf.list_assets(
        db=db,
        source_type=source_type,
        license_type=license_type,
        category=category,
        tags=tags,
        status=status,
        limit=limit,
        offset=offset,
    )

    return {
        "items": [_asset_to_dict(a) for a in result["items"]],
        "total": result["total"],
        "limit": result["limit"],
        "offset": result["offset"],
    }


@router.get("/{asset_id}")
async def get_asset_detail(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取素材详情"""
    asset = await apf.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return _asset_to_dict(asset)


@router.patch("/{asset_id}")
async def patch_asset(
    asset_id: str,
    request: AssetUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新素材"""
    update_data = request.model_dump(exclude_unset=True)
    asset = await apf.update_asset(db, asset_id, **update_data)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    await db.commit()
    return _asset_to_dict(asset)


@router.delete("/{asset_id}")
async def remove_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除素材（软删除）"""
    success = await apf.delete_asset(db, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    await db.commit()
    return {"message": "Asset deleted"}


def _asset_to_dict(asset) -> dict:
    """将Asset转换为字典 — 兼容ORM对象与内存dataclass."""
    # Helper to handle Enum vs string fields
    def _v(field):
        return field.value if hasattr(field, "value") else field

    result = {
        "id": str(asset.id) if hasattr(asset, "id") else asset.id,
        "filename": asset.filename,
        "file_url": asset.file_url,
        "thumbnail_url": asset.thumbnail_url,
        "source_type": _v(asset.source_type),
        "license_type": _v(asset.license_type),
        "license_status": _v(asset.license_status),
        "copyright_holder": asset.copyright_holder,
        "copyright_year": asset.copyright_year,
        "usage_rights": asset.usage_rights or [],
        "copyright_validated": asset.copyright_validated,
        "stock_source": asset.stock_source,
        "stock_id": asset.stock_id,
        "license_expiry": asset.license_expiry.isoformat() if hasattr(asset.license_expiry, "isoformat") else asset.license_expiry,
        "ai_model": asset.ai_model,
        "ai_prompt": asset.ai_prompt,
        "ai_disclosure": asset.ai_disclosure,
        "category": asset.category,
        "tags": asset.tags or [],
        "description": asset.description,
        "series_id": asset.series_id,
        "status": _v(asset.status),
        "created_at": asset.created_at.isoformat() if hasattr(asset.created_at, "isoformat") else asset.created_at,
        "updated_at": asset.updated_at.isoformat() if hasattr(asset.updated_at, "isoformat") else asset.updated_at,
        "uploaded_by": asset.uploaded_by,
        "meta_mime_type": getattr(asset, "meta_mime_type", None),
        "meta_width": getattr(asset, "meta_width", None),
        "meta_height": getattr(asset, "meta_height", None),
        "type": _derive_asset_type(asset),
    }

    # AI元数据 — 兼容 dataclass 与 dict
    ai_meta = getattr(asset, "ai_metadata", None)
    if ai_meta:
        if hasattr(ai_meta, "model"):
            result["ai_metadata"] = {"model": ai_meta.model, "prompt": ai_meta.prompt}
        else:
            result["ai_metadata"] = ai_meta

    return result

def _derive_asset_type(asset) -> str:
    """Derive asset type from mime_type or filename extension."""
    mime = getattr(asset, "meta_mime_type", None)
    if mime and mime.startswith("image/"):
        return "image"
    if mime and mime.startswith("video/"):
        return "video"
    filename = getattr(asset, "filename", "")
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext in ("jpg", "jpeg", "png", "webp", "gif", "bmp", "svg"):
        return "image"
    if ext in ("mp4", "mov", "avi", "mkv", "webm"):
        return "video"
    return "unknown"


# ─── Phase 3-2: Secure file download endpoints ───

@router.get("/{asset_id}/download")
async def download_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download original asset file (auth-guarded).

    Returns a redirect to the storage URL (OSS CDN or local path).
    """
    asset = await apf.get_asset(db, asset_id)
    if not asset or asset.status == "DELETED":
        raise HTTPException(status_code=404, detail="Asset not found")

    file_url = asset.file_url
    if file_url.startswith("/uploads/"):
        # Local dev mode — serve via FileResponse
        file_path = os.path.join(settings.UPLOAD_DIR, file_url[len("/uploads/"):])
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        return FileResponse(
            path=file_path,
            filename=asset.filename,
            media_type=getattr(asset, "meta_mime_type", None) or "application/octet-stream",
        )

    # OSS mode — redirect to CDN URL
    return RedirectResponse(url=file_url)


@router.get("/{asset_id}/thumbnail")
async def download_thumbnail(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download asset thumbnail (auth-guarded).

    Returns a redirect to the storage URL (OSS CDN or local path).
    """
    asset = await apf.get_asset(db, asset_id)
    if not asset or asset.status == "DELETED":
        raise HTTPException(status_code=404, detail="Asset not found")

    thumb_url = asset.thumbnail_url
    if not thumb_url:
        raise HTTPException(status_code=404, detail="Thumbnail not available")

    if thumb_url.startswith("/uploads/"):
        # Local dev mode — serve via FileResponse
        thumb_path = os.path.join(settings.UPLOAD_DIR, thumb_url[len("/uploads/"):])
        if not os.path.isfile(thumb_path):
            raise HTTPException(status_code=404, detail="Thumbnail not found on disk")
        return FileResponse(path=thumb_path, media_type="image/jpeg")

    # OSS mode — redirect to CDN URL
    return RedirectResponse(url=thumb_url)
