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

def list_chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]

async def async_list(values: list) -> Any:
    for value in values:
        yield value
        await asyncio.sleep(0)

@bot.slash_command(name="register", description="Linked Role의 기본적인 연동을 설정합니다.")
@commands.is_owner()
async def _addConnection(inter: disnake.ApplicationCommandInteraction):
    await inter.response.defer(ephemeral=True)
    records = [
        RoleMetadataRecord(
            key="complete",
            name="ALL CLEAR!!",
            description="게임의 도전 과제를 모두 달성해야 합니다.",
            type=RoleMetadataType.boolean_equal
        ),
        RoleMetadataRecord(
            key="percentage",
            name="Achievement Percentage",
            description="% 이상의 도전 과제를 달성해야 합니다.",
            type=RoleMetadataType.interger_greater_than_or_equal
        )
    ]
    data = None
    async with aiohttp.ClientSession() as cs:
        async with cs.get(f"http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid={os.getenv('STEAM_GAME_ID')}&key={os.getenv('STEAM_API_KEY')}&steamid={os.getenv('STEAM_OWNER_ID')}&l=ko") as r:
            res = await r.json()
            data = res["playerstats"]

    async for achievement in async_list(data["achievements"]):
        records.append(RoleMetadataRecord(
            key=achievement["apiname"],
            name=achievement["name"],
            description=achievement["description"],
            type=RoleMetadataType.boolean_equal
        ))
    
    await inter.edit_original_message(content="역할 데이터 등록을 시작합니다!")
    async with LinkedRolesOAuth2(client_id=os.getenv("CLIENT_ID"), token=os.getenv("BOT_TOKEN")) as client:
        async for rec in async_list(list_chunk(records, 3)):
            result = await client.register_role_metadata(records=tuple(rec), force=True)
            await inter.followup.send(result)
            await asyncio.sleep(5)

bot.run(os.getenv("BOT_TOKEN"))