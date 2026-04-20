"""MCP server exposing CRUD operations on the agreements database."""

import json
import sys
from pathlib import Path

# Ensure src is on the path when run as a subprocess
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from mcp.server.fastmcp import FastMCP

from agreements.database.session import AsyncSessionFactory, init_db
from agreements.models.agreement import AgreementORM, AgreementSchema

mcp = FastMCP("database-server")

_db_initialized = False


async def _ensure_db() -> None:
    global _db_initialized
    if not _db_initialized:
        await init_db()
        _db_initialized = True


@mcp.tool()
async def create_agreement(
    title: str,
    agreement_type: str,
    parties: str,
    content: str,
    status: str = "draft",
) -> str:
    """Create a new agreement.

    Args:
        title: Agreement title.
        agreement_type: One of NDA, ServiceAgreement, Employment, Other.
        parties: JSON-encoded list of {name, role} dicts.
        content: Full agreement text.
        status: draft | active | expired | terminated (default: draft).

    Returns:
        JSON representation of the created agreement.
    """
    import uuid
    from datetime import datetime

    await _ensure_db()
    parties_list = json.loads(parties) if isinstance(parties, str) else parties
    agreement = AgreementORM(
        id=str(uuid.uuid4()),
        title=title,
        agreement_type=agreement_type,
        parties=parties_list,
        content=content,
        status=status,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata_={},
    )
    async with AsyncSessionFactory() as session:
        session.add(agreement)
        await session.commit()
        await session.refresh(agreement)
    return AgreementSchema.from_orm(agreement).model_dump_json()


@mcp.tool()
async def get_agreement(id: str) -> str:
    """Retrieve an agreement by ID.

    Args:
        id: UUID of the agreement.

    Returns:
        JSON representation or error message.
    """
    from sqlalchemy import select

    await _ensure_db()
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(AgreementORM).where(AgreementORM.id == id))
        agreement = result.scalar_one_or_none()
    if agreement is None:
        return json.dumps({"error": f"Agreement {id} not found"})
    return AgreementSchema.from_orm(agreement).model_dump_json()


@mcp.tool()
async def list_agreements(
    status: str | None = None,
    agreement_type: str | None = None,
    party_name: str | None = None,
) -> str:
    """List agreements with optional filters.

    Args:
        status: Filter by status (draft/active/expired/terminated).
        agreement_type: Filter by type (NDA/ServiceAgreement/Employment/Other).
        party_name: Filter by party name (substring match).

    Returns:
        JSON array of matching agreements.
    """
    from sqlalchemy import select

    await _ensure_db()
    async with AsyncSessionFactory() as session:
        stmt = select(AgreementORM)
        if status:
            stmt = stmt.where(AgreementORM.status == status)
        if agreement_type:
            stmt = stmt.where(AgreementORM.agreement_type == agreement_type)
        result = await session.execute(stmt)
        agreements = result.scalars().all()

    schemas = [AgreementSchema.from_orm(a) for a in agreements]
    if party_name:
        pn_lower = party_name.lower()
        schemas = [
            a for a in schemas
            if any(pn_lower in p.get("name", "").lower() for p in a.parties)
        ]
    return json.dumps([json.loads(a.model_dump_json()) for a in schemas])


@mcp.tool()
async def update_agreement(id: str, fields_to_update: str) -> str:
    """Update fields of an existing agreement.

    Args:
        id: UUID of the agreement.
        fields_to_update: JSON object with fields to update (title, content, status, etc.).

    Returns:
        JSON representation of the updated agreement or error.
    """
    from datetime import datetime

    from sqlalchemy import select

    await _ensure_db()
    updates = json.loads(fields_to_update) if isinstance(fields_to_update, str) else fields_to_update

    async with AsyncSessionFactory() as session:
        result = await session.execute(select(AgreementORM).where(AgreementORM.id == id))
        agreement = result.scalar_one_or_none()
        if agreement is None:
            return json.dumps({"error": f"Agreement {id} not found"})

        allowed = {"title", "agreement_type", "parties", "content", "status", "metadata_"}
        for key, value in updates.items():
            mapped_key = "metadata_" if key == "metadata" else key
            if mapped_key in allowed:
                setattr(agreement, mapped_key, value)
        agreement.version += 1
        agreement.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(agreement)
    return AgreementSchema.from_orm(agreement).model_dump_json()


@mcp.tool()
async def search_agreements(query: str) -> str:
    """Full-text search on agreement title and content.

    Args:
        query: Search string.

    Returns:
        JSON array of matching agreements.
    """
    from sqlalchemy import or_, select

    await _ensure_db()
    q = f"%{query}%"
    async with AsyncSessionFactory() as session:
        stmt = select(AgreementORM).where(
            or_(
                AgreementORM.title.ilike(q),
                AgreementORM.content.ilike(q),
            )
        )
        result = await session.execute(stmt)
        agreements = result.scalars().all()
    return json.dumps([json.loads(AgreementSchema.from_orm(a).model_dump_json()) for a in agreements])


@mcp.tool()
async def delete_agreement(id: str) -> str:
    """Delete an agreement by ID.

    Args:
        id: UUID of the agreement.

    Returns:
        Confirmation message or error.
    """
    from sqlalchemy import select

    await _ensure_db()
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(AgreementORM).where(AgreementORM.id == id))
        agreement = result.scalar_one_or_none()
        if agreement is None:
            return json.dumps({"error": f"Agreement {id} not found"})
        await session.delete(agreement)
        await session.commit()
    return json.dumps({"success": True, "deleted_id": id})


if __name__ == "__main__":
    mcp.run()
