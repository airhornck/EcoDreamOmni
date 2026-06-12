# EcoDreamOmni 后端 API 路由梳理

> 基于 `apps/backend/src/api/` 目录下全部 52 个 `.py` 文件自动提取

## account_pool.py
- **Router Prefix**: `/account-pool`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_pool_account()` | create pool account | get_current_user |
| GET | `/` | `list_pool_accounts()` | list pool accounts | get_current_user |
| GET | `/{entry_id}` | `get_pool_account_detail()` | get pool account detail | get_current_user |
| PATCH | `/{entry_id}` | `update_pool_account()` | update pool account | get_current_user |
| DELETE | `/{entry_id}` | `delete_pool_account()` | delete pool account | get_current_user |
| GET | `/{entry_id}/browser-config` | `get_browser_context_config()` | get browser context config | get_current_user |
| PATCH | `/{entry_id}/status` | `update_account_status()` | update account status | get_current_user |
| PATCH | `/{entry_id}/persona` | `update_account_persona()` | update account persona | get_current_user |

## admin.py
- **Router Prefix**: `/admin`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/users` | `list_users()` | list users | get_db, require_role |

## agent_cockpit.py
- **Router Prefix**: `/agent-cockpit`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/dashboard` | `dashboard()` | dashboard | 无 |
| GET | `/agents/{agent_id}` | `agent_overview()` | agent overview | 无 |
| GET | `/alerts/summary` | `alert_summary()` | alert summary | 无 |
| GET | `/activity` | `recent_activity()` | recent activity | 无 |
| POST | `/agents/{agent_id}/health-check` | `health_check()` | health check | 无 |

## agent_hub.py
- **Router Prefix**: `/agent-hub`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/agents` | `register_agent()` | register agent | 无 |
| GET | `/agents` | `list_agents()` | list agents | 无 |
| GET | `/agents/{agent_id}` | `get_agent()` | get agent | 无 |
| PATCH | `/agents/{agent_id}` | `update_agent()` | update agent | 无 |
| DELETE | `/agents/{agent_id}` | `deregister_agent()` | deregister agent | 无 |
| POST | `/agents/{agent_id}/configs` | `create_config()` | create config | 无 |
| GET | `/agents/{agent_id}/configs` | `list_configs()` | list configs | 无 |
| GET | `/agents/{agent_id}/configs/{version}` | `get_config()` | get config | 无 |
| POST | `/agents/{agent_id}/configs/{version}/activate` | `activate_config()` | activate config | 无 |
| POST | `/agents/{agent_id}/configs/{version}/rollback` | `rollback_config()` | rollback config | 无 |
| GET | `/agents/{agent_id}/dependencies` | `list_dependencies()` | list dependencies | 无 |
| POST | `/agents/{agent_id}/dependencies` | `declare_dependency()` | declare dependency | 无 |
| POST | `/agents/{agent_id}/health-check` | `health_check()` | health check | 无 |
| GET | `/agents/{agent_id}/permissions` | `list_permissions()` | list permissions | 无 |
| POST | `/agents/{agent_id}/permissions` | `grant_permission()` | grant permission | 无 |

## agent_metrics.py
- **Router Prefix**: `/agent-metrics`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/tasks` | `record_task()` | record task | 无 |
| GET | `/tasks` | `list_tasks()` | list tasks | 无 |
| GET | `/agents/{agent_id}` | `agent_metrics()` | agent metrics | 无 |
| GET | `/overall` | `overall_metrics()` | overall metrics | 无 |
| POST | `/tasks/{task_id}/score` | `submit_score()` | submit score | 无 |
| GET | `/cost/by-agent` | `cost_by_agent()` | cost by agent | 无 |
| GET | `/cost/by-content` | `cost_by_content()` | cost by content | 无 |

## agent_orchestra.py
- **Router Prefix**: `(无)`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/agents` | `create_agent()` | create agent | get_current_user |
| GET | `/agents` | `list_agents()` | list agents | get_current_user |
| GET | `/agents/{agent_id}` | `get_agent()` | get agent | get_current_user |
| POST | `/agents/{agent_id}/skills` | `bind_skill()` | bind skill | get_current_user |
| PUT | `/agents/{agent_id}` | `update_agent()` | update agent | get_current_user |
| DELETE | `/agents/{agent_id}` | `delete_agent()` | delete agent | get_current_user |
| POST | `/workflows` | `create_workflow()` | create workflow | get_current_user |
| GET | `/workflows` | `list_workflows()` | list workflows | get_current_user |
| GET | `/workflows/{workflow_id}` | `get_workflow()` | get workflow | get_current_user |
| POST | `/pipelines` | `create_pipeline()` | create pipeline | get_current_user |
| GET | `/pipelines` | `list_pipelines()` | list pipelines | get_current_user |
| GET | `/pipelines/{pipeline_id}` | `get_pipeline()` | get pipeline | get_current_user |

