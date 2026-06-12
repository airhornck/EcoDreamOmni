"""ComplianceGuard service: check, batch check, rules list."""

from typing import Dict, List

from src.services.compliance_engine import check_compliance, list_rules


def check_single(text: str, content_id: str = "") -> Dict:
    return check_compliance(text, content_id)


def check_batch(items: List[Dict]) -> List[Dict]:
    """Batch compliance check.

    items: [{"text": str, "content_id": str}, ...]
    """
    results = []
    for item in items:
        result = check_compliance(text=item["text"], content_id=item.get("content_id", ""))
        results.append(result)
    return results


def get_rules() -> List[Dict]:
    return list_rules()
