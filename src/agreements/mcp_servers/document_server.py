"""MCP server for document export and import."""

import base64
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from mcp.server.fastmcp import FastMCP

from agreements.database.session import AsyncSessionFactory, init_db
from agreements.models.agreement import AgreementORM, AgreementSchema

mcp = FastMCP("document-server")

_db_initialized = False


async def _ensure_db() -> None:
    global _db_initialized
    if not _db_initialized:
        await init_db()
        _db_initialized = True


@mcp.tool()
async def export_to_pdf(agreement_id: str) -> str:
    """Export an agreement to PDF and return it as base64-encoded bytes.

    Args:
        agreement_id: UUID of the agreement to export.

    Returns:
        JSON with base64-encoded PDF bytes and filename, or error.
    """
    from sqlalchemy import select

    await _ensure_db()
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(AgreementORM).where(AgreementORM.id == agreement_id))
        agreement = result.scalar_one_or_none()

    if agreement is None:
        return json.dumps({"error": f"Agreement {agreement_id} not found"})

    schema = AgreementSchema.from_orm(agreement)

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=inch, rightMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(schema.title, styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Type: {schema.agreement_type}", styles["Normal"]))
        story.append(Paragraph(f"Status: {schema.status}", styles["Normal"]))
        story.append(Paragraph(f"Version: {schema.version}", styles["Normal"]))
        story.append(Paragraph(f"Created: {schema.created_at.isoformat()}", styles["Normal"]))
        story.append(Spacer(1, 12))

        if schema.parties:
            story.append(Paragraph("Parties:", styles["Heading2"]))
            for party in schema.parties:
                name = party.get("name", "Unknown")
                role = party.get("role", "")
                story.append(Paragraph(f"  • {name} ({role})" if role else f"  • {name}", styles["Normal"]))
            story.append(Spacer(1, 12))

        story.append(Paragraph("Agreement Content:", styles["Heading2"]))
        for line in schema.content.split("\n"):
            if line.strip():
                story.append(Paragraph(line, styles["Normal"]))
            else:
                story.append(Spacer(1, 6))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
    except ImportError:
        # Fallback: plain-text PDF placeholder
        pdf_bytes = f"PDF Export: {schema.title}\n\n{schema.content}".encode()

    encoded = base64.b64encode(pdf_bytes).decode()
    filename = f"{agreement_id[:8]}_{schema.title.replace(' ', '_')[:30]}.pdf"
    return json.dumps({"filename": filename, "content_base64": encoded, "size_bytes": len(pdf_bytes)})


@mcp.tool()
def import_document(content: str, format: str = "text") -> str:
    """Import a document and extract plain text.

    Args:
        content: Raw document content (plain text or base64-encoded for binary formats).
        format: Input format: 'text' (default) or 'base64'.

    Returns:
        JSON with extracted plain text.
    """
    if format == "base64":
        try:
            decoded = base64.b64decode(content).decode("utf-8", errors="replace")
        except Exception as e:
            return json.dumps({"error": f"Failed to decode base64: {e}"})
        extracted = decoded
    else:
        extracted = content

    # Strip excessive whitespace
    lines = [line.rstrip() for line in extracted.splitlines()]
    cleaned = "\n".join(lines)
    return json.dumps({"text": cleaned, "char_count": len(cleaned)})


if __name__ == "__main__":
    mcp.run()