## agent_watch.py
- **Router Prefix**: `/agent-watch`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/heartbeat` | `heartbeat()` | heartbeat | 无 |
| GET | `/agents/{agent_id}/status` | `agent_status()` | agent status | 无 |
| GET | `/dashboard` | `dashboard()` | dashboard | 无 |
| POST | `/traces` | `start_trace()` | start trace | 无 |
| POST | `/traces/{trace_id}/finish` | `finish_trace()` | finish trace | 无 |
| POST | `/traces/{trace_id}/spans` | `record_span()` | record span | 无 |
| GET | `/traces` | `list_traces()` | list traces | 无 |
| GET | `/traces/{trace_id}` | `get_trace()` | get trace | 无 |
| GET | `/alerts` | `list_alerts()` | list alerts | 无 |
| PATCH | `/alerts/{alert_id}/ack` | `ack_alert()` | ack alert | 无 |
| POST | `/alerts/{alert_id}/resolve` | `resolve_alert()` | resolve alert | 无 |
| POST | `/detect/loop` | `detect_loop()` | detect loop | 无 |
| POST | `/detect/timeout` | `detect_timeout()` | detect timeout | 无 |

## api_platform.py
- **Router Prefix**: `/api-platform`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/keys` | `create_key()` | create key | require_tenant |
| GET | `/keys` | `list_keys()` | list keys | require_tenant |
| DELETE | `/keys/{key_id}` | `revoke_key()` | revoke key | 无 |
| POST | `/webhooks` | `register_webhook()` | register webhook | require_tenant |
| GET | `/webhooks` | `list_webhooks()` | list webhooks | require_tenant |
| DELETE | `/webhooks/{webhook_id}` | `delete_webhook()` | delete webhook | 无 |
| GET | `/rate-limit` | `rate_limit_status()` | rate limit status | require_tenant |

## asset_pool.py
- **Router Prefix**: `/assets`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/stats` | `get_asset_statistics()` | get asset statistics | get_current_user, get_db |
| POST | `/recommend` | `get_recommendations()` | get recommendations | get_current_user, get_db |
| POST | `/upload` | `upload_asset()` | upload asset | get_current_user, get_db |
| POST | `/upload-file` | `upload_asset_file()` | upload asset file | get_current_user, get_db |
| POST | `/search-stock` | `search_stock()` | search stock | get_current_user |
| POST | `/import-stock` | `import_stock()` | import stock | get_current_user, get_db |
| GET | `/` | `get_assets()` | get assets | get_current_user, get_db |
| GET | `/{asset_id}` | `get_asset_detail()` | get asset detail | get_current_user, get_db |
| PATCH | `/{asset_id}` | `patch_asset()` | patch asset | get_current_user, get_db |
| DELETE | `/{asset_id}` | `remove_asset()` | remove asset | get_current_user, get_db |
| GET | `/{asset_id}/download` | `download_asset()` | download asset | get_current_user, get_db |
| GET | `/{asset_id}/thumbnail` | `download_thumbnail()` | download thumbnail | get_current_user, get_db |

## audit.py
- **Router Prefix**: `/audit`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/logs` | `query_logs()` | query logs | 无 |
| POST | `/logs` | `log_event()` | log event | 无 |
| GET | `/stats` | `audit_stats()` | audit stats | 无 |

## auth.py
- **Router Prefix**: `/auth`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/register` | `register()` | register | get_db |
| POST | `/login` | `login()` | login | get_db |
| GET | `/me` | `get_me()` | get me | get_current_user |
| POST | `/mfa/setup` | `mfa_setup()` | mfa setup | get_current_user, get_db |
| POST | `/mfa/enable` | `mfa_enable()` | mfa enable | get_current_user, get_db |

## brand_knowledge.py
- **Router Prefix**: `/brand-knowledge`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/entries` | `list_entries()` | list entries | get_current_user, get_db |
| POST | `/entries` | `create_entry()` | create entry | get_current_user, get_db |
| GET | `/entries/{entry_id}` | `get_entry()` | get entry | get_current_user, get_db |
| PUT | `/entries/{entry_id}` | `update_entry()` | update entry | get_current_user, get_db |
| DELETE | `/entries/{entry_id}` | `delete_entry()` | delete entry | get_current_user, get_db |
| POST | `/bulk-import` | `bulk_import_entries()` | bulk import entries | get_current_user, get_db |

## comment_hub.py
- **Router Prefix**: `/comments`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/{content_id}/replies/suggest` | `suggest_reply_route()` | suggest reply route | get_current_user |
| POST | `/replies/{reply_id}/submit` | `submit_reply_route()` | submit reply route | get_current_user |
| POST | `/replies/{reply_id}/approve` | `approve_reply_route()` | approve reply route | get_current_user |
| POST | `/replies/{reply_id}/reject` | `reject_reply_route()` | reject reply route | get_current_user |
| GET | `/pending-review` | `list_pending_replies_route()` | list pending replies route | get_current_user |
| GET | `/account/{account_id}/stats` | `get_account_stats_route()` | get account stats route | get_current_user |

## compliance.py
- **Router Prefix**: `/compliance`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/check` | `compliance_check()` | compliance check | get_current_user, get_db |
| POST | `/batch-check` | `compliance_batch_check()` | compliance batch check | get_current_user, get_db |
| GET | `/rules` | `compliance_rules()` | compliance rules | get_current_user, get_db |
| GET | `/stats` | `get_compliance_stats()` | get compliance stats | get_current_user |
| GET | `/history` | `get_compliance_history()` | get compliance history | get_current_user |
| DELETE | `/history` | `clear_compliance_history()` | clear compliance history | get_current_user |

