"""Import keywords from a text file into keyword_library table.

Usage:
    cd EcoDreamOmni/apps/backend
    python -m scripts.import_keywords <path_to_keyword_file>

Example:
    python -m scripts.import_keywords ../../docs/关键词/keyword.md
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.models.viral_analyzer_orm import KeywordLibraryORM


def parse_keywords(filepath: str) -> list[str]:
    """Read keyword file and return deduplicated non-empty keywords."""
    keywords = []
    seen = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            kw = line.strip()
            if kw and kw not in seen and len(kw) <= 100:
                seen.add(kw)
                keywords.append(kw)
    return keywords


async def import_keywords(filepath: str):
    keywords = parse_keywords(filepath)
    print(f"Found {len(keywords)} unique keywords in {filepath}")

    async with AsyncSessionLocal() as db:
        # Check existing keywords
        result = await db.execute(select(KeywordLibraryORM.keyword))
        existing = {row[0] for row in result.all()}
        print(f"Existing keywords in DB: {len(existing)}")

        new_keywords = [kw for kw in keywords if kw not in existing]
        print(f"New keywords to insert: {len(new_keywords)}")

        if not new_keywords:
            print("No new keywords to import.")
            return

        # Batch insert
        batch_size = 500
        total_inserted = 0
        for i in range(0, len(new_keywords), batch_size):
            batch = new_keywords[i : i + batch_size]
            for kw in batch:
                db.add(
                    KeywordLibraryORM(
                        keyword=kw,
                        dimension="industry",
                        weight=1.0,
                        is_active=True,
                    )
                )
            await db.commit()
            total_inserted += len(batch)
            print(f"  Inserted batch {i//batch_size + 1}: {len(batch)} keywords")

        print(f"Done! Total inserted: {total_inserted}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.import_keywords <path_to_keyword_file>")
        sys.exit(1)
    filepath = sys.argv[1]
    asyncio.run(import_keywords(filepath))
