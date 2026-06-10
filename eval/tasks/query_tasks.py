"""Evaluation tasks for the Query specialist — searching and retrieving agreements."""

import json
from eval.tasks.base import LABEnvironment, LABRubric, LABTask

# Shared seed data used across query tasks
_NDA_ACME_BETA = {
    "title": "Acme-Beta NDA 2026",
    "agreement_type": "NDA",
    "parties": json.dumps([
        {"name": "Acme Corp", "role": "Disclosing Party"},
        {"name": "Beta Ltd", "role": "Receiving Party"},
    ]),
    "content": "This NDA governs confidentiality between Acme Corp and Beta Ltd.",
    "status": "active",
}

_SERVICE_GLOBALCORP = {
    "title": "GlobalCorp DevShop Service Agreement",
    "agreement_type": "ServiceAgreement",
    "parties": json.dumps([
        {"name": "GlobalCorp", "role": "Client"},
        {"name": "DevShop LLC", "role": "Provider"},
    ]),
    "content": "Software development services at $10,000/month.",
    "status": "active",
}

_EMPLOYMENT_JANE = {
    "title": "Jane Smith Employment Agreement",
    "agreement_type": "Employment",
    "parties": json.dumps([
        {"name": "Acme Corp", "role": "Employer"},
        {"name": "Jane Smith", "role": "Employee"},
    ]),
    "content": "Employment as Senior Engineer, $150,000/year.",
    "status": "active",
}

_NDA_DRAFT = {
    "title": "Sunrise Ventures Draft NDA",
    "agreement_type": "NDA",
    "parties": json.dumps([
        {"name": "Sunrise Ventures", "role": "Disclosing Party"},
        {"name": "Moonlight Partners", "role": "Receiving Party"},
    ]),
    "content": "Preliminary NDA for acquisition discussions.",
    "status": "draft",
}

_EXPIRED_SERVICE = {
    "title": "OldCorp Service Agreement",
    "agreement_type": "ServiceAgreement",
    "parties": json.dumps([
        {"name": "OldCorp", "role": "Client"},
        {"name": "VendorX", "role": "Provider"},
    ]),
    "content": "Expired services contract.",
    "status": "expired",
}

_ALL_SEED = [_NDA_ACME_BETA, _SERVICE_GLOBALCORP, _EMPLOYMENT_JANE, _NDA_DRAFT, _EXPIRED_SERVICE]

