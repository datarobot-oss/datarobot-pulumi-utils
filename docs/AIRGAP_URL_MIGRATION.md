# Airgapped URL Migration Guide

## Problem

In airgapped on-premise environments, `DATAROBOT_ENDPOINT` is set to an
internal nginx URL (e.g. `http://datarobot-nginx/api/v2`). Recipe repos derive
all `pulumi.export` URLs from this variable, so the printed outputs contain
internal URLs that are unreachable outside the cluster.  Additionally, resource
properties returned directly by the DR API (such as
`CustomApplication.application_url`) also carry the internal hostname.

## Fix (in `datarobot-pulumi-utils`)

Two helpers have been added to `datarobot_pulumi_utils.common`:

| Function | Use for |
|----------|---------|
| `get_datarobot_url()` | Building URLs from scratch (deployment endpoints, playground URLs, etc.) |
| `fix_url(url)` | Fixing URLs that come directly from the DataRobot API (e.g. `application_url`) |

Both are re-exported from `datarobot_pulumi_utils.common`.

`get_datarobot_url()` uses the DataRobot SDK client (`dr.client.get_client()`)
for the `/clientConfig/` call, so no extra auth wiring is needed — it reuses
the same credentials already configured for Pulumi.

### Resolution order for `get_datarobot_url()`

1. `DATAROBOT_WEB_SERVER_URL` env var — explicit override, highest priority.
   The `/api/v2` suffix is appended automatically if absent.
2. `GET /clientConfig/` via SDK → `EXTERNAL_WEB_SERVER_URL` — auto-detected.
   The `/api/v2` suffix is appended automatically.
3. Return `DATAROBOT_ENDPOINT` as-is — it already has the `/api/v2` suffix.

The function returns the **full API endpoint** including `/api/v2`, making it a
direct drop-in for `os.getenv("DATAROBOT_ENDPOINT")`.  For web console/UI URLs
(playgrounds, deployment console pages) strip the suffix:
`get_datarobot_url().removesuffix("/api/v2")`.

---

## How to update a recipe repo

### Step 1 — Bump `datarobot-pulumi-utils` dependency

```toml
# pyproject.toml
[tool.poetry.dependencies]
datarobot-pulumi-utils = ">=X.Y.Z"   # replace with the release version
```

### Step 2 — Update each `infra/infra/agent_*.py`

#### Add the import

```python
from datarobot_pulumi_utils.common import get_datarobot_url
```

#### Replace the inline `datarobot_url` construction

```python
# BEFORE
datarobot_url = (
    os.getenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
    .rstrip("/")
    .rstrip("/api/v2")
)

# AFTER — for API endpoint lambdas
_dr_url = get_datarobot_url()   # includes /api/v2

# For web/console URLs (playground links, deployment console, etc.)
_dr_web_url = _dr_url.removesuffix("/api/v2")
```

#### Replace `os.getenv('DATAROBOT_ENDPOINT')` in deployment endpoint lambdas

Compute `_dr_url` **once** outside the lambda.  Because `get_datarobot_url()`
now includes `/api/v2`, it is a true drop-in for `DATAROBOT_ENDPOINT` — no
need to append `/api/v2` manually:

```python
# BEFORE
agent_deployment_completions_endpoint = agent_agent_deployment.id.apply(
    lambda id: f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}/chat/completions"
)

# AFTER
_dr_url = get_datarobot_url()   # resolved once at Pulumi program start

agent_deployment_completions_endpoint = agent_agent_deployment.id.apply(
    lambda id: f"{_dr_url}/deployments/{id}/chat/completions"
)
```

Substitution table for API endpoint lambdas:

| Before | After |
|--------|-------|
| `f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}"` | `f"{_dr_url}/deployments/{id}"` |
| `f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}/chat/completions"` | `f"{_dr_url}/deployments/{id}/chat/completions"` |
| `f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}/directAccess"` | `f"{_dr_url}/deployments/{id}/directAccess"` |
| `f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}/directAccess/a2a/"` | `f"{_dr_url}/deployments/{id}/directAccess/a2a/"` |
| `f"{os.getenv('DATAROBOT_ENDPOINT')}/genai/agents/fromCustomModel/{id}/chat/"` | `f"{_dr_url}/genai/agents/fromCustomModel/{id}/chat/"` |

For **web/console URLs** (playground links, deployment console, etc.):

```python
_dr_web_url = get_datarobot_url().removesuffix("/api/v2")

playground_url = pulumi.Output.format(
    "{0}/usecases/{1}/playgrounds/{2}/comparison/chats",
    _dr_web_url,   # <-- web URL, no /api/v2
    use_case.id,
    playground.id,
)
```

### Step 3 — Fix API-sourced URLs (e.g. `application_url`)

For properties that come directly from the DataRobot API (not constructed from
`DATAROBOT_ENDPOINT`) use `fix_url` inside `.apply()`:

```python
from datarobot_pulumi_utils.common import fix_url

# BEFORE
pulumi.export("My App URL", my_app.application_url)

# AFTER
pulumi.export("My App URL", my_app.application_url.apply(fix_url))
```

### Step 4 — Add `DATAROBOT_WEB_SERVER_URL` to `.env.template`

```bash
# Optional. Set this to override the auto-detected external URL in airgapped
# environments where DATAROBOT_ENDPOINT is an internal URL.
# When unset, the URL is resolved automatically via /clientConfig/.
# DATAROBOT_WEB_SERVER_URL=https://your-dr-instance.example.com
```

---

## Affected repos (known)

| Repo | Files updated |
|------|--------------|
| `datarobot-pulumi-utils` | `src/.../common/urls.py`, `common/__init__.py` |
| `datarobot-agent-application` | `infra/infra/agent.py`, `mcp_server.py`, `fastapi_server.py`, `configurations/llm/blueprint_with_llm_gateway.py`, `configurations/llm/blueprint_with_external_llm.py` |
| `recipe-talk-to-my-docs` | `infra/infra/agent_retrieval_agent.py` |
| `recipe-datarobot-agent-templates` | `infra/infra/agent_nat.py`, `agent_crewai.py`, `agent_generic_base.py`, `agent_langgraph.py`, `agent_llamaindex.py` |
| `agentic-workflow-builder` | `infra/infra/agent_crewai.py` (and any other agent files) |
| `buzok_experiments` | `_archive/otel/infra/infra/agent_otel.py` (archived) |

To find all other affected repos in the org:
```
org:datarobot os.getenv('DATAROBOT_ENDPOINT') path:infra/infra language:python
```

---

## Verification

After applying changes, run `pulumi up` on the airgapped environment and confirm
that `pulumi.export` outputs show the external URL
(e.g. `https://your-cluster.eks.delivery.drdev.io/api/v2/...`) instead of
`http://datarobot-nginx/api/v2/...`.
