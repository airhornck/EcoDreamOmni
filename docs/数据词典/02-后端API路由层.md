# 后端 API 路由总览

> **自动生成于** 2026-05-28


> **统计**: 52 个路由文件，125 个端点

## RBAC 核心模块（新增 2026-05-31）

- **文件**: `src/core/rbac.py`
- **职责**: 用户角色判断与任务/发布任务权限校验（API 层调用，Service 层不依赖）

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_admin` | `(user: User) -> bool` | `user.role == "admin"` |
| `can_view_task` | `(user: User, task) -> bool` | admin 看全部，其他仅自己 |
| `can_modify_task` | `(user: User, task) -> bool` | admin 改全部，其他仅自己 |
| `can_review_task` | `(user: User, task) -> bool` | admin/reviewer 可审核任何任务，operator 仅自己 |
| `task_list_created_by_filter` | `(user: User) -> Optional[str]` | admin 返回 `None`（无过滤），其他返回 `user.id` |

## admin.py

- **Router Prefix**: `/admin`


| 方法 | 路径 | Handler |
|------|------|---------|
| GET | `/admin/users` | `list_users()` |

## asset_pool.py

- **Router Prefix**: `/assets`


| 方法 | 路径 | Handler |
|------|------|---------|
| GET | `/assets/stats` | `get_asset_statistics()` |
| POST | `/assets/recommend` | `get_recommendations()` |
| POST | `/assets/upload` | `upload_asset()` |
| POST | `/assets/upload-file` | `upload_asset_file()` |
| POST | `/assets/search-stock` | `search_stock()` |
| POST | `/assets/import-stock` | `import_stock()` |
| GET | `/assets` | `get_assets()` |
| GET | `/assets/{asset_id}` | `get_asset_detail()` |
| PATCH | `/assets/{asset_id}` | `patch_asset()` |
| DELETE | `/assets/{asset_id}` | `remove_asset()` |
| GET | `/assets/{asset_id}/download` | `download_asset()` |
| GET | `/assets/{asset_id}/thumbnail` | `download_thumbnail()` |

## auth.py

- **Router Prefix**: `/auth`


| 方法 | 路径 | Handler |
|------|------|---------|
| POST | `/auth/register` | `register()` |
| POST | `/auth/login` | `login()` |
| GET | `/auth/me` | `get_me()` |
| POST | `/auth/mfa/setup` | `mfa_setup()` |
| POST | `/auth/mfa/enable` | `mfa_enable()` |

## brand_knowledge.py

- **Router Prefix**: `/brand-knowledge`


| 方法 | 路径 | Handler |
|------|------|---------|
| GET | `/brand-knowledge/entries` | `list_entries()` |
| POST | `/brand-knowledge/entries` | `create_entry()` |
| GET | `/brand-knowledge/entries/{entry_id}` | `get_entry()` |
| PUT | `/brand-knowledge/entries/{entry_id}` | `update_entry()` |
| DELETE | `/brand-knowledge/entries/{entry_id}` | `delete_entry()` |
| POST | `/brand-knowledge/bulk-import` | `bulk_import_entries()` |

## compliance.py

- **Router Prefix**: `/compliance`


| 方法 | 路径 | Handler |
|------|------|---------|
| POST | `/compliance/check` | `compliance_check()` |
| POST | `/compliance/batch-check` | `compliance_batch_check()` |
| GET | `/compliance/rules` | `compliance_rules()` |

## content_forge.py

- **Router Prefix**: ``


| 方法 | 路径 | Handler |
|------|------|---------|
| POST | `/content-generate` | `generate_content()` |
| POST | `/content-drafts/{draft_id}/submit-for-review` | `submit_for_review()` |

## data_analyst.py

- **Router Prefix**: `/data-analyst`


| 方法 | 路径 | Handler |
|------|------|---------|
| POST | `/data-analyst/reports` | `create_report()` |
| GET | `/data-analyst/engagements` | `list_engagements()` |

## human_in_loop.py

- **Router Prefix**: `/human-in-the-loop`
- **认证依赖**: `get_current_user`（V2.7.4 增补 — 全部端点须注入）
- **数据隔离**: 按 `TaskORM.created_by` 过滤；审核操作使用 `can_review_task`（admin/reviewer 可审核全部）

| 方法 | 路径 | Handler | 认证 | 隔离规则 |
|------|------|---------|------|----------|
| GET | `/human-in-the-loop/pending` | `get_pending_tasks()` | ✅ `get_current_user` | admin/reviewer 看全部；operator 仅 `created_by == user.id` |
| GET | `/human-in-the-loop/tasks/{task_id}` | `get_review_detail()` | ✅ `get_current_user` | 仅可查看自己创建的任务 |
| POST | `/human-in-the-loop/tasks/{task_id}/approve` | `approve_task()` | ✅ `get_current_user` | admin/reviewer 可审核全部；operator 仅自己 |
| POST | `/human-in-the-loop/tasks/{task_id}/reject` | `reject_task()` | ✅ `get_current_user` | admin/reviewer 可审核全部；operator 仅自己 |
| POST | `/human-in-the-loop/tasks/{task_id}/revise` | `revise_task()` | ✅ `get_current_user` | admin/reviewer 可审核全部；operator 仅自己 |
| GET | `/human-in-the-loop/stats` | `get_stats()` | ✅ `get_current_user` | 仅统计自己创建的任务 |
| POST | `/human-in-the-loop/tasks/{task_id}/mark-risk` | `mark_task_risk()` | ✅ `get_current_user` | 仅可操作自己创建的任务 |
| POST | `/human-in-the-loop/batch-approve` | `batch_approve()` | ✅ `get_current_user` | 仅可批量审核自己创建的任务 |

## llm_hub.py

- **Router Prefix**: `/llm-hub`


| 方法 | 路径 | Handler |
|------|------|---------|
| POST | `/llm-hub/models` | `register_model()` |
| GET | `/llm-hub/models` | `list_models()` |
| GET | `/llm-hub/models/{model_id}` | `get_model()` |
| PUT | `/llm-hub/models/{model_id}` | `update_model()` |
| DELETE | `/llm-hub/models/{model_id}` | `delete_model()` |
| POST | `/llm-hub/models/{model_id}/test` | `test_connectivity()` |
| POST | `/llm-hub/scope-configs` | `set_scope_config()` |
| GET | `/llm-hub/scope-configs` | `list_scope_configs()` |
| DELETE | `/llm-hub/scope-configs/{config_id}` | `remove_scope_config()` |
| GET | `/llm-hub/scope-configs/nodes` | `get_node_scope_overview()` |
| POST | `/llm-hub/usage-logs` | `log_usage()` |
| GET | `/llm-hub/usage-logs` | `get_usage_logs()` |
| GET | `/llm-hub/cost-summary` | `get_cost_summary()` |

## persona_story.py

- **Router Prefix**: `/persona-stories`


| 方法 | 路径 | Handler |
|------|------|---------|
| POST | `/persona-stories` | `create_story_route()` |
| GET | `/persona-stories` | `list_stories_route()` |
| GET | `/persona-stories/{story_id}` | `get_story_route()` |
| PUT | `/persona-stories/{story_id}` | `update_story_route()` |
| DELETE | `/persona-stories/{story_id}` | `delete_story_route()` |
| POST | `/persona-stories/{story_id}/clone` | `clone_story_route()` |
| PATCH | `/persona-stories/{story_id}/status` | `update_status_route()` |
| POST | `/persona-stories/{story_id}/nodes` | `create_node_route()` |
| GET | `/persona-stories/{story_id}/nodes` | `list_nodes_route()` |
| POST | `/persona-stories/{story_id}/nodes/reorder` | `reorder_nodes_route()` |
| GET | `/persona-stories/{story_id}/context` | `get_story_context_route()` |
| GET | `/persona-stories/{story_id}/next-node` | `get_next_available_node_route()` |
| PUT | `/persona-stories/story-nodes/{node_id}` | `update_node_route()` |
| DELETE | `/persona-stories/story-nodes/{node_id}` | `delete_node_route()` |
| POST | `/persona-stories/story-nodes/{node_id}/bind-content` | `bind_content_route()` |

## platform_rules.py

- **Router Prefix**: `/platform-rules`


| 方法 | 路径 | Handler |
|------|------|---------|
| GET | `/platform-rules` | `list_rules()` |
| POST | `/platform-rules` | `create_rule()` |
| GET | `/platform-rules/{rule_id}` | `get_rule()` |
| PATCH | `/platform-rules/{rule_id}` | `update_rule()` |
| DELETE | `/platform-rules/{rule_id}` | `delete_rule()` |
| POST | `/platform-rules/evaluate` | `evaluate_content()` |
| GET | `/platform-rules/yaml-platforms` | `list_yaml_platforms()` |
| POST | `/platform-rules/load-yaml` | `load_yaml_rules()` |
| POST | `/platform-rules/seed-compliance-defaults` | `seed_compliance_defaults()` |
| GET | `/platform-rules/attribution/{content_id}` | `get_attribution()` |
| POST | `/platform-rules/douyin/evaluate` | `evaluate_douyin()` |
| POST | `/platform-rules/xiaohongshu/evaluate` | `evaluate_xiaohongshu()` |

## prohibited_words.py

- **Router Prefix**: `/prohibited-words`


| 方法 | 路径 | Handler |
|------|------|---------|
| POST | `/prohibited-words` | `create_word()` |
| GET | `/prohibited-words` | `list_words()` |
| POST | `/prohibited-words/detect` | `detect_words()` |
| POST | `/prohibited-words/seed-defaults` | `seed_defaults()` |
| DELETE | `/prohibited-words/{word_id}` | `delete_word()` |
| POST | `/prohibited-words/guidelines` | `create_guideline()` |
| GET | `/prohibited-words/guidelines` | `list_guidelines()` |

## publisher.py

- **Router Prefix**: `/publish-tasks`
- **认证依赖**: `get_current_user`（V2.7.4 增补）
- **数据隔离**: 按 `PublishTaskORM.created_by` 过滤（V2.7.4 新增字段）

| 方法 | 路径 | Handler | 认证 | 隔离规则 |
|------|------|---------|------|----------|
| POST | `/publish-tasks` | `create_task()` | ✅ `get_current_user` | 自动注入 `created_by = user.id` |
| GET | `/publish-tasks` | `list_tasks()` | ✅ `get_current_user` | admin 看全部；其他仅 `created_by == user.id` |
| GET | `/publish-tasks/{task_id}` | `get_task()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| PUT | `/publish-tasks/{task_id}` | `update_task()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| DELETE | `/publish-tasks/{task_id}` | `delete_task()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/publish-tasks/{task_id}/execute` | `execute_task()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |

