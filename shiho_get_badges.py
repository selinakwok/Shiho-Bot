import os

import discord
import easyocr
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from dotenv import load_dotenv
from zipfile import ZipFile

load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents().all()
bot = commands.Bot(command_prefix='&', intents=intents)
reader = easyocr.Reader(['en'], gpu=False)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.command(name="get_badges")
async def get_badges(ctx, event: str, start_id, end_id):
    async with ctx.typing():
        start_message = bot.get_partial_messageable(start_id)
        end_message = bot.get_partial_messageable(end_id)
        channel = bot.get_channel(1029205688817307669)
        badges = [b async for b in channel.history(before=end_message, after=start_message)]
        pm = bot.get_partial_messageable(1029205688817307669)
        with ZipFile(event + ".zip", 'w') as zip_file:
            count = 0
            pts_list = []
            for b in badges:
                image_message = await pm.fetch_message(b.id)
                image = image_message.attachments[0]
                image = await image.read()
                result = reader.readtext(image)
                print(result)
                for t in result:
                    bbox = t[0]
                    if 820 <= bbox[1][0] <= 828 and 23 <= bbox[1][1] <= 31 and 820 <= bbox[2][0] <= 828 and 72 <= bbox[2][1] <= 79:
                        pts = t[1]
                        break
                if pts + "_4" in pts_list:
                    pts = pts + "_5"
                elif pts + "_3" in pts_list:
                    pts = pts + "_4"
                elif pts + "_2" in pts_list:
                    pts = pts + "_3"
                elif pts + "_1" in pts_list:
                    pts = pts + "_2"
                elif pts in pts_list:
                    pts = pts + "_1"
                pts_list.append(pts)
                zip_file.writestr(pts + ".png", image)
                count += 1
    await ctx.send("成功自動命名及下載" + str(count) + "張成績圖 <:ln_shiho_smile:1024352083173965857>")
    await ctx.send(file=discord.File(event + ".zip"))
    os.remove(event + ".zip")
    print("zip file sent")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error



bot.run(TOKEN)
