"""In-process specialist dispatch for mock evaluation mode.

Bypasses A2A HTTP and MCP subprocess overhead while still exercising real specialist
LLM logic by building inline LangChain tools backed by the patched in-memory database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool


def _build_creator_tools() -> list:
    """Inline LangChain tools for the creator specialist."""
    import agreements.mcp_servers.database_server as db_srv
    import agreements.mcp_servers.template_server as tmpl_srv

    @tool
    async def database_create_agreement(
        title: str,
        agreement_type: str,
        parties: str,
        content: str,
        status: str = "draft",
    ) -> str:
        """Create a new agreement. agreement_type: NDA, ServiceAgreement, Employment, Other.
        parties: JSON list of {name, role}. status: draft|active|expired|terminated."""
        return await db_srv.create_agreement(
            title=title,
            agreement_type=agreement_type,
            parties=parties,
            content=content,
            status=status,
        )

    @tool
    def template_list_templates() -> str:
        """List all available agreement template types."""
        return tmpl_srv.list_templates()

    @tool
    def template_get_template(agreement_type: str) -> str:
        """Get the raw template for a given agreement type (NDA, ServiceAgreement, Employment, Other)."""
        return tmpl_srv.get_template(agreement_type)

    @tool
    def template_render_template(agreement_type: str, variables: str) -> str:
        """Render a template by substituting {{variable}} placeholders. variables: JSON object."""
        return tmpl_srv.render_template(agreement_type, variables)

    @tool
    async def document_export_to_pdf(agreement_id: str) -> str:
        """Export an agreement to PDF and return base64-encoded bytes."""
        import agreements.mcp_servers.document_server as doc_srv
        return await doc_srv.export_to_pdf(agreement_id)

    return [
        database_create_agreement,
        template_list_templates,
        template_get_template,
        template_render_template,
        document_export_to_pdf,
    ]


def _build_query_tools() -> list:
    """Inline LangChain tools for the query specialist."""
    import agreements.mcp_servers.database_server as db_srv

    @tool
    async def database_get_agreement(id: str) -> str:
        """Retrieve an agreement by its UUID."""
        return await db_srv.get_agreement(id)

    @tool
    async def database_list_agreements(
        status: str = None,
        agreement_type: str = None,
        party_name: str = None,
    ) -> str:
        """List agreements with optional filters. status: draft|active|expired|terminated.
        agreement_type: NDA|ServiceAgreement|Employment|Other. party_name: substring match."""
        return await db_srv.list_agreements(
            status=status,
            agreement_type=agreement_type,
            party_name=party_name,
        )

    @tool
    async def database_search_agreements(query: str) -> str:
        """Full-text search on agreement title and content."""
        return await db_srv.search_agreements(query)

    @tool
    async def document_export_to_pdf(agreement_id: str) -> str:
        """Export an agreement to PDF and return base64-encoded bytes."""
        import agreements.mcp_servers.document_server as doc_srv
        return await doc_srv.export_to_pdf(agreement_id)

    return [
        database_get_agreement,
        database_list_agreements,
        database_search_agreements,
        document_export_to_pdf,
    ]


def _build_modifier_tools() -> list:
    """Inline LangChain tools for the modifier specialist."""
    import agreements.mcp_servers.database_server as db_srv
    import agreements.mcp_servers.template_server as tmpl_srv

    @tool
    async def database_get_agreement(id: str) -> str:
        """Retrieve an agreement by its UUID."""
        return await db_srv.get_agreement(id)

    @tool
    async def database_update_agreement(id: str, fields_to_update: str) -> str:
        """Update fields of an existing agreement. fields_to_update: JSON object with fields to change."""
        return await db_srv.update_agreement(id, fields_to_update)

    @tool
    async def database_delete_agreement(id: str) -> str:
        """Delete an agreement by its UUID."""
        return await db_srv.delete_agreement(id)

    @tool
    def template_render_template(agreement_type: str, variables: str) -> str:
        """Render a template by substituting {{variable}} placeholders. variables: JSON object."""
        return tmpl_srv.render_template(agreement_type, variables)

    @tool
    async def document_export_to_pdf(agreement_id: str) -> str:
        """Export an agreement to PDF and return base64-encoded bytes."""
        import agreements.mcp_servers.document_server as doc_srv
        return await doc_srv.export_to_pdf(agreement_id)

    @tool
    def document_import_document(content: str, format: str = "text") -> str:
        """Import a document and extract plain text. format: 'text' or 'base64'."""
        import agreements.mcp_servers.document_server as doc_srv
        return doc_srv.import_document(content, format)

    return [
        database_get_agreement,
        database_update_agreement,
        database_delete_agreement,
        template_render_template,
        document_export_to_pdf,
        document_import_document,
    ]


class MockAgreementsBackend:
    """Dispatches to specialist graphs in-process using real MCP tool functions.

    The database session factory must already be patched before calling dispatch().
    Tools are created fresh per dispatch call so they capture the current module state.
    """

    async def dispatch(self, intent: str, task_description: str) -> str:
        """Run the appropriate specialist graph and return its text response."""
        if intent == "create":
            return await self._run_specialist(
                "agreements.agents.creator.graph",
                _build_creator_tools(),
                task_description,
            )
        elif intent == "modify":
            return await self._run_specialist(
                "agreements.agents.modifier.graph",
                _build_modifier_tools(),
                task_description,
            )
        else:
            return await self._run_specialist(
                "agreements.agents.query.graph",
                _build_query_tools(),
                task_description,
            )

    async def _run_specialist(
        self,
        graph_module_path: str,
        tools: list,
        task_description: str,
    ) -> str:
        import importlib
        graph_module = importlib.import_module(graph_module_path)
        graph = await graph_module.build_graph(tools)
        result = await graph.ainvoke({"messages": [HumanMessage(content=task_description)]})
        last_message = result["messages"][-1]
        return last_message.content if hasattr(last_message, "content") else str(last_message)
