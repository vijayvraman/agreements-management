"""Unit tests for MCP server tools (invoked directly, without MCP transport)."""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
async def db(tmp_path):
    """Set up a temp SQLite database and patch the session factory for tests."""
    db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from agreements.models.agreement import Base

    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Patch the module-level objects in database_server and document_server
    import agreements.mcp_servers.database_server as db_srv
    import agreements.mcp_servers.document_server as doc_srv

    original_db_factory = db_srv.AsyncSessionFactory
    original_db_flag = db_srv._db_initialized
    original_doc_factory = doc_srv.AsyncSessionFactory
    original_doc_flag = doc_srv._db_initialized

    db_srv.AsyncSessionFactory = session_factory
    db_srv._db_initialized = True
    doc_srv.AsyncSessionFactory = session_factory
    doc_srv._db_initialized = True

    yield db_srv

    db_srv.AsyncSessionFactory = original_db_factory
    db_srv._db_initialized = original_db_flag
    doc_srv.AsyncSessionFactory = original_doc_factory
    doc_srv._db_initialized = original_doc_flag
    await engine.dispose()


# ---------------------------------------------------------------------------
# Template server tests (sync, no DB)
# ---------------------------------------------------------------------------


def test_list_templates():
    from agreements.mcp_servers.template_server import list_templates

    result = json.loads(list_templates())
    assert isinstance(result, list)
    assert "NDA" in result
    assert "ServiceAgreement" in result


def test_get_template_nda():
    from agreements.mcp_servers.template_server import get_template

    result = json.loads(get_template("NDA"))
    assert "template" in result
    assert "{{party_1_name}}" in result["template"]


def test_get_template_unknown():
    from agreements.mcp_servers.template_server import get_template

    result = json.loads(get_template("Unknown"))
    assert "error" in result


def test_render_template():
    from agreements.mcp_servers.template_server import render_template

    variables = json.dumps({
        "party_1_name": "Acme Corp",
        "party_2_name": "Beta Ltd",
        "effective_date": "2026-04-20",
        "purpose": "business evaluation",
        "term_years": "2",
        "governing_state": "California",
    })
    result = json.loads(render_template("NDA", variables))
    assert "rendered" in result
    assert "Acme Corp" in result["rendered"]
    assert "Beta Ltd" in result["rendered"]


def test_render_template_partial():
    from agreements.mcp_servers.template_server import render_template

    variables = json.dumps({"party_1_name": "Acme Corp"})
    result = json.loads(render_template("NDA", variables))
    assert "unfilled_placeholders" in result
    assert len(result["unfilled_placeholders"]) > 0


# ---------------------------------------------------------------------------
# Database server tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_and_get_agreement(db):
    from agreements.mcp_servers import database_server as db_srv

    parties = json.dumps([{"name": "Acme Corp", "role": "Disclosing Party"}])
    created_json = await db_srv.create_agreement(
        title="Test NDA",
        agreement_type="NDA",
        parties=parties,
        content="This is a test NDA.",
    )
    created = json.loads(created_json)
    assert created["title"] == "Test NDA"
    assert created["status"] == "draft"

    fetched_json = await db_srv.get_agreement(created["id"])
    fetched = json.loads(fetched_json)
    assert fetched["id"] == created["id"]


@pytest.mark.asyncio
async def test_list_and_search_agreements(db):
    from agreements.mcp_servers import database_server as db_srv

    parties = json.dumps([{"name": "Acme Corp", "role": "party"}])
    await db_srv.create_agreement("Alpha Agreement", "NDA", parties, "content alpha")
    await db_srv.create_agreement("Beta Agreement", "ServiceAgreement", parties, "content beta")

    all_list = json.loads(await db_srv.list_agreements())
    assert len(all_list) == 2

    nda_list = json.loads(await db_srv.list_agreements(agreement_type="NDA"))
    assert len(nda_list) == 1
    assert nda_list[0]["title"] == "Alpha Agreement"

    search_result = json.loads(await db_srv.search_agreements("beta"))
    assert any("Beta" in a["title"] for a in search_result)


@pytest.mark.asyncio
async def test_update_agreement(db):
    from agreements.mcp_servers import database_server as db_srv

    parties = json.dumps([])
    created = json.loads(await db_srv.create_agreement("To Update", "NDA", parties, "original"))
    updated = json.loads(await db_srv.update_agreement(
        created["id"], json.dumps({"status": "active", "content": "updated content"})
    ))
    assert updated["status"] == "active"
    assert updated["content"] == "updated content"
    assert updated["version"] == 2


@pytest.mark.asyncio
async def test_delete_agreement(db):
    from agreements.mcp_servers import database_server as db_srv

    parties = json.dumps([])
    created = json.loads(await db_srv.create_agreement("To Delete", "NDA", parties, "content"))
    result = json.loads(await db_srv.delete_agreement(created["id"]))
    assert result["success"] is True

    fetched = json.loads(await db_srv.get_agreement(created["id"]))
    assert "error" in fetched


# ---------------------------------------------------------------------------
# Document server tests
# ---------------------------------------------------------------------------


def test_import_document_text():
    from agreements.mcp_servers.document_server import import_document

    result = json.loads(import_document("Hello World\nThis is a test.", "text"))
    assert "Hello World" in result["text"]
    assert result["char_count"] > 0


def test_import_document_base64():
    import base64

    from agreements.mcp_servers.document_server import import_document

    encoded = base64.b64encode(b"Base64 content here").decode()
    result = json.loads(import_document(encoded, "base64"))
    assert "Base64 content here" in result["text"]
