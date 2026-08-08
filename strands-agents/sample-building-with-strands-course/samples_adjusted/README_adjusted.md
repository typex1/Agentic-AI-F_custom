# Adjusted Samples — Limited Permissions (amazon.nova-lite-v1:0 only)

This folder contains copies of every example in `samples/`, adjusted to run in an
environment where the IAM role only permits:

- `bedrock-runtime`: `Converse`, `ConverseStream`, `InvokeModel`, `InvokeModelWithResponseStream`
- Region: **us-east-1**
- Model: **amazon.nova-lite-v1:0** only (the `us.` inference profile is denied)

Every script below was executed and verified on 2026-08-03 with strands-agents 1.45.0,
strands-agents-tools 0.8.2, and strands-agents-evals 1.0.1.

**Result: 42 files adjusted — 35 runnable scripts (34 working, 1 not working) + 7 shared helpers.**

## Common Adjustment

All agents, judges, simulators, and summarizers now use:

```python
from strands.models import BedrockModel
model = BedrockModel(model_id="amazon.nova-lite-v1:0", region_name="us-east-1")
```

The explicit `region_name` is required because `AWS_REGION` is not set in this
environment (the strands default region would be wrong).

## Adjusted Scripts by Folder

### 01-agent-loop (3 scripts — all working)
| Script | Adjustment |
|--------|------------|
| `simple_agent.py` | Default model → nova-lite |
| `agent_with_tools.py` | Default model → nova-lite |
| `agent_with_defaults.py` | Claude Sonnet → nova-lite |

### 02-model-providers (1 script — working)
| Script | Adjustment |
|--------|------------|
| `model_providers.py` | Bedrock/nova-lite made the active provider; Anthropic/OpenAI/Ollama imports and models commented out (packages not installed, no API keys / local server) |

### 03-mcp-tools (4 scripts — all working)
| Script | Adjustment |
|--------|------------|
| `mcp_coding_agent.py` | Default model → nova-lite |
| `mcp_http.py` | Default model → nova-lite |
| `tool_executor.py` | Default model → nova-lite |
| `tool_filtering.py` | Default model → nova-lite |

### 04-callbacks-streaming (3 scripts — all working)
| Script | Adjustment |
|--------|------------|
| `callbacks_streaming.py` | Shared `MODEL` constant for all 3 agents |
| `async_streaming.py` | Default model → nova-lite |
| `fastapi_streaming.py` | Default model → nova-lite (`fastapi` installed via pip; verified with uvicorn + curl) |

### 05-hooks (2 scripts — all working)
| Script | Adjustment |
|--------|------------|
| `rate_limiter.py` | Default model → nova-lite |
| `approval_interrupt.py` | Default model → nova-lite (interrupt/approval flow verified end to end) |

### 06-plugins-skills (1 script — working)
| Script | Adjustment |
|--------|------------|
| `customer_service.py` | Default model → nova-lite |

### 07-steering (2 files — working)
| Script | Adjustment |
|--------|------------|
| `customer_service_steering.py` | Default model → nova-lite |
| `steering_handlers.py` (helper) | **Nova Lite workaround:** the framework's `LLMSteeringHandler` uses a structured-output model named `_LLMSteering`; Nova Lite drops the leading underscore when emitting the tool call, causing an infinite "tool not found" loop. Added an underscore-free `SteeringDecision` model and a `steer_before_tool` override. |

### 08-conversation-management (6 files — all working)
| Script | Adjustment |
|--------|------------|
| `sliding_window.py` | Default model → nova-lite |
| `summarizing.py` | Default model → nova-lite |
| `custom_summarizer.py` | Main agent → nova-lite; summarizer Claude Haiku → nova-lite |
| `context_manager_auto.py` | Default model → nova-lite |
| `context_manager_agentic.py` | Default model → nova-lite |
| `steering_handlers.py` (helper) | Same Nova Lite workaround as 07 |

### 09-persistent-memory (3 files — 1 working, 1 NOT working)
| Script | Adjustment |
|--------|------------|
| `file_session_manager.py` | Default model → nova-lite; removed `conversation_manager="auto"` (not supported by strands-agents 1.45.0 — the string form belongs to `context_manager` and caused an `AttributeError`) |
| `s3_session_manager_not_working.py` | **NOT WORKING:** requires an S3 bucket, but the IAM role denies `s3:CreateBucket` and `s3:PutObject` (verified). Model and `conversation_manager` fixes applied for reference. |
| `steering_handlers.py` (helper) | Same Nova Lite workaround as 07 |

