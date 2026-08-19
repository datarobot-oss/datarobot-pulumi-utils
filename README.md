<div align="center">
  <h1>DataRobot Pulumi Utils</h1>
</div>
<div align="center">
  <a href="https://pypi.python.org/pypi/datarobot-pulumi-utils"><img src="https://img.shields.io/pypi/v/datarobot-pulumi-utils.svg" alt="PyPI"></a>
  <a href="https://github.com/datarobot-oss/datarobot-pulumi-utils"><img src="https://img.shields.io/pypi/pyversions/datarobot-pulumi-utils.svg" alt="versions"></a>
  <a href="https://github.com/datarobot-oss/datarobot-pulumi-utils/blob/main/LICENSE"><img src="https://img.shields.io/github/license/datarobot-oss/datarobot-pulumi-utils.svg?v" alt="license"></a>
</div>

---

`datarobot-pulumi-utils` is a Python helper library for provisioning DataRobot
resources with [Pulumi](https://www.pulumi.com/). It builds on the official
[`pulumi-datarobot`](https://www.pulumi.com/registry/packages/datarobot/)
provider and adds typed configuration models, custom resources for operations
the provider does not cover, and small runtime helpers.

It is the shared foundation that DataRobot Application Templates use to define
their `infra/` Pulumi programs.

## How it fits together

DataRobot's infrastructure-as-code stack has three layers, each building on the
one below it:

```
terraform-provider-datarobot   Terraform provider (Go); defines DataRobot resources
          |
          |  bridged into a Pulumi provider by the Pulumi Terraform Bridge
          v
pulumi-datarobot               Pulumi provider; manage those resources from Python
          |
          |  extended with config schemas, extra resources, and helpers by
          v
datarobot-pulumi-utils         this repo
```

1. [`terraform-provider-datarobot`](https://github.com/datarobot-community/terraform-provider-datarobot)
   is the underlying Terraform provider. It defines the DataRobot resources and
   data sources.
2. [`pulumi-datarobot`](https://github.com/datarobot-community/pulumi-datarobot)
   bridges that Terraform provider into a Pulumi provider via the
   [Pulumi Terraform Bridge](https://github.com/pulumi/pulumi-terraform-bridge),
   exposing the same resources to Python (and Node.js, Go, and .NET).
3. `datarobot-pulumi-utils` (this repo) builds on `pulumi-datarobot`, adding the
   pieces below.

A practical consequence: if a DataRobot resource is missing or misbehaving, the
fix usually belongs in whichever layer owns it. New resource coverage comes from
the Terraform provider (surfaced through the Pulumi provider), while the
higher-level config models and gap-filling resources live here.

## What's in the box

### `datarobot_pulumi_utils.schema`

Pydantic models that give you typed, validated configuration for DataRobot
concepts: LLMs, guardrails, vector databases, custom models, applications,
datasets, data connections, execution environments, predictions, and training.
Use them to describe DataRobot config in one place instead of passing around
loose dictionaries.

```python
from datarobot_pulumi_utils.schema.exec_envs import RuntimeEnvironments

# Resolve a named DataRobot base environment to its ID (via the DataRobot API)
base_env_id = RuntimeEnvironments.PYTHON_312_APPLICATION_BASE.value.id
```

`schema.llms` additionally holds the LLM Gateway naming helpers
`ensure_datarobot_prefix()` and `DEPLOYED_LLM_PLACEHOLDER_MODEL`. Note these operate on
*gateway / LiteLLM* model strings (`datarobot/azure/gpt-5-mini`), which are a different
namespace from the *playground* LLM ids in `LLMs` (`azure-openai-gpt-5-mini`).

### `datarobot_pulumi_utils.pulumi`

Custom Pulumi resources (mostly
[dynamic providers](https://www.pulumi.com/docs/concepts/resources/dynamic-providers/)
that wrap the DataRobot Python SDK) for operations the official provider does
not expose, all plugging into the normal `pulumi up` create/update/delete
lifecycle. Covers query-generated datasets, dataset refresh, recipe datasets,
challengers, custom model deployments, RAG and playground custom models, proxy
LLM blueprints, execution environments, notebook execution (papermill), export
collection, and stack helpers.

```python
from datarobot_pulumi_utils.pulumi.stack import get_stack
```

`pulumi.llm_credentials.get_runtime_values()` resolves which provider serves a gateway
model, creates the DataRobot credential resources that provider needs, and returns the
custom-model runtime parameter values referencing them.
`pulumi.llm_blueprint.get_blueprint_runtime_parameters()` returns the full runtime
parameter set a blueprint-backed custom model needs to load.

```python
from datarobot_pulumi_utils.pulumi.llm_credentials import get_runtime_values

# `resource_suffix` is part of each credential's resource name, and therefore part of its
# Pulumi identity -- changing it replaces live credentials.
runtime_values = get_runtime_values("datarobot/azure/gpt-5-mini", resource_suffix="[my-app]")
```

### `datarobot_pulumi_utils.common`

Small runtime utilities:

- `get_datarobot_url()` / `fix_url()`: resolve the external DataRobot URL,
  including airgapped on-premise clusters where the API returns internal
  hostnames (see [docs/AIRGAP_URL_MIGRATION.md](docs/AIRGAP_URL_MIGRATION.md)).
- `check_feature_flags()` / `check_feature_flag_set()`: assert that the DataRobot
  feature flags your program depends on are enabled -- from a YAML file, or from an
  in-memory `dict[str, bool]` respectively.

- `verify_llm_gateway_model_availability()`: assert a model is present and active in
  this cluster's LLM Gateway catalog before deploying against it.
- `verify_llm()`: send a one-token "Hi" to the configured LLM -- deployment, gateway, or
  external provider -- so a misconfigured model fails before `pulumi up` rather than after.
  Requires the optional `llm` extra.

```python
from datarobot_pulumi_utils.common import get_datarobot_url, fix_url
```

## Installation

```bash
pip install datarobot-pulumi-utils
# or
uv add datarobot-pulumi-utils
```

`common.llm_validation.verify_llm()` needs `litellm`, which ships as the optional `llm`
extra:

```bash
pip install "datarobot-pulumi-utils[llm]"
# or
uv add "datarobot-pulumi-utils[llm]"
```

Requires Python 3.10+.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and
[Task](https://taskfile.dev/) as the command runner:

```bash
uv sync --all-extras --dev   # set up the environment
task lint-check              # check formatting, lint, and types (ruff + mypy)
task test                    # run the test suite
task build                   # build the package
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache 2.0 - see [LICENSE](LICENSE) for details.
