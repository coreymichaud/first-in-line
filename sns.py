import aiohttp
import asyncio

class DiscordNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    async def send_notification(self, message: str):
        delay = 0.2  # Default delay
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.webhook_url, json={"content": message}) as response:
                        if response.status == 204:
                            return  # Success
                        elif response.status == 429:
                            print("Rate limited by Discord. Retrying in 0.5s...")
                            await asyncio.sleep(0.5)
                            continue
                        else:
                            text = await response.text()
                            print(f"Failed to send Discord notification: {response.status} {text}")
                            return
            except Exception as e:
                print(f"Exception during Discord send: {e}")
                await asyncio.sleep(0.5)  # Wait before retrying