## content_forge.py
- **Router Prefix**: `(无)`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/content-drafts` | `create_draft()` | create draft | get_current_user |
| GET | `/content-drafts` | `list_drafts()` | list drafts | get_current_user |
| GET | `/content-drafts/{draft_id}` | `get_draft()` | get draft | get_current_user |
| PATCH | `/content-drafts/{draft_id}` | `update_draft()` | update draft | get_current_user |
| DELETE | `/content-drafts/{draft_id}` | `delete_draft()` | delete draft | get_current_user |
| POST | `/content-generate` | `generate_content()` | generate content | get_current_user, get_db |
| POST | `/content-drafts/{draft_id}/submit-for-review` | `submit_for_review()` | submit for review | get_current_user, get_db |

## content_insight.py
- **Router Prefix**: `/content-insight`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/analyze` | `analyze_content()` | analyze content | 无 |
| POST | `/tags/extract` | `extract_tags()` | extract tags | 无 |
| POST | `/tags/compare` | `compare_tags()` | compare tags | 无 |
| GET | `/recommendations` | `get_recommendations()` | get recommendations | 无 |

## content_series.py
- **Router Prefix**: `/content-series`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_series_route()` | create series route | get_current_user |
| GET | `/` | `list_series_route()` | list series route | get_current_user |
| GET | `/{series_id}` | `get_series_route()` | get series route | get_current_user |
| POST | `/{series_id}/contents` | `add_content_to_series_route()` | add content to series route | get_current_user |
| GET | `/{series_id}/context` | `get_series_context_route()` | get series context route | get_current_user |
| POST | `/engagement-check` | `engagement_check_route()` | engagement check route | get_current_user |

## cron_hub.py
- **Router Prefix**: `/cron-hub`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/jobs` | `create_job()` | create job | 无 |
| GET | `/jobs` | `list_jobs()` | list jobs | 无 |
| GET | `/jobs/{job_id}` | `get_job()` | get job | 无 |
| PATCH | `/jobs/{job_id}` | `update_job()` | update job | 无 |
| DELETE | `/jobs/{job_id}` | `delete_job()` | delete job | 无 |
| POST | `/jobs/{job_id}/execute` | `execute_job()` | execute job | 无 |
| POST | `/jobs/{job_id}/dry-run` | `dry_run_job()` | dry run job | 无 |
| GET | `/executions` | `list_executions()` | list executions | 无 |
| POST | `/executions/{execution_id}/complete` | `complete_execution()` | complete execution | 无 |
| POST | `/executions/{execution_id}/retry` | `retry_execution()` | retry execution | 无 |
| GET | `/dlq` | `list_dlq()` | list dlq | 无 |
| POST | `/dlq/{dlq_id}/review` | `review_dlq()` | review dlq | 无 |
| POST | `/dlq/{dlq_id}/retry` | `retry_dlq()` | retry dlq | 无 |
| DELETE | `/dlq/{dlq_id}` | `delete_dlq()` | delete dlq | 无 |
| POST | `/validate-cron` | `validate_cron()` | validate cron | 无 |

## dashboard.py
- **Router Prefix**: `/dashboard`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/overview` | `overview()` | overview | get_current_user |
| GET | `/quick-actions` | `quick_actions()` | quick actions | get_current_user |
| GET | `/alerts` | `alerts()` | alerts | get_current_user |
| GET | `/activity-log` | `activity_log()` | activity log | get_current_user |
| GET | `/core-metrics` | `core_metrics()` | core metrics | get_current_user |

## data_analyst.py
- **Router Prefix**: `/data-analyst`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/reports` | `create_report()` | create report | get_current_user |
| GET | `/reports/{report_id}` | `get_report()` | get report | get_current_user |
| GET | `/dashboard` | `get_dashboard()` | get dashboard | get_current_user |
| GET | `/attribution/{content_id}` | `get_attribution()` | get attribution | get_current_user |
| POST | `/calibrate` | `create_calibration()` | create calibration | get_current_user |
| GET | `/calibration-check` | `calibration_check()` | calibration check | get_current_user |
| GET | `/publish-trend` | `get_publish_trend()` | get publish trend | get_current_user |
| GET | `/platform-distribution` | `get_platform_distribution()` | get platform distribution | get_current_user |
| GET | `/engagement-distribution` | `get_engagement_distribution()` | get engagement distribution | get_current_user |
| GET | `/mape-trend` | `get_mape_trend()` | get mape trend | get_current_user |
| GET | `/content-ranking` | `get_content_ranking()` | get content ranking | get_current_user |
| GET | `/account-comparison` | `get_account_comparison()` | get account comparison | get_current_user |
| GET | `/calibration-status` | `get_calibration_status()` | get calibration status | get_current_user |
| GET | `/import-history` | `get_import_history()` | get import history | get_current_user |
| GET | `/engagement-trend` | `get_engagement_trend()` | get engagement trend | get_current_user |

