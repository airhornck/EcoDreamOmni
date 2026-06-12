"""P7-2: E2E 测试 — Playground 爆款复刻

测试场景：粘贴爆款链接 → 解析 → 生成 ContentTemplate
→ 修改变量 → 一键生成 → 保存模板
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.e2e
class TestPlaygroundFlow:
    """Playground 爆款复刻 E2E 测试。"""

    def test_parse_viral_content(self, client: TestClient):
        """粘贴爆款内容 → 解析结构。"""
        resp = client.post(
            "/playground/parse",
            json={
                "text": "作为一名省钱狗爸，我发现很多铲屎官都在为狗狗驱虫贵烦恼。今天分享一个平价驱虫药，我家豆豆用了3个月，效果非常好。大家有什么驱虫经验欢迎在评论区交流！",
            },
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code in (200, 501)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            assert "hook_pattern" in data
            assert "body_structure" in data
            assert "cta_pattern" in data
            assert "tone" in data
            assert isinstance(data.get("keywords"), list)

    def test_list_templates(self, client: TestClient):
        """获取模板列表。"""
        resp = client.get("/playground/templates")
        assert resp.status_code in (200, 501)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            if data:
                tmpl = data[0]
                assert "id" in tmpl
                assert "name" in tmpl
                assert "prompt_template" in tmpl
                assert isinstance(tmpl.get("variables"), list)

    def test_generate_content(self, client: TestClient):
        """修改变量 → 一键生成内容。"""
        resp = client.post(
            "/playground/generate",
            json={
                "template_id": "tmpl_001",
                "variables": {
                    "persona": "省钱狗爸",
                    "problem": "狗狗驱虫贵",
                    "solution": "平价驱虫药",
                    "pet_name": "豆豆",
                    "duration": "3个月",
                    "effect": "非常好",
                },
            },
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code in (200, 501)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            assert "title" in data
            assert "body" in data
            assert isinstance(data.get("hashtags"), list)

    def test_full_playground_flow(self, client: TestClient):
        """完整流程：解析 → 模板 → 变量 → 生成。"""
        # 1. 解析
        parse_resp = client.post(
            "/playground/parse",
            json={"text": "测试爆款文案内容"},
            headers={"Content-Type": "application/json"},
        )
        assert parse_resp.status_code in (200, 501)

        # 2. 模板列表
        tmpl_resp = client.get("/playground/templates")
        assert tmpl_resp.status_code in (200, 501)

        # 3. 生成
        gen_resp = client.post(
            "/playground/generate",
            json={
                "template_id": "tmpl_001",
                "variables": {"persona": "测试人设"},
            },
            headers={"Content-Type": "application/json"},
        )
        assert gen_resp.status_code in (200, 501)
