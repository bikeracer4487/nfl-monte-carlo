# API Setup Guide

## The Odds API

### Step 1: Sign Up

1. Visit https://the-odds-api.com/
2. Click "Get Free API Key"
3. Enter your email and create an account
4. Verify your email

### Step 2: Get Your API Key

1. Log in to your account
2. Navigate to the Dashboard
3. Copy your API key

### Step 3: Configure the Application

1. Create a `.env` file in the project root (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```
   ODDS_API_KEY=your_actual_api_key_here
   ```

### API Quota

**Free Tier**:
- 500 requests per month
- Resets on the 1st of each month
- Sufficient for weekly odds updates throughout the season

**Usage Strategy**:
- Cache odds data aggressively (default: 1 hour TTL)
- Update once per week (≈16-20 calls per update)
- 500 calls/month = 25-30 weekly updates (covers entire season)

**Paid Tier** ($30/month):
- 20,000 requests per month
- Use if you need more frequent updates

### Monitoring Usage

- Check remaining quota in dashboard
- App displays remaining requests after each API call
- Use `client.get_requests_remaining()` to check programmatically

## ESPN API

**No setup required!**

ESPN's API is free and does not require an API key.

## Testing API Connections

Run the test suite with real API calls:

```bash
# Run all API tests (requires valid ODDS_API_KEY in .env)
pytest -m api

# Run without API tests
pytest -m "not api"
```

## Troubleshooting

### "Odds API key not configured"

Make sure your `.env` file exists and contains:
```
ODDS_API_KEY=your_actual_key
```

### "API quota exceeded"

You've used all 500 free monthly requests. Either:
- Wait until next month (resets on 1st)
- Upgrade to paid tier
- Use cached odds data

### ESPN API not responding

ESPN's API is unofficial and may occasionally be unavailable. The app will use cached data when possible.