## harness.py
- **Router Prefix**: `/harness`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/sessions` | `create_session()` | create session | 无 |
| GET | `/sessions` | `list_sessions()` | list sessions | 无 |
| GET | `/sessions/{session_id}` | `get_session()` | get session | 无 |
| POST | `/sessions/{session_id}/step` | `run_step()` | run step | 无 |
| POST | `/sessions/{session_id}/run` | `run_session()` | run session | 无 |
| POST | `/sessions/{session_id}/pause` | `pause_session()` | pause session | 无 |
| POST | `/sessions/{session_id}/resume` | `resume_session()` | resume session | 无 |
| GET | `/sessions/{session_id}/summary` | `get_session_summary()` | get session summary | 无 |
| POST | `/subagents` | `create_subagent()` | create subagent | 无 |
| GET | `/subagents` | `list_subagents()` | list subagents | 无 |
| POST | `/subagents/{subagent_id}/step` | `run_subagent_step()` | run subagent step | 无 |
| POST | `/subagents/{subagent_id}/run` | `run_subagent_to_completion()` | run subagent to completion | 无 |
| GET | `/plans` | `list_plans()` | list plans | 无 |
| GET | `/plans/{plan_id}` | `get_plan()` | get plan | 无 |
| POST | `/plans/{plan_id}/pause` | `pause_plan()` | pause plan | 无 |
| POST | `/plans/{plan_id}/resume` | `resume_plan()` | resume plan | 无 |
| POST | `/plans/{plan_id}/cancel` | `cancel_plan()` | cancel plan | 无 |
| GET | `/checkpoints/{session_id}` | `list_checkpoints()` | list checkpoints | 无 |
| POST | `/checkpoints/{session_id}/rollback` | `rollback_checkpoint()` | rollback checkpoint | 无 |
| GET | `/context/{session_id}` | `get_context()` | get context | 无 |
| POST | `/context/{session_id}/add` | `add_context_message()` | add context message | 无 |
| GET | `/context/{session_id}/stats` | `get_context_stats()` | get context stats | 无 |
| GET | `/tools` | `list_tools()` | list tools | 无 |
| GET | `/tools/{tool_id}` | `get_tool()` | get tool | 无 |

## human_in_loop.py
- **Router Prefix**: `/human-in-the-loop`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/pending` | `get_pending_tasks()` | get pending tasks | get_db |
| GET | `/tasks/{task_id}` | `get_review_detail()` | get review detail | get_db |
| POST | `/tasks/{task_id}/approve` | `approve_task()` | approve task | get_db |
| POST | `/tasks/{task_id}/reject` | `reject_task()` | reject task | get_db |
| POST | `/tasks/{task_id}/revise` | `revise_task()` | revise task | get_db |
| GET | `/history` | `get_history()` | get history | 无 |
| GET | `/stats` | `get_stats()` | get stats | get_db |
| POST | `/detect-risk` | `detect_risk()` | detect risk | 无 |
| POST | `/tasks/{task_id}/mark-risk` | `mark_task_risk()` | mark task risk | get_db |
| POST | `/batch-approve` | `batch_approve()` | batch approve | get_db |

## image_forge.py
- **Router Prefix**: `/image-configs`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_config()` | create config | get_current_user |
| GET | `/` | `list_configs()` | list configs | get_current_user |
| GET | `/{config_id}` | `get_config()` | get config | get_current_user |
| PATCH | `/{config_id}/layout` | `update_layout()` | update layout | get_current_user |
| GET | `/{config_id}/recommendations` | `get_recommendations()` | get recommendations | get_current_user |
| POST | `/{config_id}/t2-check` | `run_t2_check()` | run t2 check | get_current_user |
| POST | `/{config_id}/submit` | `submit()` | submit | get_current_user |
| POST | `/{config_id}/approve` | `approve()` | approve | get_current_user |
| POST | `/{config_id}/reject` | `reject()` | reject | get_current_user |

## ip_reputation.py
- **Router Prefix**: `/ip-reputation`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/register` | `register_ip()` | register ip | 无 |
| GET | `/` | `list_ips()` | list ips | 无 |
| GET | `/{ip_id}` | `get_ip()` | get ip | 无 |
| PATCH | `/{ip_id}` | `update_ip()` | update ip | 无 |
| DELETE | `/{ip_id}` | `delete_ip()` | delete ip | 无 |
| POST | `/{ip_id}/anomaly` | `report_anomaly()` | report anomaly | 无 |
| POST | `/{ip_id}/evaluate` | `evaluate_trial()` | evaluate trial | 无 |
| GET | `/{ip_id}/circuit` | `check_circuit()` | check circuit | 无 |
| POST | `/{ip_id}/recover` | `manual_recover()` | manual recover | 无 |
| POST | `/{ip_id}/bind` | `bind_account()` | bind account | 无 |
| POST | `/{ip_id}/unbind` | `unbind_account()` | unbind account | 无 |
| POST | `/switch` | `switch_ip()` | switch ip | 无 |
| GET | `/switch-logs` | `list_switch_logs()` | list switch logs | 无 |
| GET | `/recommend` | `recommend_ip()` | recommend ip | 无 |

## llm_hub.py
- **Router Prefix**: `/llm-hub`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/models` | `register_model()` | register model | get_current_user, get_db |
| GET | `/models` | `list_models()` | list models | get_current_user, get_db |
| GET | `/models/{model_id}` | `get_model()` | get model | get_current_user, get_db |
| PUT | `/models/{model_id}` | `update_model()` | update model | get_current_user, get_db |
| DELETE | `/models/{model_id}` | `delete_model()` | delete model | get_current_user, get_db |
| POST | `/models/{model_id}/test` | `test_connectivity()` | test connectivity | get_current_user, get_db |
| POST | `/scope-configs` | `set_scope_config()` | set scope config | get_current_user, get_db |
| GET | `/scope-configs` | `list_scope_configs()` | list scope configs | get_current_user, get_db |
| DELETE | `/scope-configs/{config_id}` | `remove_scope_config()` | remove scope config | get_current_user, get_db |
| GET | `/scope-configs/nodes` | `get_node_scope_overview()` | get node scope overview | get_current_user, get_db |
| POST | `/usage-logs` | `log_usage()` | log usage | get_current_user, get_db |
| GET | `/usage-logs` | `get_usage_logs()` | get usage logs | get_current_user, get_db |
| GET | `/cost-summary` | `get_cost_summary()` | get cost summary | get_current_user, get_db |

## matrix_ops.py
- **Router Prefix**: `/matrix`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/groups` | `create_group()` | create group | 无 |
| GET | `/groups` | `list_groups()` | list groups | 无 |
| GET | `/groups/{group_id}` | `get_group()` | get group | 无 |
| DELETE | `/groups/{group_id}` | `delete_group()` | delete group | 无 |
| POST | `/groups/auto` | `auto_group()` | auto group | 无 |
| POST | `/assignments` | `assign_brief()` | assign brief | 无 |
| GET | `/assignments` | `list_assignments()` | list assignments | 无 |
| POST | `/schedules` | `create_schedule()` | create schedule | 无 |
| GET | `/schedules` | `list_schedules()` | list schedules | 无 |
| GET | `/groups/{group_id}/health` | `group_health()` | group health | 无 |

