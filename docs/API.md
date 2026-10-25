# HTTP Interface

The project is primarily a server-rendered Flask application, but it also exposes two lightweight JSON endpoints for demonstration, testing and integration.

## `GET /health`

Returns a simple service and database health response.

Example response:

```json
{
  "service": "automated-emergency-response-system",
  "status": "ok"
}
```

## `GET /api/incidents`

Returns all incident records, newest first.

Example response shape:

```json
{
  "count": 2,
  "incidents": [
    {
      "id": 2,
      "latitude": -36.8509,
      "longitude": 174.7645,
      "impact_g": 6.4,
      "motion_after_impact": false,
      "severity": "CRITICAL",
      "status": "OPEN",
      "created_at": "2026-10-25 00:00:00"
    }
  ]
}
```

## Browser routes

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Render incident dashboard and simulation form |
| POST | `/incident` | Validate and create a simulated incident plus alert audit row |
| POST | `/incident/<id>/resolve` | Mark an incident as resolved |

## Validation behaviour

Incident creation rejects missing fields, invalid latitude/longitude ranges, negative impact values and unsupported motion values. Browser submissions are redirected back to the dashboard rather than exposing an exception.

## Important limitation

No authentication is implemented because this repository is a self-contained demonstration. A real responder system would require identity, authorisation, rate limiting, CSRF protection, audit controls and secure transport.