## review_publish.py

- **Router Prefix**: `/review-publish-center`
- **认证依赖**: `get_current_user`（V2.7.4 增补 — 全部端点须注入）
- **数据隔离**: 按 `TaskORM.created_by` 过滤；admin 看全部/操作全部，其他仅自己

| 方法 | 路径 | Handler | 认证 | 隔离规则 |
|------|------|---------|------|----------|
| GET | `/review-publish-center/conclusions` | `get_review_conclusions()` | ✅ `get_current_user` | admin 看全部；其他仅 `created_by == user.id` |
| GET | `/review-publish-center/conclusions/{task_id}` | `get_review_conclusion_detail()` | ✅ `get_current_user` | admin 可看全部；其他仅自己 |
| POST | `/review-publish-center/conclusions/{task_id}/confirm-publish` | `confirm_publish()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| PUT | `/review-publish-center/conclusions/{task_id}/content` | `update_review_content()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/review-publish-center/conclusions/{task_id}/regenerate` | `regenerate_content()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |

## task_hub.py

- **Router Prefix**: `/task-hub`
- **认证依赖**: `get_current_user`（V2.7.4 增补 — 全部端点须注入）
- **数据隔离**: 按 `TaskORM.created_by` 过滤；admin 看全部/操作全部，其他仅自己