## methodology.py
- **Router Prefix**: `/methodologies`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/` | `list_methodologies()` | list methodologies | get_current_user |
| GET | `/{framework_id}/stages` | `list_stages_by_framework()` | list stages by framework | get_current_user |
| GET | `/stages` | `list_stages()` | list stages | get_current_user |
| GET | `/stages/{stage_id}/template` | `get_stage_template()` | get stage template | get_current_user |
| GET | `/stages/{stage_id}` | `get_stage()` | get stage | get_current_user |
| POST | `/stages/{stage_id}/evaluate` | `evaluate_content()` | evaluate content | get_current_user |
| GET | `/stages/{stage_id}/audience` | `get_stage_audience_segments()` | get stage audience segments | get_current_user |
| GET | `/stages/{stage_id}/personas` | `get_stage_persona_recommendations()` | get stage persona recommendations | get_current_user |
| GET | `/aipl/{aipl_stage}/to-5a` | `map_aipl_to_5a()` | map aipl to 5a | get_current_user |
| GET | `/5a/{five_a_stage}/to-aipl` | `map_5a_to_aipl()` | map 5a to aipl | get_current_user |

## metrics.py
- **Router Prefix**: `(无)`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/metrics` | `prometheus_metrics()` | prometheus metrics | 无 |
| GET | `/health/detailed` | `detailed_health()` | detailed health | 无 |

## orchestrator.py
- **Router Prefix**: `/orchestrator`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/groups/{group_id}/schedule` | `schedule_group()` | schedule group | 无 |
| GET | `/shards` | `list_shards()` | list shards | 无 |
| POST | `/shards/{shard_id}/execute` | `execute_shard()` | execute shard | 无 |
| GET | `/groups/{group_id}/health` | `group_health()` | group health | 无 |

## persona_pool.py
- **Router Prefix**: `/personas`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_persona()` | create persona | get_current_user |
| GET | `/` | `list_personas()` | list personas | get_current_user |
| GET | `/{persona_id}` | `get_persona()` | get persona | get_current_user |
| PATCH | `/{persona_id}` | `update_persona()` | update persona | get_current_user |
| POST | `/clone` | `clone_persona()` | clone persona | get_current_user |
| DELETE | `/{persona_id}` | `delete_persona()` | delete persona | get_current_user |
| POST | `/match` | `match_personas()` | match personas | get_current_user |

## persona_story.py
- **Router Prefix**: `/persona-stories`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_story_route()` | create story route | get_current_user, get_db |
| GET | `/` | `list_stories_route()` | list stories route | get_current_user, get_db |
| GET | `/{story_id}` | `get_story_route()` | get story route | get_current_user, get_db |
| PUT | `/{story_id}` | `update_story_route()` | update story route | get_current_user, get_db |
| DELETE | `/{story_id}` | `delete_story_route()` | delete story route | get_current_user, get_db |
| POST | `/{story_id}/clone` | `clone_story_route()` | clone story route | get_current_user, get_db |
| PATCH | `/{story_id}/status` | `update_status_route()` | update status route | get_current_user, get_db |
| POST | `/{story_id}/nodes` | `create_node_route()` | create node route | get_current_user, get_db |
| GET | `/{story_id}/nodes` | `list_nodes_route()` | list nodes route | get_current_user, get_db |
| POST | `/{story_id}/nodes/reorder` | `reorder_nodes_route()` | reorder nodes route | get_current_user, get_db |
| GET | `/{story_id}/context` | `get_story_context_route()` | get story context route | get_current_user, get_db |
| GET | `/{story_id}/next-node` | `get_next_available_node_route()` | get next available node route | get_current_user, get_db |
| PUT | `/story-nodes/{node_id}` | `update_node_route()` | update node route | get_current_user, get_db |
| DELETE | `/story-nodes/{node_id}` | `delete_node_route()` | delete node route | get_current_user, get_db |
| POST | `/story-nodes/{node_id}/bind-content` | `bind_content_route()` | bind content route | get_current_user, get_db |

## pipeline.py
- **Router Prefix**: `/pipeline`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/tasks` | `submit_task()` | submit task | get_current_user |
| GET | `/tasks/{task_id}` | `get_task_status()` | get task status | get_current_user |
| GET | `/tasks` | `list_tasks()` | list tasks | get_current_user |
| POST | `/tasks/{task_id}/cancel` | `cancel_task()` | cancel task | get_current_user |

