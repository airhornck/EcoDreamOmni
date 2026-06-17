"""Tests for Agent Fleet — Phase 8 P8-3."""

import pytest

from src.services.agent_fleet import (
    create_fleet,
    get_fleet,
    list_fleets,
    delete_fleet,
    register_instance,
    unregister_instance,
    heartbeat,
    route_task,
    evaluate_scaling,
    list_instances,
    update_instance_status,
    get_fleet_health,
    InstanceStatus,
    RoutingStrategy,
)


class TestAgentFleet:
    def test_create_fleet(self):
        fleet = create_fleet(
            agent_type="content-forge",
            tenant_id="tenant_001",
            min_instances=1,
            max_instances=5,
        )
        assert fleet.fleet_id.startswith("fleet_")
        assert fleet.agent_type == "content-forge"
        assert fleet.tenant_id == "tenant_001"
        assert fleet.max_instances == 5
        assert fleet.routing_strategy == RoutingStrategy.ROUND_ROBIN

    def test_get_fleet(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1")
        fetched = get_fleet(fleet.fleet_id)
        assert fetched is not None
        assert fetched.fleet_id == fleet.fleet_id

    def test_get_fleet_not_found(self):
        assert get_fleet("fleet_nonexistent") is None

    def test_list_fleets(self):
        create_fleet(agent_type="a", tenant_id="t1")
        create_fleet(agent_type="b", tenant_id="t1")
        create_fleet(agent_type="c", tenant_id="t2")
        assert len(list_fleets()) >= 3
        assert len(list_fleets(tenant_id="t1")) >= 2
        assert len(list_fleets(tenant_id="t2")) >= 1

    def test_delete_fleet(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1")
        assert delete_fleet(fleet.fleet_id) is True
        assert get_fleet(fleet.fleet_id) is None
        assert delete_fleet("nonexistent") is False


class TestAgentInstance:
    def test_register_instance(self):
        fleet = create_fleet(agent_type="content-forge", tenant_id="t1", max_instances=3)
        inst = register_instance(fleet.fleet_id, agent_id="cf_001")
        assert inst is not None
        assert inst.instance_id.startswith("inst_")
        assert inst.agent_type == "content-forge"
        assert inst.status == InstanceStatus.HEALTHY

    def test_register_instance_fleet_not_found(self):
        assert register_instance("fleet_bad", agent_id="x") is None

    def test_register_instance_max_reached(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1", max_instances=1)
        register_instance(fleet.fleet_id, agent_id="a")
        with pytest.raises(ValueError, match="已达最大实例数"):
            register_instance(fleet.fleet_id, agent_id="b")

    def test_unregister_instance(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1")
        inst = register_instance(fleet.fleet_id, agent_id="a")
        assert unregister_instance(fleet.fleet_id, inst.instance_id) is True
        assert unregister_instance(fleet.fleet_id, "bad_id") is False

    def test_list_instances(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1")
        register_instance(fleet.fleet_id, agent_id="a")
        register_instance(fleet.fleet_id, agent_id="b")
        assert len(list_instances(fleet.fleet_id)) == 2

    def test_update_instance_status(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1")
        inst = register_instance(fleet.fleet_id, agent_id="a")
        assert update_instance_status(fleet.fleet_id, inst.instance_id, "degraded") is True
        assert update_instance_status(fleet.fleet_id, "bad", "offline") is False

    def test_heartbeat(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1")
        inst = register_instance(fleet.fleet_id, agent_id="a")
        assert heartbeat(fleet.fleet_id, inst.instance_id, cpu_percent=45.0, current_tasks=2) is True
        assert heartbeat("bad", "bad") is False


class TestRouting:
    def test_round_robin_routing(self):
        fleet = create_fleet(
            agent_type="test", tenant_id="t1",
            routing_strategy="round_robin",
        )
        register_instance(fleet.fleet_id, agent_id="a")
        register_instance(fleet.fleet_id, agent_id="b")

        r1 = route_task(fleet.fleet_id)
        r2 = route_task(fleet.fleet_id)
        assert r1 is not None
        assert r2 is not None
        # Round robin should alternate
        assert r1.instance_id != r2.instance_id

    def test_least_load_routing(self):
        fleet = create_fleet(
            agent_type="test", tenant_id="t1",
            routing_strategy="least_load",
        )
        inst1 = register_instance(fleet.fleet_id, agent_id="a")
        inst2 = register_instance(fleet.fleet_id, agent_id="b")
        heartbeat(fleet.fleet_id, inst1.instance_id, current_tasks=3)
        heartbeat(fleet.fleet_id, inst2.instance_id, current_tasks=1)

        routed = route_task(fleet.fleet_id)
        assert routed.instance_id == inst2.instance_id  # less loaded

    def test_capability_match_routing(self):
        fleet = create_fleet(
            agent_type="test", tenant_id="t1",
            routing_strategy="capability_match",
        )
        inst1 = register_instance(fleet.fleet_id, agent_id="a", capabilities=["text", "image"])
        register_instance(fleet.fleet_id, agent_id="b", capabilities=["text"])

        routed = route_task(fleet.fleet_id, required_capabilities=["image"])
        assert routed.instance_id == inst1.instance_id

    def test_route_no_available_instances(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1")
        assert route_task(fleet.fleet_id) is None

    def test_route_busy_instances_skipped(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1")
        inst = register_instance(fleet.fleet_id, agent_id="a", max_tasks=1)
        heartbeat(fleet.fleet_id, inst.instance_id, current_tasks=1)
        assert route_task(fleet.fleet_id) is None


class TestFleetHealth:
    def test_fleet_health(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1")
        register_instance(fleet.fleet_id, agent_id="a")
        register_instance(fleet.fleet_id, agent_id="b")

        health = get_fleet_health(fleet.fleet_id)
        assert health["total_instances"] == 2
        assert health["healthy_count"] == 2
        assert health["fleet_id"] == fleet.fleet_id

    def test_fleet_health_offline(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1")
        inst = register_instance(fleet.fleet_id, agent_id="a")
        update_instance_status(fleet.fleet_id, inst.instance_id, "offline")

        health = get_fleet_health(fleet.fleet_id)
        assert health["offline_count"] == 1
        assert health["healthy_count"] == 0

    def test_get_fleet_health_not_found(self):
        assert get_fleet_health("fleet_bad") is None


class TestAutoScaling:
    def test_evaluate_scaling_maintain(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1", auto_scale_enabled=True)
        register_instance(fleet.fleet_id, agent_id="a")
        result = evaluate_scaling(fleet.fleet_id)
        assert result["recommendation"] in ("maintain", "scale_down")

    def test_evaluate_scaling_scale_up_cpu(self):
        fleet = create_fleet(
            agent_type="test", tenant_id="t1",
            auto_scale_enabled=True,
            max_instances=5,
        )
        inst = register_instance(fleet.fleet_id, agent_id="a")
        heartbeat(fleet.fleet_id, inst.instance_id, cpu_percent=85.0)
        result = evaluate_scaling(fleet.fleet_id)
        assert result["recommendation"] == "scale_up"

    def test_evaluate_scaling_manual(self):
        fleet = create_fleet(agent_type="test", tenant_id="t1", auto_scale_enabled=False)
        result = evaluate_scaling(fleet.fleet_id)
        assert result["recommendation"] == "manual"

    def test_evaluate_scaling_not_found(self):
        result = evaluate_scaling("fleet_bad")
        assert "error" in result
