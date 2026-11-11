"""Synthetic qualifying metadata for testing loader gates, never a real audit."""
from forgely_training import (COPILOT_SELECTOR_VERSION,policy_payload_digest,
                              selector_code_digest,selector_runtime_digest)


def qualifying_selector_audit(policy):
    return dict(selector_version=COPILOT_SELECTOR_VERSION,source='simulation',real_observations=0,
        policy_payload_sha256=policy_payload_digest(policy),selector_code_sha256=selector_code_digest(),
        selector_runtime_sha256=selector_runtime_digest(),evaluation=policy['evaluation'])
