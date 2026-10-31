import os
import asyncio
from urllib.parse import urlparse

import aiohttp
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

ALLOWED_DOMAINS = {
    "link4m.net",
    "link4m.org",
    "link4m.com",
    "graffic.com",
    "graffic.net",
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

semaphore = asyncio.Semaphore(5)


def valid_url(url):
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        return (
            parsed.scheme == "https"
            and any(
                host == domain or host.endswith("." + domain)
                for domain in ALLOWED_DOMAINS
            )
        )
    except Exception:
        return False


@client.event
async def on_ready():
    await tree.sync()
    print(f"Bot online: {client.user}")


@tree.command(
    name="bypass",
    description="Kiểm tra và theo chuyển hướng liên kết"
)
@app_commands.describe(url="Liên kết cần kiểm tra")
async def bypass(interaction: discord.Interaction, url: str):
    if not valid_url(url):
        await interaction.response.send_message(
            "❌ Link không hợp lệ hoặc không thuộc miền được hỗ trợ.",
            ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True)

    async with semaphore:
        try:
            timeout = aiohttp.ClientTimeout(total=15)

            async with aiohttp.ClientSession(
                timeout=timeout
            ) as session:
                async with session.get(
                    url,
                    allow_redirects=True,
                    max_redirects=10,
                    headers={
                        "User-Agent": "Mozilla/5.0"
                    }
                ) as response:
                    final_url = str(response.url)

                    await interaction.followup.send(
                        f"✅ **Đã kiểm tra liên kết**\n"
                        f"🔗 Kết quả: <{final_url}>\n"
                        f"📊 HTTP: `{response.status}`"
                    )

        except Exception as error:
            await interaction.followup.send(
                "⚠️ Không xử lý được link này. "
                "Link có thể yêu cầu JavaScript, CAPTCHA "
                "hoặc đăng nhập."
            )


if not TOKEN:
    raise RuntimeError("Chưa thiết lập DISCORD_TOKEN")

client.run(TOKEN)
