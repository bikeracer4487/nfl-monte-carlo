# Data Cache Directory

This directory stores cached API data to minimize API calls and enable offline functionality.

## Cache Files

### schedule_2025.json
- **Purpose**: Complete 2025-26 NFL regular season schedule (272 games)
- **Source**: ESPN API
- **Update Frequency**: Once per season (or force refresh)
- **Max Age**: 24 hours

### results_current.json
- **Purpose**: Completed game results
- **Source**: ESPN Scoreboard API
- **Update Frequency**: Weekly (after games complete)
- **Max Age**: 1 hour

### odds_current.json
- **Purpose**: Current betting odds for upcoming games
- **Source**: The Odds API
- **Update Frequency**: Weekly (to conserve API quota)
- **Max Age**: 1 hour

### teams.json
- **Purpose**: NFL team information (names, divisions, conferences, logos)
- **Source**: ESPN API
- **Update Frequency**: Once per season
- **Never expires**

### user_overrides.json
- **Purpose**: User-defined game result/odds overrides
- **Source**: User input (via GUI in future phases)
- **Update Frequency**: On user change
- **Never auto-deleted**

## Gitignore

All `.json` files in this directory are gitignored to avoid committing cached data.
Only this README and `.gitkeep` are tracked in git.

## Manual Cache Management

### Clear all caches

```python
from src.data.cache_manager import CacheManager
from pathlib import Path

cache = CacheManager(Path("data"))
cache.clear_cache()
```

### Clear specific cache

```python
cache.clear_cache("odds")
```

### Check cache status

```python
info = cache.get_cache_info()
print(info)
```

Or simply delete the JSON files manually:

```bash
rm data/*.json
```

## Cache Location

By default, caches are stored in the `data/` directory at the project root. This can be configured in `.env`:

```
CACHE_DIRECTORY=data
```

## Cache Behavior

- **Schedule**: Cached for 24 hours. The 2025 season schedule is fixed, so it rarely needs updating.
- **Results**: Cached for 1 hour. During game days, results update frequently.
- **Odds**: Cached for 1 hour. Odds change frequently, but we update weekly to conserve API quota.
- **Teams**: Cached indefinitely. Team information doesn't change during a season.
- **Overrides**: Never expire. User changes are permanent until manually cleared.

## Offline Mode

The app works offline using cached data. If caches are stale, you'll see a warning but can continue using old data.

To refresh, click the "Refresh Data" button in the GUI (Phase 4+) or run:

```python
from src.data.schedule_loader import ScheduleLoader
from src.data.espn_api import ESPNAPIClient
from src.data.cache_manager import CacheManager
from pathlib import Path

espn = ESPNAPIClient("https://site.api.espn.com/apis/site/v2", "https://sports.core.api.espn.com/v2")
cache = CacheManager(Path("data"))
loader = ScheduleLoader(espn, cache)

# Force refresh
schedule = loader.load_schedule(force_refresh=True)
```