### 10-agents-as-tools (1 script — working)
| Script | Adjustment |
|--------|------------|
| `agent_as_tool.py` | Orchestrator (Claude Opus) and specialist (Claude Sonnet) → both nova-lite |

### 11-graphs (2 scripts — all working)
| Script | Adjustment |
|--------|------------|
| `basic_graph.py` | Shared `MODEL` constant for all 4 graph-node agents |
| `workflow.py` | Shared `MODEL` constant for all 4 agents |

### 12-swarms (2 scripts — all working)
| Script | Adjustment |
|--------|------------|
| `debugging_swarm.py` | Shared `MODEL` constant for all 4 swarm agents |
| `mixed_patterns.py` | Shared `MODEL` constant for all 4 agents |

### 13-evals (8 files — all working)
The strands-evals default judge model is `global.anthropic.claude-sonnet-4-6`
(not accessible), so every evaluator/simulator/generator needs an explicit model.
The samples were also written for a newer strands-evals API than the installed 1.0.1.

| Script | Adjustment |
|--------|------------|
| `basic_eval.py` | Agent + `OutputEvaluator` judge → nova-lite; `run_evaluations` returns a single report in 1.0.1 (`reports[0]` → `report`) |
| `custom_evaluator.py` | Agent → nova-lite; custom evaluator needs `super().__init__()` in 1.0.1; report fix |
| `trajectory_eval.py` | Agents + `TrajectoryEvaluator` judge → nova-lite; trajectory passed as tool **names** only (Nova Lite cannot serialize complex nested trajectories into the judge's scorer tools — caused `ValidationException` loops and 0.0 scores); report fix |
| `experiment_generator.py` | Generator model → nova-lite; renamed the generator's internal `_Case` structured-output model (same Nova Lite underscore bug as 07) — without this, 0 cases are generated |
| `simulator_eval.py` | Simulator + judges → nova-lite; monkeypatched `ActorSimulator._generate_profile_from_case`, which hardcodes a default (Claude) agent in the library; report fix. Note: takes ~10 minutes to run. |
| `customer_service_eval.py` | Agent + both judges → nova-lite; trajectory names fix; report fix |
| `create_agent.py` (helper) | nova-lite; removed `conversation_manager="auto"` |
| `steering_handlers.py` (helper) | Same Nova Lite workaround as 07 |

Tip: the eval reports use an interactive display — press `q` to exit.

### 14-deploy (4 files — all working locally)
Actual cloud deployment (`agentcore deploy` / `sam deploy`) is not possible with
these permissions, but both apps run and serve requests locally
(`bedrock-agentcore` and `mangum` installed via pip).

| Script | Adjustment |
|--------|------------|
| `main.py` | nova-lite; removed `conversation_manager="auto"`. Note: port 8080 is occupied in this IDE — run with `python3 -c "import main; main.app.run(port=8081)"` |
| `lambda-deployment/lambda_handler.py` | nova-lite. Test locally with `uvicorn lambda_handler:app --port 8766` |
| `steering_handlers.py` (helper) | Same Nova Lite workaround as 07 |
| `lambda-deployment/steering_handlers.py` (helper) | Same Nova Lite workaround as 07 |

## Key Findings

1. **Only the plain model ID works.** `amazon.nova-lite-v1:0` is allowed;
   `us.amazon.nova-lite-v1:0` (inference profile) is denied.
2. **Nova Lite drops leading underscores in structured-output tool names.**
   This breaks any framework code using `_`-prefixed pydantic models for
   structured output (`_LLMSteering` in steering, `_Case` in the experiment
   generator). Workaround: underscore-free model names.
3. **Nova Lite struggles with complex tool inputs.** Passing deeply nested
   dict/list structures as judge scorer-tool arguments produces malformed
   toolUse JSON (`ValidationException`). Workaround: simplify inputs (e.g.,
   tool-name lists instead of full call records).
4. **Version mismatches** between the samples and the installed packages
   (`conversation_manager="auto"`, single vs. list `EvaluationReport`,
   `Evaluator.__init__`) needed small code fixes independent of permissions.
5. **No S3 access** — the only sample that cannot work is the S3 session manager.