QUERY_TASKS: list[LABTask] = [
    LABTask(
        id="query_list_all_001",
        intent="query",
        instruction="List all agreements in the system.",
        environment=LABEnvironment(seed_agreements=_ALL_SEED),
        expected_output_description=(
            "Response should list all 5 seeded agreements, referencing their titles or types."
        ),
        rubrics=[
            LABRubric("r1", "Response lists multiple agreements (not just one)"),
            LABRubric("r2", "Response mentions at least one NDA"),
            LABRubric("r3", "Response mentions at least one Service Agreement or Employment Agreement"),
            LABRubric("r4", "Response does not claim the database is empty"),
        ],
    ),
    LABTask(
        id="query_list_active_ndas_002",
        intent="query",
        instruction="Show me all active NDAs.",
        environment=LABEnvironment(seed_agreements=_ALL_SEED),
        expected_output_description=(
            "Response should list only active NDAs. The Acme-Beta NDA is active; "
            "the Sunrise Ventures NDA is draft. So only one NDA should appear as active."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'Acme-Beta' or 'Acme Corp' in context of an NDA"),
            LABRubric("r2", "Response does not list the Sunrise Ventures draft NDA as active"),
            LABRubric("r3", "Response focuses on NDAs (not service or employment agreements)"),
            LABRubric("r4", "Response does not fabricate NDA titles not in the system"),
        ],
    ),
    LABTask(
        id="query_filter_by_party_003",
        intent="query",
        instruction="Find all agreements involving Acme Corp.",
        environment=LABEnvironment(seed_agreements=_ALL_SEED),
        expected_output_description=(
            "Acme Corp appears in the Acme-Beta NDA (as Disclosing Party) and in the "
            "Jane Smith Employment Agreement (as Employer). Both should be returned."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions the Acme-Beta NDA"),
            LABRubric("r2", "Response mentions the Jane Smith Employment Agreement or Acme Corp as employer"),
            LABRubric("r3", "Response does not include GlobalCorp or OldCorp agreements"),
            LABRubric("r4", "Response does not fabricate additional Acme Corp agreements"),
        ],
    ),
    LABTask(
        id="query_search_by_keyword_004",
        intent="query",
        instruction="Search for agreements containing 'software development'.",
        environment=LABEnvironment(seed_agreements=_ALL_SEED),
        expected_output_description=(
            "The GlobalCorp DevShop Service Agreement content mentions software development. "
            "Response should return that agreement."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'GlobalCorp' or 'DevShop' or the Service Agreement"),
            LABRubric("r2", "Response does not include unrelated agreements as matching"),
            LABRubric("r3", "Response does not fabricate agreement content"),
        ],
    ),
    LABTask(
        id="query_count_by_status_005",
        intent="query",
        instruction="How many agreements are currently in draft status?",
        environment=LABEnvironment(seed_agreements=_ALL_SEED),
        expected_output_description=(
            "One agreement (Sunrise Ventures Draft NDA) has draft status. "
            "Response should indicate 1 draft agreement."
        ),
        rubrics=[
            LABRubric("r1", "Response indicates there is 1 draft agreement (or mentions 'one draft')"),
            LABRubric("r2", "Response mentions 'Sunrise Ventures' or the draft NDA title"),
            LABRubric("r3", "Response does not claim there are 0 drafts"),
            LABRubric("r4", "Response does not claim there are 3 or more drafts"),
        ],
    ),
    LABTask(
        id="query_get_by_type_service_006",
        intent="query",
        instruction="List all Service Agreements.",
        environment=LABEnvironment(seed_agreements=_ALL_SEED),
        expected_output_description=(
            "Two Service Agreements exist: GlobalCorp DevShop (active) and OldCorp (expired). "
            "Both should be returned."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'GlobalCorp' or 'DevShop' service agreement"),
            LABRubric("r2", "Response mentions 'OldCorp' service agreement"),
            LABRubric("r3", "Response does not include NDAs or Employment Agreements as Service Agreements"),
        ],
    ),
    LABTask(
        id="query_no_results_007",
        intent="query",
        instruction="Find all terminated agreements.",
        environment=LABEnvironment(seed_agreements=_ALL_SEED),
        expected_output_description=(
            "No agreements have 'terminated' status in the seeded data. "
            "Response should clearly state no terminated agreements were found."
        ),
        rubrics=[
            LABRubric("r1", "Response indicates no terminated agreements were found"),
            LABRubric("r2", "Response does not list active or draft agreements as terminated"),
            LABRubric("r3", "Response does not fabricate terminated agreement IDs"),
        ],
    ),
    LABTask(
        id="query_filter_employment_008",
        intent="query",
        instruction="Show me all Employment Agreements.",
        environment=LABEnvironment(seed_agreements=_ALL_SEED),
        expected_output_description=(
            "One Employment Agreement exists: Jane Smith at Acme Corp. "
            "Response should return exactly that one."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'Jane Smith' or the employment agreement title"),
            LABRubric("r2", "Response indicates there is one Employment Agreement"),
            LABRubric("r3", "Response does not include NDAs or Service Agreements"),
        ],
    ),
    LABTask(
        id="query_search_party_name_009",
        intent="query",
        instruction="Are there any agreements with Beta Ltd?",
        environment=LABEnvironment(seed_agreements=_ALL_SEED),
        expected_output_description=(
            "Beta Ltd appears as Receiving Party in the Acme-Beta NDA. "
            "Response should confirm the NDA exists."
        ),
        rubrics=[
            LABRubric("r1", "Response confirms there is an agreement with Beta Ltd"),
            LABRubric("r2", "Response mentions the NDA type or 'Acme-Beta' or the title"),
            LABRubric("r3", "Response does not claim Beta Ltd has no agreements"),
        ],
    ),
    LABTask(
        id="query_expired_agreements_010",
        intent="query",
        instruction="List all expired agreements.",
        environment=LABEnvironment(seed_agreements=_ALL_SEED),
        expected_output_description=(
            "One agreement (OldCorp Service Agreement) has expired status. "
            "Response should list just that one."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions 'OldCorp' or the expired service agreement"),
            LABRubric("r2", "Response indicates there is 1 expired agreement"),
            LABRubric("r3", "Response does not list active agreements as expired"),
        ],
    ),
    LABTask(
        id="query_empty_db_011",
        intent="query",
        instruction="List all agreements.",
        environment=LABEnvironment(seed_agreements=[]),
        expected_output_description=(
            "The database is empty. Response should clearly state that no agreements exist."
        ),
        rubrics=[
            LABRubric("r1", "Response indicates the database is empty or no agreements were found"),
            LABRubric("r2", "Response does not fabricate any agreement titles or IDs"),
            LABRubric("r3", "Response does not produce an error — it handles empty state gracefully"),
        ],
    ),
    LABTask(
        id="query_search_content_012",
        intent="query",
        instruction="Search for agreements mentioning 'confidentiality'.",
        environment=LABEnvironment(seed_agreements=_ALL_SEED),
        expected_output_description=(
            "The Acme-Beta NDA content mentions confidentiality. "
            "Response should return that agreement."
        ),
        rubrics=[
            LABRubric("r1", "Response mentions the Acme-Beta NDA or Acme Corp"),
            LABRubric("r2", "Response does not fabricate unrelated agreements as matching"),
        ],
    ),
]
