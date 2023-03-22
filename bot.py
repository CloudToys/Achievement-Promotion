import os
import asyncio
from typing import Any

import disnake
from disnake.ext import commands
from dotenv import load_dotenv
from linked_roles import RoleMetadataType, LinkedRolesOAuth2, RoleMetadataRecord

load_dotenv()
bot = commands.InteractionBot(
    status=disnake.Status.dnd,
    activity=disnake.Activity(type=disnake.ActivityType.watching, name="Achievements"),
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
            key="tutorial",
            name="Honor roll",
            description="튜토리얼 스테이지를 퍼펙트로 클리어해야 합니다.",
            type=RoleMetadataType.boolean_equal
        ),
        RoleMetadataRecord(
            key="allperfect",
            name="Go to bed",
            description="모든 스테이지를 퍼펙트로 클리어해야 합니다.",
            type=RoleMetadataType.boolean_equal
        ),
        RoleMetadataRecord(
            key="complete",
            name="ALL CLEAR!!",
            description="게임의 도전 과제를 모두 달성해야 합니다.",
            type=RoleMetadataType.boolean_equal
        ),
        RoleMetadataRecord(
            key="percentage",
            name="Percent of Achievement",
            description="% 이상의 도전 과제를 달성해야 합니다.",
            type=RoleMetadataType.interger_greater_than_or_equal
        ),
    ]
    async with LinkedRolesOAuth2(client_id=os.getenv("CLIENT_ID"), token=os.getenv("BOT_TOKEN")) as client:
        try:
            await client.register_role_metadata(records=tuple(records), force=True)
        except Exception as e:
            await inter.edit_original_message(e)
        else:
            await inter.edit_original_message(content="> :star2: 역할 추가가 완료되었습니다!")

bot.run(os.getenv("BOT_TOKEN"))