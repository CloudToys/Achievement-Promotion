import os
import asyncio
from typing import Any

import aiohttp
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
from linked_roles import RoleMetadataType, LinkedRolesOAuth2, RoleMetadataRecord

load_dotenv()
bot = commands.InteractionBot(
    intents=disnake.Intents.default()
)

async def async_list(values: list) -> Any:
    for value in values:
        yield value
        await asyncio.sleep(0)

@bot.slash_command(name="register", description="Linked Role의 기본적인 연동을 설정합니다.")
@commands.is_owner()
async def _addConnection(inter: disnake.ApplicationCommandInteraction):
    await inter.response.defer(ephemeral=True)
    client = LinkedRolesOAuth2(client_id=bot.user.id, token=os.getenv("BOT_TOKEN"))
    records = [
        RoleMetadataRecord(
            key="complete",
            name="ALL CLEAR!!",
            description="게임의 모든 도전 과제를 달성했는지 여부입니다.",
            type=RoleMetadataType.boolean_equal
        ),
        RoleMetadataRecord(
            key="percentage",
            name="Achievement Percentage",
            description="게임의 도전 과제 달성률입니다.",
            type=RoleMetadataType.interger_greater_than_or_equal
        )
    ]
    session = aiohttp.ClientSession()
    r = await session.get(f"http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid={os.getenv('STEAM_GAME_ID')}&key={os.getenv('STEAM_API_KEY')}&steamid={os.getenv('STEAM_OWNER_ID')}&l=ko")
    res = await r.json()
    data = res["playerstats"]
    async for achievement in async_list(data["achievements"]):
        records.append(RoleMetadataRecord(
            key=achievement["apiname"],
            name=achievement["name"],
            description=achievement["description"],
            type=RoleMetadataType.boolean_equal
        ))
    result = await client.register_role_metadata(records=tuple(records), force=True)
    await inter.edit_original_message(content=str(result))

bot.run(os.getenv("BOT_TOKEN"))