"""Evaluation tasks for the Modifier specialist — updating and deleting agreements."""

import json
from eval.tasks.base import LABEnvironment, LABRubric, LABTask

# Seed agreement used for modify tasks
_NDA_DRAFT = {
    "title": "Acme-Beta Draft NDA",
    "agreement_type": "NDA",
    "parties": json.dumps([
        {"name": "Acme Corp", "role": "Disclosing Party"},
        {"name": "Beta Ltd", "role": "Receiving Party"},
    ]),
    "content": "This NDA governs confidentiality between Acme Corp and Beta Ltd for 2 years.",
    "status": "draft",
}

_SERVICE_ACTIVE = {
    "title": "DevShop Service Agreement",
    "agreement_type": "ServiceAgreement",
    "parties": json.dumps([
        {"name": "ClientCo", "role": "Client"},
        {"name": "DevShop LLC", "role": "Provider"},
    ]),
    "content": "Software development services at $8,000/month.",
    "status": "active",
}

_EMPLOYMENT_ACTIVE = {
    "title": "John Doe Employment Agreement",
    "agreement_type": "Employment",
    "parties": json.dumps([
        {"name": "TechFirm Inc", "role": "Employer"},
        {"name": "John Doe", "role": "Employee"},
    ]),
    "content": "Employment as Software Engineer, $130,000/year.",
    "status": "active",
}

