# D-06: API Rate Limits

The Solstice API is available on Growth and Enterprise plans. All endpoints are authenticated with an API key passed in the Authorization header. Responses are returned as JSON, and pagination is handled via a `next_cursor` field in the response body. We recommend caching responses where possible to avoid unnecessary repeat calls, especially for endpoints that return large datasets. Rate limits: Growth plans are limited to 60 requests per minute, and Enterprise plans are limited to 300 requests per minute, per API key. Exceeding the limit returns an HTTP 429 response.