## platform_account.py
- **Router Prefix**: `/platform-accounts`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_platform_account()` | create platform account | get_current_user |
| GET | `/` | `list_platform_accounts()` | list platform accounts | get_current_user |
| GET | `/{pa_id}` | `get_platform_account_detail()` | get platform account detail | get_current_user |
| PATCH | `/{pa_id}` | `update_platform_account()` | update platform account | get_current_user |
| DELETE | `/{pa_id}` | `delete_platform_account()` | delete platform account | get_current_user |
| GET | `/{pa_id}/session-status` | `session_status()` | session status | get_current_user |
| POST | `/qr-login/start` | `qr_login_start()` | qr login start | get_current_user |
| GET | `/qr-login/poll` | `qr_login_poll()` | qr login poll | get_current_user |

## platform_adapters.py
- **Router Prefix**: `/platform-adapters`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/platforms` | `list_platforms()` | list platforms | 无 |
| GET | `/specs` | `get_all_specs()` | get all specs | 无 |
| GET | `/{platform}/spec` | `get_platform_spec()` | get platform spec | 无 |
| POST | `/{platform}/format` | `format_content()` | format content | 无 |
| POST | `/{platform}/validate` | `validate_payload()` | validate payload | 无 |

## platform_rules.py
- **Router Prefix**: `/platform-rules`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/` | `list_rules()` | list rules | get_current_user, get_db |
| POST | `/` | `create_rule()` | create rule | get_current_user, get_db |
| GET | `/{rule_id}` | `get_rule()` | get rule | get_current_user, get_db |
| PATCH | `/{rule_id}` | `update_rule()` | update rule | get_current_user, get_db |
| DELETE | `/{rule_id}` | `delete_rule()` | delete rule | get_current_user, get_db |
| POST | `/evaluate` | `evaluate_content()` | evaluate content | get_current_user, get_db |
| GET | `/yaml-platforms` | `list_yaml_platforms()` | list yaml platforms | get_current_user |
| POST | `/load-yaml` | `load_yaml_rules()` | load yaml rules | get_current_user, get_db |
| POST | `/seed-compliance-defaults` | `seed_compliance_defaults()` | seed compliance defaults | get_current_user, get_db |
| GET | `/attribution/{content_id}` | `get_attribution()` | get attribution | get_current_user, get_db |
| POST | `/douyin/evaluate` | `evaluate_douyin()` | evaluate douyin | get_current_user |
| POST | `/xiaohongshu/evaluate` | `evaluate_xiaohongshu()` | evaluate xiaohongshu | get_current_user, get_db |

## pool_predictor.py
- **Router Prefix**: `/predictions`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_prediction_endpoint()` | create prediction endpoint | get_current_user |
| GET | `/hit-rate` | `get_hit_rate()` | get hit rate | get_current_user |
| POST | `/batch` | `batch_prediction_endpoint()` | batch prediction endpoint | get_current_user |
| POST | `/train` | `train_model_endpoint()` | train model endpoint | get_current_user |
| GET | `/model/metrics` | `get_model_metrics_endpoint()` | get model metrics endpoint | get_current_user |
| GET | `/stats` | `get_prediction_stats()` | get prediction stats | get_current_user |
| GET | `/accuracy` | `get_prediction_accuracy()` | get prediction accuracy | get_current_user |
| GET | `/{prediction_id}` | `get_prediction_endpoint()` | get prediction endpoint | get_current_user |

## pool_predictor_explore.py
- **Router Prefix**: `/pool-predictor/explore`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/train` | `train_exploration()` | train exploration | 无 |
| POST | `/predict` | `predict_with_model()` | predict with model | 无 |
| GET | `/compare` | `compare_models()` | compare models | 无 |
| POST | `/ab-assign` | `ab_assign()` | ab assign | 无 |
| POST | `/feedback` | `record_feedback()` | record feedback | 无 |

## prohibited_words.py
- **Router Prefix**: `/prohibited-words`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_word()` | create word | get_current_user, get_db |
| GET | `/` | `list_words()` | list words | get_current_user, get_db |
| POST | `/detect` | `detect_words()` | detect words | get_current_user, get_db |
| POST | `/seed-defaults` | `seed_defaults()` | seed defaults | get_current_user, get_db |
| DELETE | `/{word_id}` | `delete_word()` | delete word | get_current_user, get_db |
| POST | `/guidelines` | `create_guideline()` | create guideline | get_current_user, get_db |
| GET | `/guidelines` | `list_guidelines()` | list guidelines | get_current_user, get_db |

## prompt_registry.py
- **Router Prefix**: `/prompt-registry`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/variables` | `register_variable()` | register variable | 无 |
| GET | `/variables` | `list_variables()` | list variables | 无 |
| DELETE | `/variables/{name}` | `delete_variable()` | delete variable | 无 |
| POST | `/templates` | `create_template()` | create template | 无 |
| GET | `/templates` | `list_templates()` | list templates | 无 |
| GET | `/templates/{template_id}` | `get_template()` | get template | 无 |
| POST | `/templates/{template_id}/versions` | `create_template_version()` | create template version | 无 |
| POST | `/templates/{template_id}/activate` | `activate_template()` | activate template | 无 |
| POST | `/templates/{template_id}/archive` | `archive_template()` | archive template | 无 |
| DELETE | `/templates/{template_id}` | `delete_template()` | delete template | 无 |
| POST | `/templates/{template_id}/render` | `render_template()` | render template | 无 |
| GET | `/templates/{template_id}/performance` | `get_performance()` | get performance | 无 |

## proxy.py
- **Router Prefix**: `/proxies`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_proxy_entry()` | create proxy entry | get_current_user |
| GET | `/` | `list_proxy_entries()` | list proxy entries | get_current_user |
| GET | `/active` | `list_active_proxies()` | list active proxies | get_current_user |
| GET | `/{entry_id}` | `get_proxy_entry()` | get proxy entry | get_current_user |
| PATCH | `/{entry_id}` | `update_proxy_entry()` | update proxy entry | get_current_user |
| DELETE | `/{entry_id}` | `delete_proxy_entry()` | delete proxy entry | get_current_user |
| POST | `/health-check` | `health_check_proxy()` | health check proxy | get_current_user |
| POST | `/{entry_id}/test` | `test_proxy_entry()` | test proxy entry | get_current_user |

