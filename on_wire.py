# on_wire.py

import urllib.parse
import asyncio
from typing import Optional
import httpx
from config_helper import logger, limiter
import dns.resolver
import database_handler
from errors import InternalServerError


# ======================================================================================================================
# ============================================= On-Wire requests =======================================================
async def resolve_handle(info):  # Take Handle and get DID
    base_url = "https://api.bsky.app/xrpc/"
    url = urllib.parse.urljoin(base_url, "com.atproto.identity.resolveHandle")
    params = {
        "handle": info
    }

    encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    full_url = f"{url}?{encoded_params}"
    logger.debug(full_url)

    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(full_url)
                response_json = response.json()

                if response.status_code == 200:
                    result = list(response_json.values())[0]

                    return result
                elif response.status_code == 400:
                    try:
                        error_message = response.json()["error"]
                        message = response.json()["message"]
                        if error_message == "InvalidRequest" and "Unable to resolve handle" in message:
                            logger.warning("Could not find repo: " + str(info))

                            return None
                    except KeyError:
                        logger.error(f"Error getting response: key error")

                        return None
                else:
                    logger.warning(f"Error resolving {info} response: {response_json}")

                    return None
        except Exception as e:
            retry_count += 1
            logger.error(f"Error occurred while making the API call: {e}")

            return None

    logger.warning("Resolve error for: " + info + " after multiple retries.")

    return None


async def resolve_did(did, did_web_pds=False) -> Optional[list]:  # Take DID and get handle
    base_url = "https://plc.directory/"
    url = f"{base_url}{did}"
    stripped_record = []

    max_retries = 5
    retry_count = 0

    if "did:web" in did:
        logger.info("Resolving did:web")
        short_did = did[len("did:web:"):]
        url = f"https://{urllib.parse.unquote(short_did)}/.well-known/did.json"

    logger.debug(url)

    while retry_count < max_retries:
        try:
            async with limiter:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)

                response_json = response.json()
                logger.debug("response: " + str(response_json))

                if response.status_code == 200:

                    if "did:web" in did:
                        try:
                            record = response_json["alsoKnownAs"]
                        except Exception as e:
                            logger.error(f"Error getting did:web handle: {e} | did: {did} | {url}")

                            record = None
                    else:
                        record = response_json.get("alsoKnownAs", "")

                    for i in record:
                        # record = str(record)
                        stripped_record.append(i.replace("at://", ""))
                        # stripped_record = stripped_record.strip("[]").replace("'", "")

                    if did_web_pds:
                        logger.info(f"Getting PDS for {did}")

                        try:
                            endpoint = response_json["service"][0]["serviceEndpoint"]

                            logger.info(f"Endpoint retrieved for {did}: {endpoint}")

                            return endpoint
                        except Exception as e:
                            logger.error(f"Error getting did:web PDS: {e} | did: {did} | PDS: {endpoint} | {url}")

                            return None

                    if "RateLimit Exceeded" in stripped_record:
                        retry_count += 1
                        sleep_time = 15

                        logger.warning(f"Approaching Rate limit waiting for {sleep_time} seconds")

                        await asyncio.sleep(sleep_time)

                    return stripped_record if stripped_record else None
                elif response.status_code == 429:
                    logger.warning("Too many requests, pausing.")
                    await asyncio.sleep(10)
                elif response.status_code == 404:
                    logger.warning(f"404 not found: {did}")

                    error_message = response_json.get("message", "")
                    logger.debug(error_message)

                    if "did not registered" in error_message.lower():
                        await database_handler.deactivate_user(did)

                        return None
                    elif "did not available" in error_message.lower():
                        logger.warning("User not found. Skipping...")

                        return None
                    else:
                        error_message = response_json.get("message", "")
                        logger.warning(error_message)

                        await database_handler.deactivate_user(did)

                        return None
                else:
                    error_message = response_json.get("message", "")
                    logger.debug(error_message)

                    if "did not registered" in error_message.lower():
                        await database_handler.deactivate_user(did)

                        return None
                    elif "did not available" in error_message.lower():
                        logger.warning("User not found. Skipping...")

                        return None
                    else:
                        retry_count += 1
                        logger.warning("Error:" + str(response.status_code))
                        logger.warning("Retrying: " + str(url))
                        await asyncio.sleep(5)
        except httpx.DecodingError as e:
            retry_count += 1
            logger.error(f"Error occurred while parsing JSON response: {e}")

            return None
        except httpx.RequestError as e:
            retry_count += 1
            logger.error(f"Error occurred while making the API call: {str(e)} {url}")

            return None
        except httpx.HTTPStatusError as e:
            retry_count += 1
            logger.error(f"Error occurred while parsing JSON response: {str(e)} {url}")

            return None
        except Exception as e:
            retry_count += 1
            logger.error(f"An unexpected error occurred: {str(e)} {url}")

            return None

    logger.warning("Failed to resolve: " + str(did) + " after multiple retries.")

    return None


