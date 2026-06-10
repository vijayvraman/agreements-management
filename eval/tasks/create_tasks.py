"""Evaluation tasks for the Creator specialist — creating new agreements."""

import json
from eval.tasks.base import LABEnvironment, LABRubric, LABTask

CREATE_TASKS: list[LABTask] = [
    LABTask(
        id="create_nda_complete_001",
        intent="create",
        instruction=(
            "Create an NDA between Acme Corp (Disclosing Party) and Beta Ltd (Receiving Party), "
            "effective 2026-06-01, for business evaluation purposes, for 2 years, "
            "governed by California law."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms that an NDA was created. Both party names (Acme Corp and Beta Ltd) "
            "should appear. The response should indicate the agreement has been saved with a draft "
            "status and provide some form of confirmation (ID or title)."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'Acme Corp' as a party"),
            LABRubric("r2", "Response mentions 'Beta Ltd' as a party"),
            LABRubric("r3", "Response indicates an NDA was created (not queried or modified)"),
            LABRubric("r4", "Response includes confirmation of creation (agreement ID, title, or success message)"),
            LABRubric("r5", "Response does not fabricate party names not mentioned in the instruction"),
        ],
    ),
    LABTask(
        id="create_nda_minimal_002",
        intent="create",
        instruction="Create a simple NDA between TechStart Inc and InvestCo.",
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms creation of an NDA with both parties present. Since minimal "
            "info was given, the agent should use defaults or request template placeholders."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'TechStart Inc' or a recognizable abbreviation"),
            LABRubric("r2", "Response mentions 'InvestCo' or a recognizable abbreviation"),
            LABRubric("r3", "Response confirms an NDA (or non-disclosure agreement) was created"),
            LABRubric("r4", "Response does not fabricate details not present in the instruction"),
        ],
    ),
    LABTask(
        id="create_service_agreement_003",
        intent="create",
        instruction=(
            "Create a Service Agreement between GlobalCorp (Client) and DevShop LLC (Service Provider). "
            "DevShop will provide software development services at $10,000 per month. "
            "Agreement starts 2026-07-01 and ends 2027-06-30, governed by New York law, "
            "with 30 days termination notice."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms a Service Agreement was created with GlobalCorp and DevShop LLC "
            "as parties, including payment terms of $10,000 per month."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'GlobalCorp' as the client"),
            LABRubric("r2", "Response mentions 'DevShop LLC' as the service provider"),
            LABRubric("r3", "Response confirms a Service Agreement (not NDA or Employment) was created"),
            LABRubric("r4", "Response references payment amount ($10,000) or payment terms"),
            LABRubric("r5", "Response includes creation confirmation (ID or success message)"),
        ],
    ),
    LABTask(
        id="create_employment_agreement_004",
        intent="create",
        instruction=(
            "Create an Employment Agreement. Employer: Acme Corp. Employee: Jane Smith. "
            "Position: Senior Engineer. Salary: $150,000 per year. Benefits: health, dental, vision. "
            "Start date: 2026-08-01. Governed by Delaware law."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms an Employment Agreement was created with Acme Corp as employer "
            "and Jane Smith as employee, including salary information."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'Acme Corp' as the employer"),
            LABRubric("r2", "Response mentions 'Jane Smith' as the employee"),
            LABRubric("r3", "Response confirms an Employment Agreement was created"),
            LABRubric("r4", "Response references the salary ($150,000) or position (Senior Engineer)"),
            LABRubric("r5", "Response does not hallucinate additional employees or unrelated terms"),
        ],
    ),
    LABTask(
        id="create_nda_three_parties_005",
        intent="create",
        instruction=(
            "Create an NDA among three parties: AlphaCo, BetaCo, and GammaCo, "
            "all as mutual disclosing parties, effective 2026-09-01, for joint venture discussions."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms an NDA was created. All three party names should appear. "
            "The agent may note that the standard template is designed for two parties "
            "but should still create the agreement."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'AlphaCo' as a party"),
            LABRubric("r2", "Response mentions 'BetaCo' as a party"),
            LABRubric("r3", "Response mentions 'GammaCo' as a party"),
            LABRubric("r4", "Response confirms creation of an NDA"),
        ],
    ),
    LABTask(
        id="create_nda_california_006",
        intent="create",
        instruction=(
            "Draft an NDA between Sunrise Ventures (Disclosing Party) and Moonlight Partners "
            "(Receiving Party) for 3 years, governed by California law, "
            "for purposes of evaluating a potential acquisition."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms NDA created with Sunrise Ventures and Moonlight Partners, "
            "referencing California law or 3-year term."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'Sunrise Ventures'"),
            LABRubric("r2", "Response mentions 'Moonlight Partners'"),
            LABRubric("r3", "Response confirms NDA creation"),
            LABRubric("r4", "Response does not fabricate unrelated parties or terms"),
        ],
    ),
    LABTask(
        id="create_service_custom_termination_007",
        intent="create",
        instruction=(
            "Create a Service Agreement between DataFlow Inc (Client) and AnalyticsPlus (Provider). "
            "Services: data analytics and reporting. Payment: $5,000 per month. "
            "Term: 12 months starting 2026-10-01. Termination notice: 60 days."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms Service Agreement created with DataFlow Inc and AnalyticsPlus. "
            "Mentions payment amount or termination terms."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'DataFlow Inc'"),
            LABRubric("r2", "Response mentions 'AnalyticsPlus'"),
            LABRubric("r3", "Response confirms a Service Agreement was created"),
            LABRubric("r4", "Response references payment ($5,000) or services description"),
        ],
    ),
    LABTask(
        id="create_employment_equity_008",
        intent="create",
        instruction=(
            "Create an Employment Agreement for employee Marcus Webb joining StartupXYZ as CTO. "
            "Salary: $200,000/year. Benefits include stock options and health insurance. "
            "Start date: 2026-07-15."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms Employment Agreement created with Marcus Webb as employee "
            "and StartupXYZ as employer. References CTO position or salary."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'Marcus Webb'"),
            LABRubric("r2", "Response mentions 'StartupXYZ'"),
            LABRubric("r3", "Response confirms an Employment Agreement was created"),
            LABRubric("r4", "Response references the position (CTO) or salary ($200,000)"),
        ],
    ),
    LABTask(
        id="create_nda_ambiguous_type_009",
        intent="create",
        instruction=(
            "I need a confidentiality agreement between OmegaCorp and ZetaLtd to protect "
            "our trade secrets during partnership negotiations."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "A confidentiality agreement is an NDA. Response should confirm creation of an NDA "
            "or non-disclosure agreement with OmegaCorp and ZetaLtd."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'OmegaCorp'"),
            LABRubric("r2", "Response mentions 'ZetaLtd' or 'Zeta Ltd'"),
            LABRubric("r3", "Response confirms creation of a confidentiality or non-disclosure agreement"),
            LABRubric("r4", "Response does not route to query or modify instead of creating"),
        ],
    ),
    LABTask(
        id="create_nda_long_term_010",
        intent="create",
        instruction=(
            "Create an NDA between LifeScience Partners and BioResearch Group for 15 years, "
            "effective immediately, for pharmaceutical research collaboration."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms NDA created with LifeScience Partners and BioResearch Group. "
            "The 15-year term may be noted."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'LifeScience Partners'"),
            LABRubric("r2", "Response mentions 'BioResearch Group'"),
            LABRubric("r3", "Response confirms NDA creation"),
            LABRubric("r4", "Response does not fabricate additional parties"),
        ],
    ),
    LABTask(
        id="create_employment_atwill_011",
        intent="create",
        instruction=(
            "Create an at-will Employment Agreement for Rachel Torres as Marketing Director "
            "at MediaGroup Corp. Salary: $120,000 per year. Start date: 2026-06-15. "
            "Governed by Texas law."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms Employment Agreement created with Rachel Torres and MediaGroup Corp."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'Rachel Torres'"),
            LABRubric("r2", "Response mentions 'MediaGroup Corp'"),
            LABRubric("r3", "Response confirms an Employment Agreement was created"),
            LABRubric("r4", "Response does not fabricate unrelated terms"),
        ],
    ),
    LABTask(
        id="create_service_no_amount_012",
        intent="create",
        instruction=(
            "Create a Service Agreement between BuildIt Co (Client) and DesignPro (Provider) "
            "for UI/UX design services. No payment amount specified. 6-month term."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms Service Agreement created. Since no payment amount was given, "
            "the agent should either use a placeholder or note the missing field — "
            "it should NOT fabricate a specific dollar amount."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'BuildIt Co'"),
            LABRubric("r2", "Response mentions 'DesignPro'"),
            LABRubric("r3", "Response confirms a Service Agreement was created"),
            LABRubric("r4", "Response does not hallucinate a specific payment amount not in the instruction"),
        ],
    ),
    LABTask(
        id="create_nda_delaware_013",
        intent="create",
        instruction=(
            "Prepare an NDA between PharmaInnovate LLC and ClinicalTrials Corp for sharing "
            "drug trial data, effective 2026-11-01, 5 years, Delaware law."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms NDA created with PharmaInnovate and ClinicalTrials Corp."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'PharmaInnovate'"),
            LABRubric("r2", "Response mentions 'ClinicalTrials Corp'"),
            LABRubric("r3", "Response confirms NDA creation"),
        ],
    ),
    LABTask(
        id="create_general_agreement_014",
        intent="create",
        instruction=(
            "Create a general agreement between Summit Realty and FloorPlan Studios. "
            "Purpose: interior design consulting for Summit's new office. "
            "Duration: 3 months starting 2026-07-01."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms creation of a general or other-type agreement with Summit Realty "
            "and FloorPlan Studios."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'Summit Realty'"),
            LABRubric("r2", "Response mentions 'FloorPlan Studios'"),
            LABRubric("r3", "Response confirms agreement creation"),
            LABRubric("r4", "Response does not fabricate unrelated parties or amounts"),
        ],
    ),
    LABTask(
        id="create_nda_specific_dates_015",
        intent="create",
        instruction=(
            "I need an NDA. Parties: NovaTech (Disclosing) and CloudBase Inc (Receiving). "
            "Effective: 2026-06-20. Purpose: evaluating a software licensing deal. "
            "Term: 1 year. Governing law: Washington."
        ),
        environment=LABEnvironment(),
        expected_output_description=(
            "Response confirms NDA created with NovaTech and CloudBase Inc."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'NovaTech'"),
            LABRubric("r2", "Response mentions 'CloudBase Inc' or 'CloudBase'"),
            LABRubric("r3", "Response confirms NDA creation"),
            LABRubric("r4", "Response does not hallucinate unrelated parties"),
        ],
    ),
]