## publisher.py
- **Router Prefix**: `/publish-tasks`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_task()` | create task | get_current_user |
| GET | `/` | `list_tasks()` | list tasks | get_current_user |
| GET | `/{task_id}` | `get_task()` | get task | get_current_user |
| PATCH | `/{task_id}` | `update_task()` | update task | get_current_user |
| DELETE | `/{task_id}` | `delete_task()` | delete task | get_current_user |
| POST | `/{task_id}/execute` | `execute_task()` | execute task | get_current_user |

## review_publish.py
- **Router Prefix**: `/review-publish-center`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/conclusions` | `get_review_conclusions()` | get review conclusions | get_db |
| GET | `/conclusions/{task_id}` | `get_review_conclusion_detail()` | get review conclusion detail | get_db |
| POST | `/conclusions/{task_id}/confirm-publish` | `confirm_publish()` | confirm publish | get_db |
| PUT | `/conclusions/{task_id}/content` | `update_review_content()` | update review content | get_db |
| POST | `/conclusions/{task_id}/regenerate` | `regenerate_content()` | regenerate content | get_db |

## skill_hub.py
- **Router Prefix**: `(无)`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_skill()` | create skill | get_current_user |
| GET | `/` | `list_skills()` | list skills | get_current_user |
| GET | `/{skill_id}` | `get_skill()` | get skill | get_current_user |
| PATCH | `/{skill_id}` | `update_skill()` | update skill | get_current_user |
| DELETE | `/{skill_id}` | `delete_skill()` | delete skill | get_current_user |
| GET | `/resolve/all` | `resolve_all_skills()` | resolve all skills | get_current_user |
| GET | `/resolve/agent/{agent_id}` | `resolve_agent_skills()` | resolve agent skills | get_current_user |
| GET | `/{skill_id}/dependencies` | `check_dependencies()` | check dependencies | get_current_user |
| GET | `/tools/registry` | `list_tool_registry()` | list tool registry | get_current_user |
| GET | `/tools/registry/{skill_id}` | `get_tool_schema()` | get tool schema | get_current_user |
| POST | `/import/hermes` | `import_hermes_skill()` | import hermes skill | get_current_user |
| POST | `/{skill_id}/execute` | `execute_skill()` | execute skill | get_current_user |

## skill_smith.py
- **Router Prefix**: `/skill-smith`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/record-performance` | `record_performance()` | record performance | get_current_user |
| GET | `/opportunities/{skill_id}` | `get_opportunities()` | get opportunities | get_current_user |
| POST | `/evolve/{skill_id}` | `evolve_skill()` | evolve skill | get_current_user |
| GET | `/triggers` | `list_triggers()` | list triggers | get_current_user |

## task_hub.py
- **Router Prefix**: `/task-hub`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/tasks` | `create_task()` | create task | get_db |
| POST | `/tasks/with-workflow` | `create_task_with_workflow()` | create task with workflow | get_db |
| POST | `/tasks/{task_id}/start-workflow` | `start_task_workflow()` | start task workflow | get_db |
| GET | `/tasks` | `list_tasks()` | list tasks | get_db |
| GET | `/tasks/{task_id}` | `get_task()` | get task | get_db |
| PATCH | `/tasks/{task_id}` | `update_task()` | update task | get_db |
| DELETE | `/tasks/{task_id}` | `delete_task()` | delete task | get_db |
| POST | `/tasks/{task_id}/transition` | `transition_task()` | transition task | get_db |
| POST | `/tasks/{task_id}/configure` | `configure()` | configure | get_db |
| POST | `/tasks/{task_id}/queue` | `queue()` | queue | get_db |
| POST | `/tasks/{task_id}/start` | `start()` | start | get_db |
| POST | `/tasks/{task_id}/pause` | `pause()` | pause | get_db |
| POST | `/tasks/{task_id}/resume` | `resume()` | resume | get_db |
| POST | `/tasks/{task_id}/complete` | `complete()` | complete | get_db |
| POST | `/tasks/{task_id}/fail` | `fail()` | fail | get_db |
| POST | `/tasks/{task_id}/cancel` | `cancel()` | cancel | get_db |
| POST | `/tasks/{task_id}/retry` | `retry()` | retry | get_db |
| POST | `/tasks/{task_id}/human-decision` | `human_decision()` | human decision | get_db |
| POST | `/batch` | `create_batch()` | create batch | get_db |
| GET | `/batch/{parent_task_id}/progress` | `batch_progress()` | batch progress | get_db |

## tenants.py
- **Router Prefix**: `/tenants`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_tenant()` | create tenant | 无 |
| GET | `/` | `list_tenants()` | list tenants | 无 |
| GET | `/{tenant_id}` | `get_tenant()` | get tenant | 无 |
| PATCH | `/{tenant_id}` | `update_tenant()` | update tenant | 无 |
| DELETE | `/{tenant_id}` | `delete_tenant()` | delete tenant | 无 |
| GET | `/{tenant_id}/config` | `get_tenant_config()` | get tenant config | 无 |
| PATCH | `/{tenant_id}/config` | `update_tenant_config()` | update tenant config | 无 |
| GET | `/context/whoami` | `whoami()` | whoami | 无 |