async def get_avatar_id(did, aux=False):
    handle = did
    base_url = "https://api.bsky.app/xrpc/"
    collection = "app.bsky.actor.profile"
    rkey = "self"
    url = urllib.parse.urljoin(base_url, "com.atproto.repo.getRecord")
    params = {
        "repo": handle,
        "collection": collection,
        "rkey": rkey
    }

    encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    full_url = f"{url}?{encoded_params}"
    logger.debug(full_url)

    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(full_url)
                response_json = response.json()
                logger.debug("response: " + str(response_json))

                if response.status_code == 200:
                    if aux:
                        try:
                            display_value = response_json['value']['displayName']
                        except Exception:
                            display_value = None

                        try:
                            description = response_json['value']['description']
                        except Exception:
                            description = None

                        return display_value, description
                    avatar_info = response_json.get("value", {}).get("avatar", {})
                    avatar_link = avatar_info.get("ref", {}).get("$link", "")
                    avatar_mimetype = avatar_info.get("mimeType", "")
                    if avatar_link and "jpeg" in avatar_mimetype:

                        return avatar_link
                    elif avatar_link:
                        logger.warning(f"No picture format or incorrect format: {avatar_mimetype}")
                        return avatar_link
                    elif not avatar_link:
                        avatar_cid = avatar_info.get("cid", "")

                        return avatar_cid
                    else:
                        retry_count += 1
                        logger.warning("Error:" + "status code: " + str(response.status_code))
                        logger.error("Could not find avatar ID or picture format")
                        logger.warning("Retrying: " + str(full_url))
                        await asyncio.sleep(10)
                elif response.status_code == 400:
                    logger.warning("User not found. Skipping...")
                    if aux:
                        return None, None

                    return None
                else:
                    error_message = response_json.get("message", "")
                    logger.debug(error_message)

                    break
        except httpx.DecodingError as e:
            retry_count += 1
            logger.error(f"Error occurred while parsing JSON response: {e}")

            return None
        except httpx.RequestError as e:
            retry_count += 1
            logger.error(f"Error occurred while making the API call: {str(e)} {full_url}")

            return None
        except httpx.HTTPStatusError as e:
            retry_count += 1
            logger.error(f"Error occurred while parsing JSON response: {str(e)} {full_url}")

            return None
        except Exception as e:
            retry_count += 1
            logger.error(f"An unexpected error occurred: {str(e)} {full_url}")

            return None

    logger.warning("Failed to resolve: " + str(did) + " after multiple retries.")

    return "Error"


async def get_profile_picture(did, avatar_id):
    base_url = "https://av-cdn.bsky.app/img/feed_fullsize/plain/"
    params = {
        "did": did,
        "/": avatar_id
    }

    encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    full_url = f"{base_url}?{encoded_params}"
    logger.debug(full_url)

    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(full_url)
                response_json = response.json()
                logger.debug("response: " + str(response_json))

                if response.status_code == 200:
                    avatar_info = response_json.get("value", {}).get("avatar", {})
                    avatar_link = avatar_info.get("ref", {}).get("$link", "")
                    avatar_mimetype = avatar_info.get("mimeType", "")
                    if avatar_link and "jpeg" in avatar_mimetype:

                        return avatar_link
                else:
                    error_message = response_json.get("message", "")
                    logger.debug(error_message)

                    if "could not find user" in error_message.lower():
                        logger.warning("User not found. Skipping...")

                        return None
                    else:
                        retry_count += 1
                        logger.warning("Error:" + str(response.status_code))
                        logger.warning("Retrying: " + str(full_url))
                        await asyncio.sleep(10)
        except httpx.DecodingError as e:
            retry_count += 1
            logger.error(f"Error occurred while parsing JSON response: {e}")

            return None
        except httpx.RequestError as e:
            retry_count += 1
            logger.error(f"Error occurred while making the API call: {str(e)} {full_url}")

            return None
        except httpx.HTTPStatusError as e:
            retry_count += 1
            logger.error(f"Error occurred while parsing JSON response: {str(e)} {full_url}")

            return None
        except Exception as e:
            retry_count += 1
            logger.error(f"An unexpected error occurred: {str(e)} {full_url}")

            return None

    logger.warning("Failed to resolve: " + str(did) + " after multiple retries.")

    return "Error"


