import requests
import certifi
import os
import time

# ---------------------- Configuration Section ----------------------
# List of Shopify store domains to process
SHOPS = ["domain1.myshopify.com", "domain2.myshopify.com"]

# Corresponding Admin API tokens for each store (keep these secure!)
API_TOKENS = ["REDACTED", "REDACTED"]

# Shopify API versions for each store (must match order of SHOPS)
API_VERSIONS = ["2023-10", "2025-04"]

# Number of draft orders to fetch per API request (Shopify max is 250)
PER_PAGE = 250

# If True, marks draft orders as payment pending instead of paid
PAYMENT_PENDING = False

# Timeout (in seconds) for each HTTP request to Shopify
REQUEST_TIMEOUT = 15

# SSL verification for HTTPS requests (set SSL_VERIFY=false in env to disable)
SSL_VERIFY = os.getenv("SSL_VERIFY", "true").lower() not in ("0", "false", "no")

# Enable verbose debug logging for request URLs and payloads
# Set DEBUG_LOG_URLS=true in env to enable
# DEBUG_LOG_URLS = os.getenv("DEBUG_LOG_URLS", "false").lower() not in ("0", "false", "no")
DEBUG_LOG_URLS = False

# Global counters for reporting
total_open_drafts = 0
total_completed = 0

# Tag to skip when processing draft orders (e.g., skip orders with this tag)
skip_tags = "shipping_charge"

# ---------------------- Credential Check ----------------------
# Ensure both SHOPS and API_TOKENS are set
if not SHOPS or not API_TOKENS:
    print("Missing URL or API_TOKEN in environment")
    exit(1)

# ---------------------- Helper Functions ----------------------

def fetch_open_draft_orders(session, shop, api_version, page_info=None):
    """
    Fetch a single page of open draft orders from a Shopify store.

    Args:
        session (requests.Session): Authenticated session for requests.
        shop (str): Shopify store domain.
        api_version (str): Shopify API version.
        page_info (str, optional): Token for pagination. None for first page.

    Returns:
        tuple: (list of draft orders, next page_info token or None)
    """
    url = f"https://{shop}/admin/api/{api_version}/draft_orders.json"
    params = {"status": "open", "limit": PER_PAGE}
    # Add pagination token if present
    if page_info:
        params["page_info"] = page_info
    if DEBUG_LOG_URLS:
        print(f"GET {url} params={params}")

    # Execute HTTP GET request with error handling
    try:
        resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        # Print debug info on HTTP error
        print(f"HTTP error {resp.status_code}: {resp.text}")
        print("Request headers:", resp.request.headers)
        exit(1)
    except requests.exceptions.SSLError as ssl_err:
        # On SSL error, retry with SSL verification disabled if not already
        if SSL_VERIFY:
            print(f"SSL error fetching drafts: {ssl_err}\n Retrying with SSL_VERIFY=false...")
            session.verify = False
            try:
                resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
            except Exception as e:
                print(f"Retry failed: {e}")
                exit(1)
        else:
            print(f"SSL error fetching drafts even with verification disabled: {ssl_err}")
            exit(1)
    except requests.exceptions.ConnectTimeout:
        print(f"Connection timed out when connecting to {url}")
        exit(1)
    except Exception as e:
        print(f"Error fetching drafts: {e}")
        exit(1)

    data = resp.json()

    # Parse Link header for pagination (get next page_info token)
    link_header = resp.headers.get("Link", "")
    next_info = None
    for part in link_header.split(","):
        if 'rel="next"' in part:
            import re
            m = re.search(r"page_info=([^&]+)", part)
            if m:
                next_info = m.group(1)
    return data.get("draft_orders", []), next_info

def complete_draft_order(session, shop, api_version, draft_id):
    """
    Complete a draft order using Shopify's GraphQL API.

    Args:
        session (requests.Session): Authenticated session for requests.
        shop (str): Shopify store domain.
        api_version (str): Shopify API version.
        draft_id (int): ID of the draft order to complete.

    Returns:
        dict or None: Order data if successful, None otherwise.
    """
    graphql_url = f"https://{shop}/admin/api/{api_version}/graphql.json"
    gid = f"gid://shopify/DraftOrder/{draft_id}"
    mutation = """
    mutation draftOrderComplete($id: ID!, $paymentPending: Boolean!) {
      draftOrderComplete(id: $id, paymentPending: $paymentPending) {
        draftOrder {
          id
        }
        userErrors {
          field
          message
        }
      }
    }"""
    variables = {'id': gid, 'paymentPending': PAYMENT_PENDING}
    payload = {'query': mutation, 'variables': variables}
    try:
        if DEBUG_LOG_URLS:
            print(f"POST {graphql_url} payload={payload}")
        resp = session.post(graphql_url, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        print(f"Network error completing draft {draft_id}: {e}")
        return None

    # Check for GraphQL or user errors
    errors = result.get("errors")
    user_errors = result.get('data', {}).get('draftOrderComplete', {}).get('userErrors')
    if errors or user_errors:
        print(f"GraphQL errors completing draft order {draft_id}: {errors or user_errors}")
        return None

    # Extract order info from response
    try:
      return result["data"]["draftOrderComplete"]["order"]
    except Exception as e:
      print(f"ignore: {e}")
      return None

def process_drafts(shop, api_token, api_version):
    """
    Main workflow for processing draft orders in a Shopify store:
      1. Fetch all open draft orders (with pagination)
      2. Optionally filter out drafts with specific tags (e.g., "shipping_charge")
      3. Complete the remaining draft orders

    Args:
        shop (str): Shopify store domain.
        api_token (str): Admin API token.
        api_version (str): Shopify API version.
    """
    global total_open_drafts, total_completed
    next_page = None        # Next page token for pagination
    count = 0               # Number of drafts completed in this store
    total_count = 0         # Total drafts found in this store

    # Set up reusable session for all requests to this store
    session = requests.Session()
    # Use certifi bundle for SSL verification if enabled
    if SSL_VERIFY:
        session.verify = certifi.where()
    else:
        session.verify = False
        print("SSL verification is disabled")
    # Set up headers for API requests
    session.headers.update({
        "X-Shopify-Access-Token": api_token,
        "Content-Type": "application/json",
        "Accept": "application/json"
    })

    # Loop through all open draft orders (handle pagination)
    while True:
        drafts, next_page = fetch_open_draft_orders(session, shop, api_version, next_page)
        if not drafts:
            # No more drafts to process
            break

        for d in drafts:
            total_open_drafts += 1
            total_count += 1
            draft_id = d["id"]

            # Complete draft order (could add tag filtering here if needed)
            print(f"Completing draft order #{draft_id}...", end="")
            order = complete_draft_order(session, shop, api_version, draft_id)
            print("Completed draft order")
            total_completed += 1
            count += 1
            # Sleep to avoid hitting Shopify API rate limits
            time.sleep(0.5)

        # If there's no next page, exit loop
        if not next_page:
            break
    print(f"********Completed {count} out of {total_count} open draft orders in {shop}.********")

# ---------------------- Main Script Entry Point ----------------------

if __name__ == "__main__":
    # Loop through all configured stores and process their draft orders
    for shop, api_token, api_version in zip(SHOPS, API_TOKENS, API_VERSIONS):
        print(f"********Fetching open draft orders in {shop}...********")
        process_drafts(shop, api_token, api_version)

    print(f"********Completed {total_completed} out of {total_open_drafts} open draft orders from both stores.********")