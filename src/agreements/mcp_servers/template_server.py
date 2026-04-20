"""MCP server for agreement templates."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("template-server")

TEMPLATES: dict[str, str] = {
    "NDA": """NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement ("Agreement") is entered into as of {{effective_date}} between:

{{party_1_name}} ("Disclosing Party")
and
{{party_2_name}} ("Receiving Party")

1. CONFIDENTIAL INFORMATION
The Receiving Party agrees to hold in strict confidence all Confidential Information disclosed by the Disclosing Party.

2. OBLIGATIONS
The Receiving Party shall not disclose, copy, or use the Confidential Information except as necessary for the purpose of {{purpose}}.

3. TERM
This Agreement shall remain in effect for {{term_years}} years from the Effective Date.

4. GOVERNING LAW
This Agreement shall be governed by the laws of {{governing_state}}.

IN WITNESS WHEREOF, the parties have executed this Agreement.

{{party_1_name}}: _______________________  Date: __________
{{party_2_name}}: _______________________  Date: __________
""",

    "ServiceAgreement": """SERVICE AGREEMENT

This Service Agreement ("Agreement") is made as of {{effective_date}} between:

{{client_name}} ("Client")
and
{{provider_name}} ("Service Provider")

1. SERVICES
Service Provider agrees to provide the following services: {{services_description}}

2. COMPENSATION
Client agrees to pay Service Provider {{payment_amount}} {{payment_terms}}.

3. TERM
This Agreement commences on {{start_date}} and continues until {{end_date}}, unless earlier terminated.

4. TERMINATION
Either party may terminate this Agreement with {{notice_days}} days written notice.

5. GOVERNING LAW
This Agreement shall be governed by the laws of {{governing_state}}.

{{client_name}}: _______________________  Date: __________
{{provider_name}}: _______________________  Date: __________
""",

    "Employment": """EMPLOYMENT AGREEMENT

This Employment Agreement ("Agreement") is entered into as of {{effective_date}} between:

{{employer_name}} ("Employer")
and
{{employee_name}} ("Employee")

1. POSITION
Employer hereby employs Employee as {{job_title}}, reporting to {{reporting_to}}.

2. COMPENSATION
Employee shall receive a base salary of {{salary}} {{pay_frequency}}.

3. BENEFITS
Employee shall be entitled to {{benefits_description}}.

4. START DATE
Employee's employment commences on {{start_date}}.

5. AT-WILL EMPLOYMENT
Employment is at-will and may be terminated by either party at any time.

6. GOVERNING LAW
This Agreement shall be governed by the laws of {{governing_state}}.

{{employer_name}}: _______________________  Date: __________
{{employee_name}}: _______________________  Date: __________
""",

    "Other": """GENERAL AGREEMENT

This Agreement ("Agreement") is entered into as of {{effective_date}} between:

{{party_1_name}}
and
{{party_2_name}}

1. PURPOSE
{{agreement_purpose}}

2. TERMS AND CONDITIONS
{{terms_and_conditions}}

3. DURATION
This Agreement is effective from {{start_date}} through {{end_date}}.

4. GOVERNING LAW
This Agreement shall be governed by the laws of {{governing_state}}.

{{party_1_name}}: _______________________  Date: __________
{{party_2_name}}: _______________________  Date: __________
""",
}


@mcp.tool()
def list_templates() -> str:
    """List all available agreement template types.

    Returns:
        JSON array of available template type names.
    """
    return json.dumps(list(TEMPLATES.keys()))


@mcp.tool()
def get_template(agreement_type: str) -> str:
    """Get the raw template for a given agreement type.

    Args:
        agreement_type: One of NDA, ServiceAgreement, Employment, Other.

    Returns:
        Template string with {{variable}} placeholders, or error JSON.
    """
    template = TEMPLATES.get(agreement_type)
    if template is None:
        available = list(TEMPLATES.keys())
        return json.dumps({"error": f"Unknown type '{agreement_type}'. Available: {available}"})
    return json.dumps({"type": agreement_type, "template": template})


@mcp.tool()
def render_template(agreement_type: str, variables: str) -> str:
    """Render a template by substituting {{variable}} placeholders.

    Args:
        agreement_type: One of NDA, ServiceAgreement, Employment, Other.
        variables: JSON object mapping placeholder names to values.

    Returns:
        Rendered agreement text or error JSON.
    """
    template = TEMPLATES.get(agreement_type)
    if template is None:
        return json.dumps({"error": f"Unknown type '{agreement_type}'"})

    vars_dict = json.loads(variables) if isinstance(variables, str) else variables
    rendered = template
    for key, value in vars_dict.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))

    # Report any unfilled placeholders
    remaining = re.findall(r"\{\{(\w+)\}\}", rendered)
    return json.dumps({
        "rendered": rendered,
        "unfilled_placeholders": remaining,
    })


if __name__ == "__main__":
    mcp.run()