async def resolve_handle_wellknown_atproto(ident):
    url = f"https://{urllib.parse.unquote(ident)}/.well-known/atproto-did"

    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    try:
                        response_json = response.json()
                    except Exception as e:
                        logger.error(f"Error getting json response: {e}")
                        try:
                            response_json = response.text.strip()
                        except Exception as e:
                            logger.error(f"Error getting response from text: {e}")

                            try:
                                response_json = response.content
                            except Exception as e:
                                logger.error(f"Error getting response from content: {e}")

                                raise InternalServerError

                    return response_json
                if response.status_code == 400:
                    logger.debug(f"response 400: {response.json()}")

                    return None

                retry_count += 1
        except Exception as e:
            retry_count += 1
            logger.error(f"Error occurred while making the API call: {e}")

    if retry_count == max_retries:
        logger.warning("Resolve error for: " + ident + " after multiple retries.")

        return None


async def verify_handle(identity) -> bool:
    handle1 = None
    handle2 = None
    handle3 = None

    at_proto_lookup = "_atproto."

    lookup = f"{at_proto_lookup}{identity}"

    at_proto_result = await resolve_handle_wellknown_atproto(identity)

    bsky_result = await resolve_handle(identity)

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        result = resolver.resolve(lookup, "TXT")

        if result:
            result = str(result[0])
            dns_result = result.strip('"')
            dns_result = dns_result.replace('did=', '')
        else:
            dns_result = None
    except Exception as e:
        logger.error(f"Error resolving DNS: {e}")

        dns_result = None

    if (at_proto_result is not None and "did:plc" in at_proto_result) or (bsky_result is not None and "did:plc" in bsky_result) or (dns_result is not None and "did:plc" in dns_result):
        if "bsky.social" in identity:
            if at_proto_result and bsky_result:
                if at_proto_result == bsky_result:
                    return True
                else:
                    return False
        else:
            if dns_result and bsky_result:
                if dns_result == bsky_result:
                    return True
                else:
                    return False
            elif bsky_result and at_proto_result:
                if bsky_result == at_proto_result:
                    return True
                else:
                    return False
            else:
                logger.error(f"validity case didn't match for {identity} | at_proto: {at_proto_result} | bsky: {bsky_result} | dns: {dns_result}")

                return False
    elif (at_proto_result is not None and "did:web" in at_proto_result) or (bsky_result is not None and "did:web" in bsky_result) or (dns_result is not None and "did:web" in dns_result):
        if at_proto_result is not None and "did:web" in at_proto_result:
            handle1 = await resolve_did(at_proto_result)
        elif bsky_result is not None and "did:web" in bsky_result:
            handle2 = await resolve_did(bsky_result)
        elif dns_result is not None and "did:web" in dns_result:
            handle3 = await resolve_did(dns_result)

        handle1 = handle1[0] if handle1 else None
        handle2 = handle2[0] if handle2 else None
        handle3 = handle3[0] if handle3 else None

        if identity == handle1 or identity == handle2 or identity == handle3:
            if dns_result and bsky_result:
                if dns_result == bsky_result:
                    return True
                else:
                    return False
            elif bsky_result and at_proto_result:
                if bsky_result == at_proto_result:
                    return True
                else:
                    return False
            else:
                logger.error(f"validity case didn't match for {identity} | at_proto: {at_proto_result} | bsky: {bsky_result} | dns: {dns_result}")

                return False
    else:
        return False


async def describe_pds(pds) -> bool:
    status_code = None

    url = f"{pds}/xrpc/com.atproto.server.describeServer"

    logger.debug(url)

    try:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, follow_redirects=True)
            except Exception:
                return False
            try:
                num_redirects = len(response.history)
                if num_redirects > 0:
                    logger.warning(f"Number of redirects: {num_redirects}")
            except Exception:
                pass
            try:
                status_code = response.status_code
            except Exception:
                pass
            if status_code:
                await database_handler.set_status_code(pds, status_code)

            if response.status_code == 200:
                response_json = response.json()
                available_user_domains = str(response_json["availableUserDomains"]).strip("[]")
                logger.debug(f"available_user_domains: {available_user_domains}")
                if available_user_domains is not None:
                    return True
                else:
                    return False
            else:
                return False
    except Exception:
        logger.warning(f"Failed to describe PDS: {url}")

        return False


async def get_labeler_info(did) -> dict[str, Optional[str]]:
    url = f"https://api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={did}"

    logger.debug(url)

    data = {}

    try:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
            except Exception:
                return {}

            if response.status_code == 200:
                response_json = response.json()
                display_name = response_json.get("displayName", None)
                description = response_json.get("description", None)

                if display_name == "":
                    display_name = None
                if description == "":
                    description = None

                data["displayName"] = display_name
                data["description"] = description

                return data
            elif response.status_code == 400:
                await database_handler.set_labeler_status(did, False)

                return {"error": "error"}
            else:
                await database_handler.set_labeler_status(did, False)

                return {"error": "error"}
    except Exception:
        logger.warning(f"Failed to get label profile info: {url}")

        return {}


