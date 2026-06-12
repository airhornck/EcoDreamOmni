"""
W6 ComplianceGuard Red-Green tests.
Tests for L1/L2/L3 rule engine, jieba segmentation, evidence chain, and audit log.
"""

from src.models.user import clear_users
from src.services.auth_service import register_user



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    email = f"cg_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"cguser_{uuid.uuid4().hex[:8]}",
        "role": role,
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# ─── L1 Hard Redlines ───


def test_l1_blocks_prescription_drugs():
    """Red: L1 must block prescription drug mentions."""
    from src.services.compliance_engine import check_compliance

    result = check_compliance("可以给猫咪用阿莫西林治疗感冒，效果很好")
    assert result["level"] == "reject"
    assert any(r["rule_id"].startswith("L1") for r in result["violations"])
    assert any("处方" in r["category"] for r in result["violations"])


def test_l1_blocks_medical_promises():
    """Red: L1 must block medical treatment promises."""
    from src.services.compliance_engine import check_compliance

    result = check_compliance("用了这个产品，三天治愈猫癣，无效退款")
    assert result["level"] == "reject"
    assert any(r["rule_id"].startswith("L1") for r in result["violations"])
    assert any("诊疗承诺" in r["category"] for r in result["violations"])


def test_l1_allows_general_care_tips():
    """Red: General care tips should pass L1."""
    from src.services.compliance_engine import check_compliance

    result = check_compliance("春天到了，记得给猫咪勤梳毛，保持环境清洁")
    assert result["level"] in ("pass", "warning")
    assert len(result["violations"]) == 0


# ─── L2 Commercial Disclosure ───


def test_l2_warns_unlabeled_commercial_content():
    """Red: L2 should warn on commercial content without disclosure."""
    from src.services.compliance_engine import check_compliance

    result = check_compliance("这款猫粮真的太棒了，我家猫吃了毛发变得超亮，大家快去下单！链接在评论区")
    # Should at least have a warning, possibly reject if L1 also triggered
    l2_violations = [r for r in result["violations"] if r["rule_id"].startswith("L2")]
    assert len(l2_violations) > 0
    assert any("标注" in r["category"] or "商业" in r["category"] for r in l2_violations)


# ─── L3 Risk Disclaimer ───


def test_l3_suggests_professional_consultation():
    """Red: L3 should suggest adding professional consultation disclaimer."""
    from src.services.compliance_engine import check_compliance

    result = check_compliance("如果你的猫出现呕吐腹泻，可能是肠胃炎，建议禁食观察")
    l3_violations = [r for r in result["violations"] if r["rule_id"].startswith("L3")]
    # MVP: symptom mention triggers L3 suggestion
    assert any("专业" in r["suggestion"] or "咨询" in r["suggestion"] or "兽医" in r["suggestion"]
               for r in l3_violations) or result["suggestions"]


# ─── Evidence Chain ───


def test_evidence_chain_is_recorded():
    """Red: Compliance check should record evidence with timestamp."""
    from src.services.compliance_engine import check_compliance

    result = check_compliance("可以给猫咪用人用的布洛芬止痛")
    assert "evidence_id" in result
    assert "checked_at" in result
    assert result["level"] == "reject"


# ─── Compliance Audit ───


def test_compliance_audit_recorded_for_l1_l2():
    """Red: L1 intercept / L2 warning must write compliance_audit record."""
    from src.services.compliance_engine import (
        check_compliance,
        clear_evidence,
        list_compliance_audit,
    )

    clear_evidence()
    result = check_compliance("用阿莫西林三天治愈猫癣，快去下单！", content_id="audit_test_001")
    assert result["level"] == "reject"

    audits = list_compliance_audit(content_id="audit_test_001")
    l1_audits = [a for a in audits if a["layer"] == "L1"]
    l2_audits = [a for a in audits if a["layer"] == "L2"]

    # L1 should have audit records
    assert len(l1_audits) >= 1
    for a in l1_audits:
        assert a["content_id"] == "audit_test_001"
        assert a["rule_id"].startswith("L1")
        assert a["snippet_hash"]
        assert a["created_at"]
        assert a["superseded_by"] is None

    # L2 should have audit record
    assert len(l2_audits) >= 1
    for a in l2_audits:
        assert a["content_id"] == "audit_test_001"
        assert a["rule_id"].startswith("L2")
        assert a["payload_ref"] == result["evidence_id"]


def test_compliance_audit_immutable():
    """Red: Audit records should be append-only; corrections via superseded_by."""
    from src.services.compliance_engine import (
        check_compliance,
        clear_evidence,
        list_compliance_audit,
        supersede_audit,
    )

    clear_evidence()
    check_compliance("用阿莫西林", content_id="audit_immutable_001")
    audits = list_compliance_audit(content_id="audit_immutable_001")
    assert len(audits) >= 1
    original = audits[0]

    corrected = supersede_audit(original["audit_id"])
    assert corrected is not None
    assert corrected["audit_id"] != original["audit_id"]
    assert corrected["superseded_by"] is None

    # Original should now point to the new record
    updated_audits = list_compliance_audit(content_id="audit_immutable_001")
    original_updated = [a for a in updated_audits if a["audit_id"] == original["audit_id"]][0]
    assert original_updated["superseded_by"] == corrected["audit_id"]


# ─── API Endpoints ───


def test_compliance_check_endpoint(client):
    """Red API should accept text and return compliance result."""
    token = get_auth_token(client)
    response = client.post(
        "/compliance/check",
        json={"text": "三天治愈猫癣，保证有效", "content_id": "draft_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "level" in data
    assert data["level"] == "reject"
    assert "violations" in data


def test_compliance_check_requires_auth(client):
    response = client.post("/compliance/check", json={"text": "test"})
    assert response.status_code == 401


def test_compliance_batch_check(client):
    """Red API should support batch checking multiple texts."""
    token = get_auth_token(client)
    response = client.post(
        "/compliance/batch-check",
        json={
            "items": [
                {"text": "春天记得给猫梳毛", "content_id": "c1"},
                {"text": "用阿莫西林治疗猫感冒", "content_id": "c2"},
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 2
    levels = {r["content_id"]: r["level"] for r in data["results"]}
    assert levels["c1"] in ("pass", "warning")
    assert levels["c2"] == "reject"


def test_compliance_rules_list(client):
    """Red API should list active compliance rules."""
    token = get_auth_token(client)
    response = client.get("/compliance/rules", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    assert len(data["rules"]) > 0
    rule_levels = {r["level"] for r in data["rules"]}
    assert rule_levels == {"L1", "L2", "L3"}
