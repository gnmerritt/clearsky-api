# helpers.py

import asyncio
import os
import uuid
from datetime import datetime, timezone

from quart import request

from config_helper import check_override, config, logger

# ======================================================================================================================
# ============================================== global variables ======================================================
blocklist_24_failed = asyncio.Event()
blocklist_failed = asyncio.Event()
runtime = datetime.now(timezone.utc)
version = "3.34.1"
default_push_server = "https://ui.staging.clearsky.app"


# ======================================================================================================================
# ================================================ Main functions ======================================================
async def get_ip() -> str:  # Get IP address of session request
    if "X-Forwarded-For" in request.headers:
        # Get the client's IP address from the X-Forwarded-For header
        ip = request.headers.get("X-Forwarded-For")
        # The client's IP address may contain multiple comma-separated values
        # Extract the first IP address from the list
        ip = ip.split(",")[0].strip()
    else:
        # Use the remote address if the X-Forwarded-For header is not available
        ip = request.remote_addr

    return ip


async def get_time_since(time) -> str:
    if time is None:
        return "Not initialized"
    time_difference = datetime.now(timezone.utc) - time

    minutes = int(time_difference.total_seconds() / 60)
    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours > 0 and remaining_minutes > 0:
        if hours == 1:
            elapsed_time = f"{int(hours)} hour {int(remaining_minutes)} minutes ago"
        else:
            elapsed_time = f"{int(hours)} hours {int(remaining_minutes)} minutes ago"
    elif hours > 0:
        elapsed_time = f"{int(hours)} hour ago" if hours == 1 else f"{int(hours)} hours ago"
    elif minutes > 0:
        elapsed_time = f"{int(minutes)} minute ago" if minutes == 1 else f"{int(minutes)} minutes ago"
    else:
        elapsed_time = "less than a minute ago"

    return elapsed_time


async def get_ip_address():
    if not os.environ.get("CLEAR_SKY") or check_override is True:
        logger.info("IP connection: Using config.ini")
        ip_address = config.get("server", "ip")
        port_address = config.get("server", "port")

        return ip_address, port_address
    else:
        logger.info("IP connection: Using environment variables.")
        ip_address = os.environ.get("CLEAR_SKY_IP")
        port_address = os.environ.get("CLEAR_SKY_PORT")

        return ip_address, port_address


async def get_replication_lag_api_key():  # TODO Need to add dynamic resources for multiple replcation lag calculation
    if not os.environ.get("CLEAR_SKY") and not check_override:
        logger.info("Replication lag: Using config.ini")
        api_key = config.get("environment", "replication_lag_key")
        resource = config.get("environment", "replication_resource")
        replication_lag_api_url = config.get("environment", "replication_lag_api_url")

        return api_key, resource, replication_lag_api_url
    else:
        logger.info("Replication lag: Using environment variables.")
        api_key = os.environ.get("CLEAR_SKY_REPLICATION_LAG_KEY")
        resource = os.environ.get("CLEAR_SKY_REPLICATION_RESOURCE")
        replication_lag_api_url = os.environ.get("CLEAR_SKY_REPLICATION_LAG_API_URL")

        return api_key, resource, replication_lag_api_url


async def get_var_info() -> dict[str, str]:
    config_api_key = config.get("environment", "api_key")
    config_self_server = config.get("environment", "self_server")

    if not os.getenv("CLEAR_SKY") and not check_override:
        push_server = config.get("environment", "push_server")
        api_key = config.get("environment", "api_key")
        self_server = config.get("environment", "self_server")
    else:
        push_server = os.environ.get("CLEARSKY_PUSH_SERVER")
        api_key = os.environ.get("CLEARSKY_API_KEY")
        self_server = os.environ.get("CLEARSKY_SELF_SERVER")

    if not api_key:
        logger.error(f"No API key configured, attempting to use config file: {config_api_key}")
        api_key = config_api_key

    if not push_server:
        logger.error(f"No push server configured, using default push server: {default_push_server}")
        push_server = default_push_server

    if not self_server:
        logger.error(f"No self server configured, attempting to use config file: {config_self_server}")
        self_server = config_self_server

    values = {
        "api_key": api_key,
        "push_server": push_server,
        "self_server": self_server,
    }

    return values


def generate_session_number() -> str:
    return str(uuid.uuid4().hex)
