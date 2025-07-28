# Shopify Open Draft Order Completion

## Description

This script automates the process of fetching and completing open draft orders from multiple Shopify stores using the Shopify Admin API. It supports pagination, error handling, and can be configured to skip draft orders with specific tags or non-zero payment due amounts. The tool is designed for bulk operations and can be run with minimal configuration.

## Features

- **Multi-store Support:** Handles multiple Shopify stores in a single run.
- **API Versioning:** Supports different API versions per store.
- **Pagination:** Fetches all open draft orders, handling Shopify’s paginated responses.
- **GraphQL Mutation:** Completes draft orders using Shopify’s GraphQL API.
- **Robust Error Handling:** Handles HTTP, SSL, and network errors gracefully.
- **Configurable SSL Verification:** Optionally disable SSL verification via environment variable.
- **Verbose Debug Logging:** Optional debug output for request URLs and payloads.
- **Rate Limiting:** Includes delays to avoid hitting Shopify API rate limits.
- **Summary Output:** Prints a summary of processed and completed draft orders per store and overall.
