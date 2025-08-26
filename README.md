# Crypto News Alert

Starter code for a local crypto news aggregation system.  The repository
currently contains two reusable modules:

* `app/providers/base.py` – template for building provider adapters with
  polling and exponential backoff.
* `app/core/telegram.py` – minimal Telegram publisher that formats news items
  and sends them to a channel.

The repository now includes a minimal end-to-end pipeline using the
`Newsdata.io` provider.  Items are normalized, de-duplicated, scored and, if
the score passes the configured threshold, published to a Telegram channel.

## Quick start

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure secrets**

   Copy `.env.example` to `.env` and fill in your tokens.

3. **Adjust runtime options**

   Edit `config.yaml` if you need to change polling intervals, scoring
   parameters or the Telegram channel.

4. **Run the ingestor**

   ```bash
   python -m app.services.ingestor
   ```

The ingestor polls Newsdata.io every 45 seconds, filters and scores incoming
items and publishes high-scoring alerts to the configured Telegram channel.
