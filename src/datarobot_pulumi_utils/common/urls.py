# Copyright 2025 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import logging
import os
import urllib.request
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)


def get_datarobot_url() -> str:
    """Return the external-facing DataRobot base URL (no trailing slash, no /api/v2 suffix).

    In airgapped on-premise environments ``DATAROBOT_ENDPOINT`` is typically
    set to the internal nginx URL (``http://datarobot-nginx/api/v2``), which is
    not reachable from outside the cluster.  This function resolves the real
    external URL so that ``pulumi.export`` outputs are usable by end users.

    Resolution order
    ----------------
    1. ``DATAROBOT_WEB_SERVER_URL`` env var — explicit override, highest priority.
       Set this when you know the external URL and want to skip the API call
       (e.g. in CI/CD where the token may not be available yet, or for testing).
    2. ``/clientConfig/`` API endpoint → ``EXTERNAL_WEB_SERVER_URL`` field.
       Called automatically when ``DATAROBOT_API_TOKEN`` is present.  Works in
       both standard and airgapped environments.
    3. Strip ``/api/v2`` from ``DATAROBOT_ENDPOINT`` — fallback that preserves
       the existing behaviour for standard (non-airgapped) deployments.

    Returns
    -------
    str
        External base URL, e.g. ``https://app.datarobot.com`` or
        ``https://my-airgap-cluster.example.com``.  No trailing slash.
    """
    # 1. Explicit override
    if url := os.getenv("DATAROBOT_WEB_SERVER_URL"):
        return url.rstrip("/")

    endpoint = os.getenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2").rstrip("/")
    api_token = os.getenv("DATAROBOT_API_TOKEN", "")

    # 2. Auto-detect via /clientConfig/ (handles airgapped environments)
    if api_token:
        try:
            req = urllib.request.Request(
                f"{endpoint}/clientConfig/",
                headers={"Authorization": f"Bearer {api_token}"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
                data = json.loads(resp.read())
                if external_url := data.get("EXTERNAL_WEB_SERVER_URL"):
                    return external_url.rstrip("/")
        except Exception:
            logger.debug(
                "Could not fetch EXTERNAL_WEB_SERVER_URL from %s/clientConfig/; "
                "falling back to DATAROBOT_ENDPOINT.",
                endpoint,
            )

    # 3. Fallback: strip /api/v2 from DATAROBOT_ENDPOINT
    return endpoint.removesuffix("/api/v2")


def get_deployment_url(deployment_id: str) -> str:
    """Translate deployment ID to GUI URL.

    TODO(CFX-1849): Replace it with a call to Python SDK

    Parameters
    ----------
    deployment_id : str
        DataRobot deployment id.
    """
    base_url = get_datarobot_url()
    return f"{base_url}/console-nextgen/deployments/{deployment_id}/"