MODIFY_TASKS: list[LABTask] = [
    LABTask(
        id="modify_activate_nda_001",
        intent="modify",
        instruction=(
            "Activate the Acme-Beta Draft NDA — change its status from draft to active."
        ),
        environment=LABEnvironment(seed_agreements=[_NDA_DRAFT]),
        expected_output_description=(
            "Response should confirm the NDA's status was updated to 'active'. "
            "Mentions 'Acme-Beta' or the NDA title."
        ),
        rubrics=[
            LABRubric("r1", "Response confirms the status was changed to 'active'"),
            LABRubric("r2", "Response references the Acme-Beta NDA or the agreement title"),
            LABRubric("r3", "Response does not claim a new agreement was created"),
            LABRubric("r4", "Response does not fabricate unrelated field changes"),
        ],
    ),
    LABTask(
        id="modify_terminate_service_002",
        intent="modify",
        instruction=(
            "Terminate the DevShop Service Agreement — set its status to terminated."
        ),
        environment=LABEnvironment(seed_agreements=[_SERVICE_ACTIVE]),
        expected_output_description=(
            "Response confirms the Service Agreement was updated to 'terminated' status."
        ),
        rubrics=[
            LABRubric("r1", "Response confirms the status was changed to 'terminated'"),
            LABRubric("r2", "Response references 'DevShop' or the Service Agreement title"),
            LABRubric("r3", "Response does not change the agreement type or parties"),
        ],
    ),
    LABTask(
        id="modify_update_content_003",
        intent="modify",
        instruction=(
            "Update the content of the Acme-Beta Draft NDA to add a clause: "
            "'Any dispute shall be resolved through binding arbitration.'"
        ),
        environment=LABEnvironment(seed_agreements=[_NDA_DRAFT]),
        expected_output_description=(
            "Response confirms the NDA content was updated. May mention arbitration clause "
            "or content update. Version should be incremented."
        ),
        rubrics=[
            LABRubric("r1", "Response confirms the agreement content was updated"),
            LABRubric("r2", "Response references the Acme-Beta NDA or arbitration clause"),
            LABRubric("r3", "Response does not delete the agreement instead of updating"),
        ],
    ),
    LABTask(
        id="modify_delete_agreement_004",
        intent="modify",
        instruction=(
            "Delete the Acme-Beta Draft NDA from the system."
        ),
        environment=LABEnvironment(seed_agreements=[_NDA_DRAFT]),
        expected_output_description=(
            "Response confirms the Acme-Beta NDA was deleted. Should indicate success."
        ),
        rubrics=[
            LABRubric("r1", "Response confirms the agreement was deleted"),
            LABRubric("r2", "Response references the Acme-Beta NDA or mentions deletion"),
            LABRubric("r3", "Response does not update status instead of deleting"),
            LABRubric("r4", "Response does not fabricate a deletion of a different agreement"),
        ],
    ),
    LABTask(
        id="modify_update_title_005",
        intent="modify",
        instruction=(
            "Rename the DevShop Service Agreement to 'DevShop LLC Master Service Agreement 2026'."
        ),
        environment=LABEnvironment(seed_agreements=[_SERVICE_ACTIVE]),
        expected_output_description=(
            "Response confirms the title was updated to the new name."
        ),
        rubrics=[
            LABRubric("r1", "Response confirms the title was updated"),
            LABRubric("r2", "Response mentions 'Master Service Agreement 2026' or the new title"),
            LABRubric("r3", "Response does not create a new agreement instead of renaming"),
        ],
    ),
    LABTask(
        id="modify_expire_employment_006",
        intent="modify",
        instruction=(
            "Mark the John Doe Employment Agreement as expired."
        ),
        environment=LABEnvironment(seed_agreements=[_EMPLOYMENT_ACTIVE]),
        expected_output_description=(
            "Response confirms the Employment Agreement's status was changed to 'expired'."
        ),
        rubrics=[
            LABRubric("r1", "Response confirms status changed to 'expired'"),
            LABRubric("r2", "Response references 'John Doe' or the Employment Agreement"),
            LABRubric("r3", "Response does not modify a different agreement"),
        ],
    ),
    LABTask(
        id="modify_nonexistent_007",
        intent="modify",
        instruction=(
            "Update the status of agreement with ID 'nonexistent-id-99999' to active."
        ),
        environment=LABEnvironment(seed_agreements=[_NDA_DRAFT]),
        expected_output_description=(
            "No agreement with that ID exists. Response should indicate the agreement was "
            "not found — it should handle this gracefully without crashing."
        ),
        rubrics=[
            LABRubric("r1", "Response indicates the agreement was not found or does not exist"),
            LABRubric("r2", "Response does not claim successful modification of a nonexistent agreement"),
            LABRubric("r3", "Response does not modify the seeded Acme-Beta NDA instead"),
        ],
    ),
    LABTask(
        id="modify_multiple_fields_008",
        intent="modify",
        instruction=(
            "Update the DevShop Service Agreement: change the status to 'active' and "
            "update the content to reflect a new rate of $12,000/month."
        ),
        environment=LABEnvironment(seed_agreements=[_SERVICE_ACTIVE]),
        expected_output_description=(
            "Response confirms multiple fields were updated: status (if changed) and content "
            "updated to reflect the $12,000 rate."
        ),
        rubrics=[
            LABRubric("r1", "Response confirms the agreement was updated"),
            LABRubric("r2", "Response references 'DevShop' or the Service Agreement"),
            LABRubric("r3", "Response references the rate ($12,000) or content update"),
            LABRubric("r4", "Response does not fabricate a different agreement being modified"),
        ],
    ),
    LABTask(
        id="modify_draft_to_active_employment_009",
        intent="modify",
        instruction=(
            "Activate the John Doe Employment Agreement — move it from its current status to active."
        ),
        environment=LABEnvironment(seed_agreements=[_EMPLOYMENT_ACTIVE]),
        expected_output_description=(
            "Response confirms the Employment Agreement is active (or already active). "
            "Should not fail even if already active."
        ),
        rubrics=[
            LABRubric("r1", "Response confirms status is or was set to 'active'"),
            LABRubric("r2", "Response references 'John Doe' or the Employment Agreement"),
            LABRubric("r3", "Response does not delete the agreement"),
        ],
    ),
    LABTask(
        id="modify_delete_and_verify_010",
        intent="modify",
        instruction=(
            "Remove the DevShop Service Agreement from the system. It's no longer needed."
        ),
        environment=LABEnvironment(seed_agreements=[_SERVICE_ACTIVE]),
        expected_output_description=(
            "Response confirms the DevShop Service Agreement was deleted."
        ),
        rubrics=[
            LABRubric("r1", "Response confirms deletion or removal of the agreement"),
            LABRubric("r2", "Response references 'DevShop' or the Service Agreement"),
            LABRubric("r3", "Response does not update status instead of deleting"),
        ],
    ),
]
