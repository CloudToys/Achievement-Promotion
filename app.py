import asyncio
import os
from urllib import parse
from typing import Any

import aiohttp
import uvicorn
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import Cookie, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from linked_roles import LinkedRolesOAuth2, RoleConnection


load_dotenv()
app = FastAPI(
    title="Achievement Promotion with Steam - Discord",
    description="This API is used to verify that you have achievement of the game and give you a role.",
    version="1.0.0",
    openapi_url=None
)
client = LinkedRolesOAuth2(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    redirect_uri=f"{os.getenv('REDIRECT_URI')}/discord",
    token=os.getenv("BOT_TOKEN"),
    scopes=("identify", "role_connection_write"),
    state=os.getenv("COOKIE_SECRET")
)
fn = Fernet(os.getenv("ENCRYPT_KEY"))

def encrypt(text: str) -> str:
    return fn.encrypt(text.encode())

def decrypt(text: str) -> str:
    return fn.decrypt(text).decode()

async def async_list(values: list) -> Any:
    for value in values:
        yield value
        await asyncio.sleep(0)

@app.on_event('startup')
async def startup():
    await client.start()

@app.on_event('shutdown')
async def shutdown():
    await client.close()

@app.get('/verify')
async def link():
    steam_openid_url = "https://steamcommunity.com/openid/login"
    u = {
        'openid.ns': "http://specs.openid.net/auth/2.0",
        'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.mode': "checkid_setup",
        'openid.return_to': f"{os.getenv('REDIRECT_URI')}/steam",
        'openid.realm': os.getenv("DEFAULT_URI")
    }
    query_string = parse.urlencode(u)
    auth_url = steam_openid_url + "?" + query_string
    return RedirectResponse(auth_url)

@app.get('/callback/steam') 
async def setup(request: Request, response: Response):
    valid = await validate(request.query_params)
    if not valid:
        raise HTTPException(status_code=404, detail="We can't verify that you have Steam profile.")
    url = client.get_oauth_url()
    response.set_cookie(key="steam_id", value=encrypt(request.query_params.get("openid.claimed_id")), max_age=300)
    return RedirectResponse(url=url)

async def validate(data: dict):
    base = "https://steamcommunity.com/openid/login"
    params = {
        "openid.assoc_handle": data["openid.assoc_handle"],
        "openid.sig": data["openid.sig"],
        "openid.ns": data["openid.ns"],
        "openid.mode": "check_authentication"
    }
    data.update(params)
    data["openid.mode"] = "check_authentication"
    data["openid.signed"] = data["openid.signed"]

    session = aiohttp.ClientSession()
    r = await session.post(base, data=data)

    if "is_valid:true" in r.text:
        return True

    return False

@app.get('/callback/discord')
async def update_metadata(response: Response, code: str, steam_id: str = Cookie()):
    token = await client.get_access_token(code)
    user = await client.fetch_user(token)

    if user is None:
        raise HTTPException(status_code=404, detail="We can't verify that you have Discord profile.")
    
    steam_id = decrypt(steam_id)
    session = aiohttp.ClientSession()
    r = await session.get(f"http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid={os.getenv('STEAM_GAME_ID')}&key={os.getenv('STEAM_API_KEY')}&steamid={steam_id}&l=en")
    res = await r.json()
    data = res["playerstats"]
    if data["success"] is False:
        if data["error"] == "Profile is not public":
            raise HTTPException(status_code=403, detail="We can't verify that you have achievement because your profile is private.")
        else:
            raise HTTPException(status_code=500, detail=data["error"])

    abc = await session.get(f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={os.getenv('STEAM_API_KEY')}&steamids={steam_id}")
    abc = await abc.json()
    role = await user.fetch_role_connection()
    if role is None:
        role = RoleConnection(platform_name=f"Steam - {data['gameName']}", platform_username=abc["response"]["players"][0]["personaname"])
    success = 0
    total = len(data["achievements"])
    async for achieve in async_list(data["achievements"]):
        if achieve["achieved"] == 1:
            success += 1
        role.add_or_edit_metadata(key=achieve["apiname"], value=True if achieve["achieved"] == 1 else False)
    percentage = (success / total) * 100
    role.add_or_edit_metadata(key="percentage", value=percentage)
    if percentage == 100:
        role.add_or_edit_metadata(key="completed", value=True)
    await user.edit_role_connection(role)
    response.set_cookie(key="steam_id", value="", max_age=1)
    return "연동이 완료되었습니다! Discord로 돌아가세요."


uvicorn.run(app, host="0.0.0.0", port=4278)