## timeline.py
- **Router Prefix**: `/timeline`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/events` | `list_events()` | list events | get_current_user, get_db |
| POST | `/events` | `create_event()` | create event | get_current_user, get_db |
| GET | `/events/{event_id}` | `get_event()` | get event | get_current_user, get_db |
| PUT | `/events/{event_id}` | `update_event()` | update event | get_current_user, get_db |
| DELETE | `/events/{event_id}` | `delete_event()` | delete event | get_current_user, get_db |

## trend_scout.py
- **Router Prefix**: `/trend-scout`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/reports` | `create_report()` | create report | get_current_user, get_db |
| GET | `/reports` | `list_reports()` | list reports | get_current_user |
| GET | `/reports/{report_id}` | `get_report()` | get report | get_current_user |
| POST | `/persona-draft` | `create_persona_draft()` | create persona draft | get_current_user |
| POST | `/reports/{report_id}/generate-pdf` | `generate_report_pdf()` | generate report pdf | get_current_user |
| GET | `/reports/{report_id}/preview` | `preview_report()` | preview report | get_current_user |
| GET | `/reports/{report_id}/download` | `download_report()` | download report | get_current_user |
| POST | `/reports/batch` | `batch_create_reports()` | batch create reports | get_current_user |
| GET | `/topics` | `list_topics()` | list topics | get_current_user |
| PATCH | `/topics/{topic_id}` | `update_topic_status()` | update topic status | get_current_user |
| DELETE | `/topics/{topic_id}` | `delete_topic()` | delete topic | get_current_user |
| POST | `/topics` | `create_topic()` | create topic | get_current_user |
| GET | `/hot-keywords` | `get_hot_keywords()` | get hot keywords | get_current_user |
| GET | `/stats` | `get_stats()` | get stats | get_current_user |

## vetdrug.py
- **Router Prefix**: `/vetdrug`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| GET | `/drugs` | `list_drugs()` | list drugs | get_current_user, get_db |
| POST | `/drugs` | `create_drug()` | create drug | get_current_user, get_db |
| GET | `/drugs/{drug_id}` | `get_drug()` | get drug | get_current_user, get_db |
| PUT | `/drugs/{drug_id}` | `update_drug()` | update drug | get_current_user, get_db |
| DELETE | `/drugs/{drug_id}` | `delete_drug()` | delete drug | get_current_user, get_db |
| POST | `/validate-claim` | `validate_claim()` | validate claim | get_current_user, get_db |
| POST | `/bulk-import` | `bulk_import_drugs()` | bulk import drugs | get_current_user, get_db |
| GET | `/expiry-warnings` | `get_expiry_warnings()` | get expiry warnings | get_current_user, get_db |

## websocket.py
- **Router Prefix**: `(无)`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| WEBSOCKET | `/ws/alerts` | `alert_websocket()` | alert websocket | 无 |
| GET | `/api/alerts` | `list_alerts_api()` | list alerts api | get_current_user |
| POST | `/api/alerts` | `create_alert_api()` | create alert api | get_current_user |

## workflow_engine.py
- **Router Prefix**: `/workflow-engine`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/templates` | `create_template()` | create template | 无 |
| GET | `/templates` | `list_templates()` | list templates | 无 |
| GET | `/templates/{template_id}` | `get_template()` | get template | 无 |
| PATCH | `/templates/{template_id}` | `update_template()` | update template | 无 |
| DELETE | `/templates/{template_id}` | `delete_template()` | delete template | 无 |
| POST | `/templates/{template_id}/executions` | `start_execution()` | start execution | 无 |
| GET | `/executions` | `list_executions()` | list executions | 无 |
| GET | `/executions/{execution_id}` | `get_execution()` | get execution | 无 |
| POST | `/executions/{execution_id}/next` | `execute_next_node()` | execute next node | 无 |
| POST | `/executions/{execution_id}/pause` | `pause_execution()` | pause execution | 无 |
| POST | `/executions/{execution_id}/resume` | `resume_execution()` | resume execution | 无 |
| POST | `/executions/{execution_id}/cancel` | `cancel_execution()` | cancel execution | 无 |
| GET | `/executions/{execution_id}/nodes` | `get_node_executions()` | get node executions | 无 |
| GET | `/executions/{execution_id}/context` | `get_context()` | get context | 无 |

## workflows.py
- **Router Prefix**: `/workflow-visual`

| 方法 | 路径 | Handler | 简要描述 | 特殊依赖 |
|------|------|---------|----------|----------|
| POST | `/` | `create_template()` | create template | get_current_user |
| GET | `/` | `list_templates()` | list templates | get_current_user |
| GET | `/{template_id}` | `get_template()` | get template | get_current_user |
| POST | `/{template_id}/upgrade-version` | `upgrade_version()` | upgrade version | get_current_user |
| GET | `/{template_id}/versions` | `get_versions()` | get versions | get_current_user |
| POST | `/{template_id}/dry-run` | `dry_run()` | dry run | get_current_user |
| GET | `/{template_id}/react-flow` | `react_flow()` | react flow | get_current_user |

