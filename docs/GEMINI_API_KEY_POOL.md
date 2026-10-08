# Gemini API Key Pool

This project uses a dynamic, thread-safe API key pool for interacting with Gemini models. This design prevents a single exhausted API key (due to rate limits or daily quota caps) from failing the entire application when additional keys are available.

## Configuration

You can configure the key pool using the `.env` file in the `backend/` directory.

### Target Multi-Key Configuration
Use `GEMINI_API_KEYS` (plural) to supply a comma-separated list of keys:
```env
GEMINI_API_KEYS=key1,key2,key3
```

- Whitespace is automatically trimmed.
- Empty entries are ignored.
- Duplicate keys are removed.
- Order is preserved as defined.

### Legacy Single-Key Configuration
For backward compatibility, if `GEMINI_API_KEYS` is not provided or is empty, the application falls back to `GEMINI_API_KEY` (singular):
```env
GEMINI_API_KEY=key1
```

## Ordered Failover Behavior

This architecture implements **ordered failover**, NOT round-robin load balancing. 

1. **Normal Operation:** The application continuously uses the currently active key (starting at index 0) for all requests. As long as the key succeeds, no rotation occurs.
2. **Exhaustion Detection:** If a request fails with a quota or rate-limit error (e.g., HTTP 429, `RESOURCE_EXHAUSTED`), the key is marked as temporarily exhausted.
3. **Failover:** The system immediately moves to the *next* available key in the list and retries the exact same request.
4. **All Keys Exhausted:** If all configured keys become temporarily exhausted, the system throws a clear `RuntimeError` preventing infinite retry loops.

## Error Classification & Recovery

The pool leverages explicit string and error-code matching from the Google Gemini SDKs to distinguish between hard daily quotas and transient rate limits.

### 1. Transient Rate Limit (`429`, `Rate Limit Exceeded`, `Too Many Requests`)
When a key is marked exhausted by a transient burst limit, it enters a **short cooldown** period.
- **Default:** `60` seconds.
- **Environment Variable:** `GEMINI_KEY_TRANSIENT_COOLDOWN_SECONDS`

### 2. Daily Quota Exhaustion (`Quota Exceeded`)
If the API explicitly returns an error mentioning `quota exceeded`, the key is marked exhausted for a **long cooldown** period because it has likely hit the hard 1,500 requests/day limit.
- **Default:** `86400` seconds (24 hours).
- **Environment Variable:** `GEMINI_KEY_QUOTA_COOLDOWN_SECONDS`

### Unhandled/Non-retryable Errors
Ordinary application errors do **NOT** trigger failover:
- Malformed requests (HTTP 400)
- Permission denied / Safety blocks
- Invalid prompts/models
- Authentication failures (unless combined with quota limits)

## Cooldown Behavior

When a key is marked as exhausted, it enters the appropriate cooldown period. During this cooldown, the key is skipped.
Once the cooldown expires, the key becomes eligible again. However, the system does not immediately interrupt the currently active (and succeeding) key. The recovered key will only be used if another failover occurs and the index cycles back to it.

> **Limitation Note:** The system distinguishes quota vs. rate limits entirely by searching the SDK exception string for the word `"quota"`. If the Gemini API changes its error structure to return generic 429s for quota hits without explicit string hints, the key pool will safely fallback to treating them as `TRANSIENT` (retrying every 60 seconds) rather than falsely locking out a key for 24 hours.

## Security

- The application ensures that API keys are **never** logged, printed in exceptions, or exposed in API responses.
- Safe identifiers are used in logs, such as `Gemini request using key index 0`.
- API keys should be properly provisioned from Google Cloud and restricted as necessary.

## Adding a New Key

To add a new key, simply append it to the `GEMINI_API_KEYS` variable in your `.env` file and restart the backend. No code changes are required!

```env
GEMINI_API_KEYS=key1,key2,key3,key4
```
