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
import logging
import os
from urllib.parse import urlsplit, urlunsplit

import datarobot as dr

logger = logging.getLogger(__name__)


def get_datarobot_url() -> str:
    """Return the external-facing DataRobot API endpoint including the ``/api/v2`` suffix.

    This is a drop-in replacement for ``os.getenv("DATAROBOT_ENDPOINT")`` that
    resolves the *external* URL even in airgapped on-premise environments where
    ``DATAROBOT_ENDPOINT`` is set to the internal nginx URL
    (``http://datarobot-nginx/api/v2``).

    Resolution order
    ----------------
    1. ``DATAROBOT_WEB_SERVER_URL`` env var — explicit override, highest priority.
       The ``/api/v2`` suffix is appended automatically if absent.
       Set this when you know the external URL and want to skip the API call
       (e.g. in CI/CD where the token may not be available yet, or for testing).
    2. ``/clientConfig/`` API endpoint → ``EXTERNAL_WEB_SERVER_URL`` field.
       Called automatically via the DataRobot SDK client.  The ``/api/v2`` suffix
       is appended automatically.  Works in both standard and airgapped environments.
    3. Return ``DATAROBOT_ENDPOINT`` as-is — it already carries the ``/api/v2``
       suffix by convention, so no transformation is needed.

    Returns
    -------
    str
        External API endpoint, e.g. ``https://app.datarobot.com/api/v2`` or
        ``https://my-airgap-cluster.example.com/api/v2``.  No trailing slash.
    """
    # 1. Explicit override
    if url := os.getenv("DATAROBOT_WEB_SERVER_URL"):
        url = url.rstrip("/")
        return url if url.endswith("/api/v2") else f"{url}/api/v2"

    endpoint = os.getenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2").rstrip("/")

    # 2. Auto-detect via /clientConfig/ (handles airgapped environments)
    try:
        client = dr.client.get_client()
        data = client.get("clientConfig/").json()
        if external_url := data.get("EXTERNAL_WEB_SERVER_URL"):
            external_url = external_url.rstrip("/")
            return external_url if external_url.endswith("/api/v2") else f"{external_url}/api/v2"
    except Exception:
        logger.debug(
            "Could not fetch EXTERNAL_WEB_SERVER_URL from %s/clientConfig/; falling back to DATAROBOT_ENDPOINT.",
            endpoint,
        )

    # 3. Fallback: DATAROBOT_ENDPOINT already has /api/v2
    return endpoint


def fix_url(url: str) -> str:
    """Replace the internal base URL with the external base URL in any URL string.

    In airgapped environments, URLs returned directly by the DataRobot API
    (e.g. ``CustomApplication.application_url``) may contain the internal nginx
    hostname (``http://datarobot-nginx/...``).  This function swaps the
    scheme+host with those from :func:`get_datarobot_url` so the resulting URL
    is reachable from outside the cluster.

    Use this inside ``pulumi.Output.apply()`` for resource properties that come
    directly from the API:

    .. code-block:: python

        from datarobot_pulumi_utils.common import fix_url

        pulumi.export(
            "My App URL",
            my_app.application_url.apply(fix_url),
        )

    Parameters
    ----------
    url : str
        URL to fix (may be internal or already external — both are safe).

    Returns
    -------
    str
        URL with scheme and host replaced by the external base URL.
        Path, query, and fragment are preserved unchanged.
    """
    if not url:
        return url
    # get_datarobot_url() includes /api/v2; urlsplit puts that in the path
    # component, so only scheme+netloc are used here — no change needed.
    external_base = get_datarobot_url()
    parsed_url = urlsplit(url)
    parsed_external = urlsplit(external_base)
    return urlunsplit(
        (
            parsed_external.scheme,
            parsed_external.netloc,
            parsed_url.path,
            parsed_url.query,
            parsed_url.fragment,
        )
    )


def get_deployment_url(deployment_id: str) -> str:
    """Translate deployment ID to GUI URL.

    TODO(CFX-1849): Replace it with a call to Python SDK

    Parameters
    ----------
    deployment_id : str
        DataRobot deployment id.
    """
    base_url = get_datarobot_url().removesuffix("/api/v2")
    return f"{base_url}/console-nextgen/deployments/{deployment_id}/"
