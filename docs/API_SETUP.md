# API Setup Guide

The application now relies exclusively on ESPN's public scoreboard endpoints for schedules, scores, and standings. There are **no third-party betting APIs** or API keys to configure.

## ESPN Data Sources

- **Schedule / Scores**: [site.api.espn.com](https://site.api.espn.com/apis/site/v2)
- **Core Team Metadata**: [sports.core.api.espn.com](https://sports.core.api.espn.com/v2)

These endpoints are publicly accessible and do not require authentication. We aggressively cache all responses on disk (`data/` directory) so the app can run offline after the first sync.

## Environment Variables

Create a `.env` (optional) if you want to override defaults:

```
LOG_LEVEL=INFO
CACHE_DIRECTORY=data
```

If the file is absent, sensible defaults are used.

## Testing Connectivity

Run the Python test suite normally:

```bash
cd backend
pytest
```

All tests are self-contained and do not hit live APIs—fixtures and cached JSON files provide deterministic data.

## Troubleshooting

- **ESPN API not responding**: ESPN occasionally rate-limits or returns 5xx errors. Re-run later; cached data will continue to work in the meantime.
- **Stale data**: Delete the relevant cache via the GUI or remove files inside `data/` (e.g., `schedule_2025.json`, `results_current.json`) and re-run the refresh flow.

That's it! No additional setup is needed beyond Python/Node dependencies.