| 方法 | 路径 | Handler | 认证 | 隔离规则 |
|------|------|---------|------|----------|
| POST | `/task-hub/tasks` | `create_task()` | ✅ `get_current_user` | 自动注入 `created_by = user.id`，覆盖前端传入值 |
| POST | `/task-hub/tasks/with-workflow` | `create_task_with_workflow()` | ✅ `get_current_user` | 自动注入 `created_by = user.id` |
| POST | `/task-hub/tasks/{task_id}/start-workflow` | `start_task_workflow()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| GET | `/task-hub/tasks` | `list_tasks()` | ✅ `get_current_user` | admin 看全部；其他 `WHERE created_by = user.id` |
| GET | `/task-hub/tasks/{task_id}` | `get_task()` | ✅ `get_current_user` | admin 可看全部；其他仅自己 |
| PATCH | `/task-hub/tasks/{task_id}` | `update_task()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己（DRAFT 状态） |
| DELETE | `/task-hub/tasks/{task_id}` | `delete_task()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/tasks/{task_id}/transition` | `transition_task()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/tasks/{task_id}/configure` | `configure()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/tasks/{task_id}/queue` | `queue()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/tasks/{task_id}/start` | `start()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/tasks/{task_id}/pause` | `pause()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/tasks/{task_id}/resume` | `resume()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/tasks/{task_id}/complete` | `complete()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/tasks/{task_id}/fail` | `fail()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/tasks/{task_id}/cancel` | `cancel()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/tasks/{task_id}/retry` | `retry()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/tasks/{task_id}/human-decision` | `human_decision()` | ✅ `get_current_user` | admin 可操作全部；其他仅自己 |
| POST | `/task-hub/batch` | `create_batch()` |
| GET | `/task-hub/batch/{parent_task_id}/progress` | `batch_progress()` |

## timeline.py

- **Router Prefix**: `/timeline`


| 方法 | 路径 | Handler |
|------|------|---------|
| GET | `/timeline/events` | `list_events()` |
| POST | `/timeline/events` | `create_event()` |
| GET | `/timeline/events/{event_id}` | `get_event()` |
| PUT | `/timeline/events/{event_id}` | `update_event()` |
| DELETE | `/timeline/events/{event_id}` | `delete_event()` |

## trend_scout.py

- **Router Prefix**: `/trend-scout`


| 方法 | 路径 | Handler |
|------|------|---------|
| POST | `/trend-scout/reports` | `create_report()` |

## vetdrug.py

- **Router Prefix**: `/vetdrug`


| 方法 | 路径 | Handler |
|------|------|---------|
| GET | `/vetdrug/drugs` | `list_drugs()` |
| POST | `/vetdrug/drugs` | `create_drug()` |
| GET | `/vetdrug/drugs/{drug_id}` | `get_drug()` |
| PUT | `/vetdrug/drugs/{drug_id}` | `update_drug()` |
| DELETE | `/vetdrug/drugs/{drug_id}` | `delete_drug()` |
| POST | `/vetdrug/validate-claim` | `validate_claim()` |
| POST | `/vetdrug/bulk-import` | `bulk_import_drugs()` |
| GET | `/vetdrug/expiry-warnings` | `get_expiry_warnings()` |
