# Facebook → Discord (free GitHub Actions bot)

This bot checks the public Facebook Page `thanthuorigin` and sends newly discovered
post links to a Discord channel through a Discord Webhook.

## Important limitations

- It only works when Facebook exposes the Page/post links to an unauthenticated request.
- Facebook can change its HTML or block automated requests. If that happens, the bot
  will report "No public post links were found" and will not send anything.
- GitHub scheduled workflows have a minimum schedule of 5 minutes, and scheduled runs
  can sometimes be delayed.
- The first run intentionally does NOT send all old posts; it initializes the state.
- Never put your Discord webhook URL directly in `bot.py` or commit it to GitHub.

## Setup

1. Create a **public** GitHub repository.
2. Upload these files while preserving `.github/workflows/facebook-to-discord.yml`.
3. In Discord, create a webhook for your target channel:
   Channel Settings → Integrations → Webhooks → New Webhook → Copy Webhook URL.
4. In GitHub:
   Settings → Secrets and variables → Actions → New repository secret
   - Name: `DISCORD_WEBHOOK_URL`
   - Secret: paste your Discord webhook URL
5. Open the repository's **Actions** tab and enable workflows if GitHub asks.
6. Run **Facebook to Discord → Run workflow** once manually.
7. After that, GitHub checks approximately every 5 minutes.

To test Discord itself, you can also run the workflow manually after creating the secret.

## Changing the Page

Edit `FACEBOOK_PAGE_URL` in the workflow to another public Facebook Page URL.
