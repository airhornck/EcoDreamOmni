"""Tests for AgentHub v4.0 Phase 2 P2-4 enhancements."""


from src.services import agent_hub as ah


class TestConfigWorkbenchFields:
    def test_create_config_with_ui_fields(self):
        agent = ah.register_agent("TestAgent", "writer")
        config = ah.create_config(
            agent_id=agent.id,
            env="dev",
            config_payload={"model": "gpt-4"},
            ui_config={"theme": "dark", "layout": "sidebar"},
            quick_actions=[{"label": "快速发布", "action": "publish"}],
            adaptive_config={"temperature": 0.7},
        )
        assert config is not None
        assert config.ui_config == {"theme": "dark", "layout": "sidebar"}
        assert config.quick_actions == [{"label": "快速发布", "action": "publish"}]
        assert config.adaptive_config == {"temperature": 0.7}

    def test_get_workbench_config(self):
        agent = ah.register_agent("TestAgent2", "writer")
        ah.create_config(
            agent_id=agent.id,
            env="dev",
            config_payload={"model": "gpt-4"},
            ui_config={"theme": "light"},
            quick_actions=[{"label": "生成文案", "action": "draft"}],
        )
        ah.activate_config(agent.id, 1)

        wb = ah.get_workbench_config(agent.id)
        assert wb is not None
        assert wb["agent_name"] == "TestAgent2"
        assert wb["ui_config"] == {"theme": "light"}
        assert len(wb["quick_actions"]) == 1
        assert wb["config_version"] == 1

    def test_get_workbench_config_no_active_config(self):
        agent = ah.register_agent("TestAgent3", "writer")
        wb = ah.get_workbench_config(agent.id)
        assert wb is None


class TestConfigHotReload:
    def test_config_update_callback(self):
        events = []

        def on_update(agent_id, config):
            events.append((agent_id, config.version))

        ah.on_config_update(on_update)

        agent = ah.register_agent("TestAgent4", "writer")
        ah.create_config(agent.id, "dev", {"model": "gpt-4"})
        ah.activate_config(agent.id, 1)

        assert len(events) == 1
        assert events[0] == (agent.id, 1)

        # Clean up callback to avoid side effects
        ah._config_update_callbacks.remove(on_update)
