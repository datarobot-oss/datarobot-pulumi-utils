# Airgapped URL Migration Guide

## Problem

In airgapped on-premise environments, `DATAROBOT_ENDPOINT` is set to an
internal nginx URL (e.g. `http://datarobot-nginx/api/v2`). Recipe repos derive
all `pulumi.export` URLs from this variable, so the printed outputs contain
internal URLs that are unreachable outside the cluster.

## Fix (in `datarobot-pulumi-utils`)

`get_datarobot_url()` has been added to
`datarobot_pulumi_utils.common.urls` (and re-exported from
`datarobot_pulumi_utils.common`).

It resolves the correct external base URL using a 3-tier priority:

1. `DATAROBOT_WEB_SERVER_URL` env var — explicit override, highest priority.
2. `/clientConfig/` API → `EXTERNAL_WEB_SERVER_URL` — auto-detected at
   Pulumi runtime when `DATAROBOT_API_TOKEN` is present.
3. Strip `/api/v2` from `DATAROBOT_ENDPOINT` — existing fallback for standard
   (non-airgapped) environments.

The function also fixes `get_deployment_url()`, which had the same issue.

---

## How to update a recipe repo

### Step 1 — Bump `datarobot-pulumi-utils` dependency

In `pyproject.toml` (or `requirements.txt`), ensure the version constraint
picks up the release that contains `get_datarobot_url()`.

```toml
# pyproject.toml
[tool.poetry.dependencies]
datarobot-pulumi-utils = ">=X.Y.Z"   # replace with the release version
```

### Step 2 — Update each `infra/infra/agent_*.py`

#### 2a. Add the import

At the top of the file, alongside other imports:

```python
from datarobot_pulumi_utils.common import get_datarobot_url
```

#### 2b. Replace the inline `datarobot_url` construction

Find this pattern (repeated in every agent file):

```python
# BEFORE
datarobot_url = (
    os.getenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
    .rstrip("/")
    .rstrip("/api/v2")
)
```

Replace with:

```python
# AFTER
datarobot_url = get_datarobot_url()
```

#### 2c. Replace `os.getenv('DATAROBOT_ENDPOINT')` in deployment endpoint lambdas

Find lambdas that build API endpoint URLs like this:

```python
# BEFORE
agent_deployment_completions_endpoint = agent_deployment.id.apply(
    lambda id: f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}/chat/completions"
)
```

Replace with (capture `get_datarobot_url()` **once** outside the lambda so it
isn't called on every `apply` invocation):

```python
# AFTER
_dr_url = get_datarobot_url()   # resolved once at Pulumi program start

agent_deployment_completions_endpoint = agent_deployment.id.apply(
    lambda id: f"{_dr_url}/api/v2/deployments/{id}/chat/completions"
)
```

> **Note:** `get_datarobot_url()` returns the base URL **without** `/api/v2`.
> You must add `/api/v2` explicitly wherever the lambda previously used
> `os.getenv('DATAROBOT_ENDPOINT')` (which already included it).

All variants follow the same pattern:

| Before | After |
|--------|-------|
| `f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}"` | `f"{_dr_url}/api/v2/deployments/{id}"` |
| `f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}/chat/completions"` | `f"{_dr_url}/api/v2/deployments/{id}/chat/completions"` |
| `f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}/directAccess"` | `f"{_dr_url}/api/v2/deployments/{id}/directAccess"` |
| `f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}/directAccess/a2a/"` | `f"{_dr_url}/api/v2/deployments/{id}/directAccess/a2a/"` |
| `f"{os.getenv('DATAROBOT_ENDPOINT')}/genai/agents/fromCustomModel/{id}/chat/"` | `f"{_dr_url}/api/v2/genai/agents/fromCustomModel/{id}/chat/"` |

### Step 3 — Add `DATAROBOT_WEB_SERVER_URL` to `.env.template`

```bash
# Optional. Set this to override the auto-detected external URL in airgapped
# environments where DATAROBOT_ENDPOINT is an internal URL.
# When unset, the URL is resolved automatically via /clientConfig/.
# DATAROBOT_WEB_SERVER_URL=https://your-dr-instance.example.com
```

---

## Affected repos (known)

| Repo | Files to update |
|------|----------------|
| `recipe-talk-to-my-docs` | `infra/infra/agent_retrieval_agent.py` |
| `recipe-datarobot-agent-templates` | `infra/infra/agent_nat.py`, `agent_crewai.py`, `agent_generic_base.py`, `agent_langgraph.py`, `agent_llamaindex.py` |
| `agentic-workflow-builder` | `infra/infra/agent_crewai.py` (and any other agent files) |
| `buzok_experiments` | `_archive/otel/infra/infra/agent_otel.py` (archived) |

To find all affected repos in the org, run this GitHub code search:
```
org:datarobot os.getenv('DATAROBOT_ENDPOINT') path:infra/infra language:python
```

---

## Verification

After applying changes, run `pulumi up` on the airgapped environment and confirm
that `pulumi.export` outputs show the external URL
(e.g. `https://your-cluster.eks.delivery.drdev.io/api/v2/...`) instead of
`http://datarobot-nginx/api/v2/...`.