async def get_pds(identifier):
    base_url = "https://plc.directory/"
    retry_count = 0
    max_retries = 5

    while retry_count < max_retries:
        full_url = f"{base_url}{identifier}"
        logger.debug(f"full url: {full_url}")

        try:
            async with limiter:
                async with httpx.AsyncClient() as client:
                    response = await client.get(full_url, timeout=10)  # Set an appropriate timeout value (in seconds)
        except httpx.ReadTimeout:
            logger.warning("Request timed out. Retrying... Retry count: %d", retry_count)
            retry_count += 1
            await asyncio.sleep(5)
            continue
        except httpx.RequestError as e:
            logger.warning("Error during API call: %s", e)
            retry_count += 1
            await asyncio.sleep(5)
            continue

        if response.status_code == 200:
            response_json = response.json()

            try:
                endpoint = response_json.get('service')[0]['serviceEndpoint']
            except Exception as e:
                endpoint = None
                logger.error(f"Error getting PDS endpoint: {full_url} {e}")

            return endpoint
        elif response.status_code == 429:
            logger.warning("Received 429 Too Many Requests. Retrying after 30 seconds...")
            await asyncio.sleep(30)  # Retry after 60 seconds
        elif response.status_code == 400:
            try:
                error_message = response.json()["error"]
                message = response.json()["message"]
                if error_message == "InvalidRequest" and "Could not find repo" in message:
                    logger.warning("Could not find repo: " + str(identifier))

                    return None
            except KeyError:
                return None
        else:
            retry_count += 1
            logger.warning("Error during API call. Status code: %s", response.status_code)
            await asyncio.sleep(5)

            continue
    if retry_count == max_retries:
        logger.warning("Could not get PDS for: " + identifier)

        return None


async def get_created_date(identifier):
    base_url = "https://plc.directory/"
    collection = "log/audit"
    retry_count = 0
    max_retries = 5

    if "did:web" in identifier:
        return None
    while retry_count < max_retries:
        full_url = f"{base_url}{identifier}/{collection}"
        logger.debug(f"full url: {full_url}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(full_url, timeout=10)  # Set an appropriate timeout value (in seconds)
        except httpx.ReadTimeout:
            logger.warning("Request timed out. Retrying... Retry count: %d", retry_count)
            retry_count += 1
            await asyncio.sleep(5)
            continue
        except httpx.RequestError as e:
            logger.warning("Error during API call: %s", e)
            retry_count += 1
            await asyncio.sleep(5)
            continue

        if response.status_code == 200:
            response_json = response.json()

            for record in response_json:
                created_at_value = record.get("createdAt")

                return created_at_value
        elif response.status_code == 429:
            retry_count += 1

            logger.warning("Received 429 Too Many Requests. Retrying after 30 seconds...")
            await asyncio.sleep(30)  # Retry after 60 seconds
        elif response.status_code == 400:
            try:
                error_message = response.json()["error"]
                message = response.json()["message"]
                if error_message == "InvalidRequest" and "Could not find repo" in message:
                    logger.warning("Could not find repo: " + str(identifier))

                    return "unknown"
            except KeyError:
                return None
        elif response.status_code == 404:
            return "unknown"
        else:
            retry_count += 1

            logger.warning("Error during API call. Status code: %s", response.status_code)
            await asyncio.sleep(5)

            continue
    if retry_count == max_retries:
        logger.warning("Could not get handle history for: " + identifier)

        return None


async def get_status(did, pds):  # Take Handle and get DID
    base_url = f"{pds}/xrpc/"
    url = urllib.parse.urljoin(base_url, "com.atproto.sync.getRepoStatus")
    params = {
        "did": did
    }

    encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    full_url = f"{url}?{encoded_params}"
    logger.debug(full_url)

    max_retries = 5
    retry_count = 0

    if "https://" in pds:
        while retry_count < max_retries:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(full_url)
                    response_json = response.json()

                    if response.status_code == 200:
                        status = response_json.get("active")
                        reason = response_json.get("status")

                        result = {"status": status, "reason": reason}

                        return result
                    elif response.status_code == 400:
                        status = False
                        reason = None

                        result = {"status": status, "reason": reason}

                        return result
                    elif response.status_code == 429:
                        retry_count += 1

                        logger.warning(f"Received 429 Too Many Requests. Retrying after 60 seconds...{full_url}")

                        await asyncio.sleep(60)  # Retry after 60 seconds
                    else:
                        status = False
                        reason = None

                        result = {"status": status, "reason": reason}

                        return result
            except Exception as e:
                retry_count += 1
                logger.error(f"Error occurred while making the API call: {e}")

        if retry_count == max_retries:
            logger.warning(f"Resolve error for: {did} after multiple retries.")

            status = None
            reason = None

            result = {"status": status, "reason": reason}

            return result
    else:
        status = False
        reason = None

        result = {"status": status, "reason": reason}

        return result
