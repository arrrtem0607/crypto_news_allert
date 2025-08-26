# Crypto News Alert

Starter code for a local crypto news aggregation system.  The repository
currently contains two reusable modules:

* `app/providers/base.py` – template for building provider adapters with
  polling and exponential backoff.
* `app/core/telegram.py` – minimal Telegram publisher that formats news items
  and sends them to a channel.

More functionality will be added in subsequent sprints.
