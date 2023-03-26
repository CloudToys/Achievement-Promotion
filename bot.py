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
            key="honor_roll",
            name="Honor roll",
            description="Perfect the tutorial",
            type=RoleMetadataType.boolean_equal,
            name_localizations={
                "ko": ""
            },
            description_localizations={
                "ko": ""
            }
        ),
        RoleMetadataRecord(
            key="new_day",
            name="New Day",
            description="Get through the morning",
            type=RoleMetadataType.boolean_equal,
            name_localizations={
                "ko": ""
            },
            description_localizations={
                "ko": ""
            }
        ),
        RoleMetadataRecord(
            key="go_to_bed",
            name="Go to bed",
            description="Get all perfect scores",
            type=RoleMetadataType.boolean_equal,
            name_localizations={
                "ko": ""
            },
            description_localizations={
                "ko": ""
            }
        ),
        RoleMetadataRecord(
            key="percentage",
            name="% of Achievements",
            description="% of cleared achievements",
            type=RoleMetadataType.interger_greater_than_or_equal,
            name_localizations={
                "ko": ""
            },
            description_localizations={
                "ko": ""
            }
        )
    ]
    async with LinkedRolesOAuth2(client_id=os.getenv("CLIENT_ID"), token=os.getenv("BOT_TOKEN")) as client:
        try:
            result = await client.register_role_metadata(records=tuple(records), force=True)
        except Exception as e:
            await inter.edit_original_message(e)
        else:
            await inter.edit_original_message(content=f"> :star2: 역할 추가가 완료되었습니다!\n{result}")

bot.run(os.getenv("BOT_TOKEN"))
