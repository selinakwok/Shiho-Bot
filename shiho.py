import io
import json
import os
import urllib.request

import PIL
import discord
import random
import requests
import aiohttp
import asyncio
import pytz
import pandas as pd
import datetime
# import easyocr
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands, tasks
from discord.ext.commands import CommandNotFound
from dotenv import load_dotenv
from io import BytesIO
import math
from zipfile import ZipFile
import cv2
import numpy as np

from cards import card

load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents().all()
bot = commands.Bot(command_prefix='&', intents=intents)
# reader = easyocr.Reader(['en'], gpu=False)
hktz = pytz.timezone("Etc/GMT-8")
pd.options.display.max_columns = None
pd.options.display.max_rows = None

bot.event_no = 0
bot.start_day = datetime.datetime.now(hktz)
bot.end_day = datetime.datetime.now(hktz)
bot.next_event = 1
bot.next_start = datetime.datetime.now(hktz)
bot.next_end = datetime.datetime.now(hktz)

bot.card_list_2 = []
bot.card_list_3 = []
bot.card_list_4 = []

char_unit = 'https://sekai-world.github.io/sekai-master-db-tc-diff/gameCharacterUnits.json'
res = urllib.request.urlopen(char_unit)
bot.characters = pd.read_json(res)
bot.characters = bot.characters[["id", "gameCharacterId", "unit"]]
bot.characters["img_path"] = ['ick', 'saki', 'hnm', 'shiho', 'mnr', 'hrk', 'airi', 'szk',
                              'khn', 'an', 'akt', 'toya', 'tks', 'emu', 'nene', 'rui',
                              'knd', 'mfy', 'ena', 'mzk', 'miku', 'rin', 'len', 'luka', 'meiko', 'kaito',
                              'miku', 'miku', 'miku', 'miku', 'miku',
                              'rin', 'rin', 'rin', 'rin', 'rin',
                              'len', 'len', 'len', 'len', 'len',
                              'luka', 'luka', 'luka', 'luka', 'luka',
                              'meiko', 'meiko', 'meiko', 'meiko', 'meiko',
                              'kaito', 'kaito', 'kaito', 'kaito', 'kaito']


@tasks.loop(hours=240, reconnect=True)  # refresh every 10 days
async def refresh_cards():
    now = datetime.datetime.now(hktz)
    url = 'https://raw.githubusercontent.com/Sekai-World/sekai-master-db-tc-diff/refs/heads/main/cards.json'
    res = urllib.request.urlopen(url)
    data = json.loads(res.read())
    card_list = []
    for i in data:
        card_list.append(card(i["assetbundleName"], i["cardRarityType"], i["attr"]))
        bot.card_list_2 = [x for x in card_list if x.rarity == "rarity_2"]
        bot.card_list_3 = [x for x in card_list if x.rarity == "rarity_3"]
        bot.card_list_4 = [x for x in card_list if x.rarity == "rarity_4"]
    channel = bot.get_channel(1007203228515057687)
    await channel.send(f"gacha card list refreshed <:ln_shiho_good:1011638119667343481> [{now.strftime('%d/%m %H:%M:%S')}]")


bot.cards_df = pd.DataFrame()
bot.events_df = pd.DataFrame()
bot.eventCards_df = pd.DataFrame()
bot.deckBonus_df = pd.DataFrame()
bot.worldLink_df = pd.DataFrame()


@tasks.loop(hours=120, reconnect=True)  # refresh every 5 days
async def update_df():
    now = datetime.datetime.now(hktz)
    channel = bot.get_channel(1007203228515057687)

    cards_url = 'https://sekai-world.github.io/sekai-master-db-diff/cards.json'
    res = urllib.request.urlopen(cards_url)
    bot.cards_df = pd.read_json(res)
    bot.cards_df = bot.cards_df[["id", "characterId", "cardRarityType", "attr", "supportUnit", "assetbundleName"]]

    events_jp = 'https://sekai-world.github.io/sekai-master-db-diff/events.json'
    res = urllib.request.urlopen(events_jp)
    events_df = pd.read_json(res)
    events_df = events_df[["id", "eventType", "name", "assetbundleName", "startAt", "aggregateAt", "unit"]]
    events_df["startAt"] = events_df["startAt"] / 1000
    events_df["aggregateAt"] = events_df["aggregateAt"] / 1000 + 1
    events_df = events_df.rename(columns={"name": "name_jp", "startAt": "start_jp", "aggregateAt": "end_jp"})

    events_tw = 'https://sekai-world.github.io/sekai-master-db-tc-diff/events.json'
    res = urllib.request.urlopen(events_tw)
    events_tw_df = pd.read_json(res)
    events_tw_df = events_tw_df[["id", "name", "startAt", "aggregateAt"]]
    events_tw_df["startAt"] = events_tw_df["startAt"] / 1000
    events_tw_df["aggregateAt"] = events_tw_df["aggregateAt"] / 1000 + 1
    events_tw_df = events_tw_df.rename(columns={"name": "name_tw", "startAt": "start_tw", "aggregateAt": "end_tw"})
    bot.events_df = pd.merge(events_df, events_tw_df, how="left", on="id")
    bot.events_df = bot.events_df.replace({np.nan: None})

    event_cards = 'https://sekai-world.github.io/sekai-master-db-diff/eventCards.json'
    res = urllib.request.urlopen(event_cards)
    bot.eventCards_df = pd.read_json(res)
    bot.eventCards_df = bot.eventCards_df[["eventId", "cardId", "bonusRate"]]

    deck_bonuses = 'https://sekai-world.github.io/sekai-master-db-diff/eventDeckBonuses.json'
    res = urllib.request.urlopen(deck_bonuses)
    bot.deckBonus_df = pd.read_json(res)
    bot.deckBonus_df = bot.deckBonus_df[bot.deckBonus_df["bonusRate"] == 50]
    bot.deckBonus_df = bot.deckBonus_df[["eventId", "gameCharacterUnitId", "cardAttr"]]

    wl_jp = 'https://sekai-world.github.io/sekai-master-db-diff/worldBlooms.json'
    res = urllib.request.urlopen(wl_jp)
    wl_jp = pd.read_json(res)
    wl_jp = wl_jp[["eventId", "gameCharacterId", "chapterNo", "chapterStartAt", "aggregateAt"]]
    wl_jp["chapterStartAt"] = wl_jp["chapterStartAt"] / 1000
    wl_jp["aggregateAt"] = wl_jp["aggregateAt"] / 1000 + 1
    wl_tc = 'https://sekai-world.github.io/sekai-master-db-tc-diff/worldBlooms.json'
    res = urllib.request.urlopen(wl_tc)
    wl_tc = pd.read_json(res)
    wl_tc = wl_tc[["eventId", "gameCharacterId", "chapterNo", "chapterStartAt", "aggregateAt"]]
    wl_tc["chapterStartAt"] = wl_tc["chapterStartAt"] / 1000
    wl_tc["aggregateAt"] = wl_tc["aggregateAt"] / 1000 + 1
    bot.worldLink_df = pd.merge(wl_jp, wl_tc, how="left", on=["eventId", "gameCharacterId", "chapterNo"],
                                suffixes=("_jp", "_tw"))

    await channel.send(f"All dataframes refreshed <:ln_shiho_good:1011638119667343481> [{now.strftime('%d/%m %H:%M:%S')}]")


def check_event_no(now_dt):
    response = urllib.request.urlopen("https://sekai-world.github.io/sekai-master-db-tc-diff/events.json")
    events = json.loads(response.read())
    events_times = [[e["id"], datetime.datetime.fromtimestamp(e["startAt"]/1000, hktz),
                     datetime.datetime.fromtimestamp((e["aggregateAt"])/1000+1, hktz)]
                    for e in events]
    low = 0
    high = len(events_times) - 1
    if now_dt < events_times[low][1]:
        return False
    if now_dt > events_times[high][1]:
        return events_times[high], False
    while low <= high:
        mid = (low + high) // 2
        if events_times[mid][1] <= now_dt < events_times[mid + 1][1]:
            return events_times[mid], events_times[mid + 1]
        elif now_dt > events_times[mid][1]:
            low = mid + 1
        else:
            high = mid - 1
    return False  # current datetime not found in events


@tasks.loop(time=datetime.time(4, 0, 0, tzinfo=hktz), reconnect=True)
async def check_event_change():  # check every day at 04:00
    print(f"check event change")
    now = datetime.datetime.now(hktz)
    if bot.next_start - datetime.timedelta(hours=15) <= now < bot.next_start:  # 00:00 <= now < 15:00
        channel = bot.get_channel(1007203228515057687)
        await channel.send(f"Event change activated [{now.strftime('%d/%m %H:%M:%S')}]")
        bot.event_no = bot.next_event
        bot.start_day = bot.next_start
        bot.end_day = bot.next_end
        bot.next_event += 1
        response = urllib.request.urlopen("https://sekai-world.github.io/sekai-master-db-tc-diff/events.json")
        events = json.loads(response.read())
        next_event = [e for e in events if e["id"] == bot.next_event][0]
        bot.next_start = datetime.datetime.fromtimestamp(next_event["startAt"]/1000, hktz)
        bot.next_end = datetime.datetime.fromtimestamp(next_event["aggregateAt"]/1000+1, hktz)
        await channel.send("Event change <:ln_saki_excited:1011509870081626162>\n"
                           f"Current event: {bot.event_no}\n"
                           f"- Event start: {bot.start_day.strftime('%m/%d %H:%M')}\n"
                           f"- Event end: {bot.end_day.strftime('%m/%d %H:%M')}\n"
                           f"Next event: {bot.next_event}\n" +
                           "- Event start: " + bot.next_start.strftime("%m/%d %H:%M") + "\n" +
                           "- Event end: " + bot.next_end.strftime("%m/%d %H:%M"))


@bot.event
async def on_ready():
    channel = bot.get_channel(1007203228515057687)
    print(f'We have logged in as {bot.user}')
    update_df.start()
    refresh_cards.start()
    now = datetime.datetime.now(hktz)
    curr_event, next_event = check_event_no(now)
    if curr_event:
        bot.event_no = curr_event[0]
        bot.start_day = curr_event[1]
        bot.end_day = curr_event[2]
        bot.next_event = bot.event_no + 1
        await channel.send(f"Current event: {bot.event_no}\n" +
                           "- Event start: " + bot.start_day.strftime("%m/%d %H:%M") + "\n" +
                           "- Event end: " + bot.end_day.strftime("%m/%d %H:%M"))
    if next_event:
        bot.next_start = next_event[1]
        bot.next_end = next_event[2]
        await channel.send(f"Next event: {bot.next_event}\n" +
                           "- Event start: " + bot.next_start.strftime("%m/%d %H:%M") + "\n" +
                           "- Event end: " + bot.next_end.strftime("%m/%d %H:%M"))
    else:
        await channel.send("<@598066719659130900> Failed to find current event <:ln_saki_weapon:1006929901745614859>")

    check_event_change.start()
    await channel.send("check_event_change started")


@bot.event
async def on_raw_reaction_add(payload):
    channel = bot.get_channel(1006460760081321985)
    if payload.channel_id != channel.id:
        return
    if payload.user_id != 1002412559632171081:
        guild_id = payload.guild_id
    else:
        return

    if payload.message_id == 1006464319287992380:  # add team roles
        e_VS = bot.get_emoji(1006937284760842282)
        e_LN = bot.get_emoji(1006937278687490188)
        e_25 = bot.get_emoji(1006937276711972974)
        e_VBS = bot.get_emoji(1006937282982449224)
        e_MMJ = bot.get_emoji(1006937280889507860)
        e_WS = bot.get_emoji(1006937286950277180)

        if payload.emoji == e_VS:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467284526710794)
            await payload.member.add_roles(role)
        elif payload.emoji == e_LN:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467353405571102)
            await payload.member.add_roles(role)
        elif payload.emoji == e_25:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467750299975680)
            await payload.member.add_roles(role)
        elif payload.emoji == e_VBS:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467540471521290)
            await payload.member.add_roles(role)
        elif payload.emoji == e_MMJ:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467430819827742)
            await payload.member.add_roles(role)
        elif payload.emoji == e_WS:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467660059512903)
            await payload.member.add_roles(role)
        elif payload.emoji.name == '🥕':
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1008611957277990983)
            await payload.member.add_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1009131452815908964:  # add VS roles
        e_miku = bot.get_emoji(1008743999441489991)
        e_luka = bot.get_emoji(1008743994542543008)
        e_rin = bot.get_emoji(1008744002461384824)
        e_len = bot.get_emoji(1008743991413588028)
        e_meiko = bot.get_emoji(1008743997134614708)
        e_kaito = bot.get_emoji(1008743988938948718)
        if payload.emoji == e_miku:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1008945487124103179)
            await payload.member.add_roles(role)
        elif payload.emoji == e_luka:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009029133927469096)
            await payload.member.add_roles(role)
        elif payload.emoji == e_rin:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009026490937118811)
            await payload.member.add_roles(role)
        elif payload.emoji == e_len:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009028009778495571)
            await payload.member.add_roles(role)
        elif payload.emoji == e_meiko:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009029762443907102)
            await payload.member.add_roles(role)
        elif payload.emoji == e_kaito:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009032280636936273)
            await payload.member.add_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1009124240613720164:  # add LN roles
        e_ick = bot.get_emoji(1008743962594525216)
        e_shiho = bot.get_emoji(1008743967808036894)
        e_hnm = bot.get_emoji(1008743960434450444)
        e_saki = bot.get_emoji(1008743964880412693)
        if payload.emoji == e_ick:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009106898995400805)
            await payload.member.add_roles(role)
        elif payload.emoji == e_shiho:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009108267546460321)
            await payload.member.add_roles(role)
        elif payload.emoji == e_hnm:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009107823621328973)
            await payload.member.add_roles(role)
        elif payload.emoji == e_saki:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009107495333154826)
            await payload.member.add_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1009125834063355944:  # add MMJ roles
        e_mnr = bot.get_emoji(1008743974871257149)
        e_hrk = bot.get_emoji(1008743972740542666)
        e_airi = bot.get_emoji(1008743970211364936)
        e_szk = bot.get_emoji(1008743977169715200)
        if payload.emoji == e_mnr:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009108754656145571)
            await payload.member.add_roles(role)
        elif payload.emoji == e_hrk:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009109149734420540)
            await payload.member.add_roles(role)
        elif payload.emoji == e_airi:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009110585851523222)
            await payload.member.add_roles(role)
        elif payload.emoji == e_szk:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009111185192407090)
            await payload.member.add_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1009125928317755442:  # add VBS roles
        e_khn = bot.get_emoji(1008743983972884541)
        e_an = bot.get_emoji(1008743981552775198)
        e_toya = bot.get_emoji(1008743986590130196)
        e_akt = bot.get_emoji(1008743979342377031)
        if payload.emoji == e_khn:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009111388414804038)
            await payload.member.add_roles(role)
        elif payload.emoji == e_an:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009111884189925568)
            await payload.member.add_roles(role)
        elif payload.emoji == e_toya:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009112780105859124)
            await payload.member.add_roles(role)
        elif payload.emoji == e_akt:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009112369177305138)
            await payload.member.add_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1009125956398624788:  # add WS roles
        e_tks = bot.get_emoji(1008744013345587220)
        e_nene = bot.get_emoji(1008744008136282112)
        e_rui = bot.get_emoji(1008744010787074059)
        e_emu = bot.get_emoji(1008744005074440212)
        if payload.emoji == e_tks:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009113246562795591)
            await payload.member.add_roles(role)
        elif payload.emoji == e_nene:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009116832621408306)
            await payload.member.add_roles(role)
        elif payload.emoji == e_rui:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009117278937284718)
            await payload.member.add_roles(role)
        elif payload.emoji == e_emu:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009116588735201331)
            await payload.member.add_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1009125987914629201:  # add 25 roles
        e_knd = bot.get_emoji(1008743953392222218)
        e_mfy = bot.get_emoji(1008743955946549409)
        e_mzk = bot.get_emoji(1008743958245028000)
        e_ena = bot.get_emoji(1008743950967906405)
        if payload.emoji == e_knd:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009117620525609072)
            await payload.member.add_roles(role)
        elif payload.emoji == e_mfy:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009117959177916476)
            await payload.member.add_roles(role)
        elif payload.emoji == e_mzk:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009118629926805656)
            await payload.member.add_roles(role)
        elif payload.emoji == e_ena:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009118300631990403)
            await payload.member.add_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1006518883068424252:  # add functional roles
        e_burn_energy = bot.get_emoji(1006486489506525294)
        e_emergency = bot.get_emoji(1006484430677876836)
        e_crystal = bot.get_emoji(1006937407431639041)
        e_note = bot.get_emoji(1006937420148768890)
        if payload.emoji == e_burn_energy:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006517648324055140)
            await payload.member.add_roles(role)
        elif payload.emoji == e_emergency:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006737042576773180)
            await payload.member.add_roles(role)
        elif payload.emoji == e_crystal:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009016057165533244)
            await payload.member.add_roles(role)
        elif payload.emoji == e_note:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009035513874874368)
            await payload.member.add_roles(role)
        elif payload.emoji.name == "🦐":
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009650094666162228)
            await payload.member.add_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1029720118328053781: # add reminder roles
        reminder_0000 = bot.get_emoji(1008600859854241853)
        reminder_2157 = bot.get_emoji(1006937417900642426)
        if payload.emoji == reminder_0000:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1029704053665570836)
            await payload.member.add_roles(role)
        elif payload.emoji == reminder_2157:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1029703649749893160)
            await payload.member.add_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1043345445637857321: # add 退車通知 role
        police = bot.get_emoji(1006480156258476042)
        if payload.emoji == police:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1043345953589055498)
            await payload.member.add_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)


@bot.event
async def on_raw_reaction_remove(payload):
    channel = bot.get_channel(1006460760081321985)
    if payload.channel_id != channel.id:
        return
    if payload.user_id != 1002412559632171081:
        guild_id = payload.guild_id
        guild = bot.get_guild(guild_id)
        member = guild.get_member(payload.user_id)
    else:
        return

    if payload.message_id == 1006464319287992380:  # remove team roles
        e_VS = bot.get_emoji(1006937284760842282)
        e_LN = bot.get_emoji(1006937278687490188)
        e_25 = bot.get_emoji(1006937276711972974)
        e_VBS = bot.get_emoji(1006937282982449224)
        e_MMJ = bot.get_emoji(1006937280889507860)
        e_WS = bot.get_emoji(1006937286950277180)
        if payload.emoji == e_VS:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467284526710794)
            await member.remove_roles(role)
        elif payload.emoji == e_LN:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467353405571102)
            await member.remove_roles(role)
        elif payload.emoji == e_25:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467750299975680)
            await member.remove_roles(role)
        elif payload.emoji == e_VBS:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467540471521290)
            await member.remove_roles(role)
        elif payload.emoji == e_MMJ:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467430819827742)
            await member.remove_roles(role)
        elif payload.emoji.name == "🥕":
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1008611957277990983)
            await member.remove_roles(role)
        elif payload.emoji == e_WS:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006467660059512903)
            await member.remove_roles(role)

    elif payload.message_id == 1009131452815908964:  # remove VS roles
        e_miku = bot.get_emoji(1008743999441489991)
        e_luka = bot.get_emoji(1008743994542543008)
        e_rin = bot.get_emoji(1008744002461384824)
        e_len = bot.get_emoji(1008743991413588028)
        e_meiko = bot.get_emoji(1008743997134614708)
        e_kaito = bot.get_emoji(1008743988938948718)
        if payload.emoji == e_miku:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1008945487124103179)
            await member.remove_roles(role)
        elif payload.emoji == e_luka:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009029133927469096)
            await member.remove_roles(role)
        elif payload.emoji == e_rin:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009026490937118811)
            await member.remove_roles(role)
        elif payload.emoji == e_len:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009028009778495571)
            await member.remove_roles(role)
        elif payload.emoji == e_meiko:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009029762443907102)
            await member.remove_roles(role)
        elif payload.emoji == e_kaito:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009032280636936273)
            await member.remove_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1009124240613720164:  # remove LN roles
        e_ick = bot.get_emoji(1008743962594525216)
        e_shiho = bot.get_emoji(1008743967808036894)
        e_hnm = bot.get_emoji(1008743960434450444)
        e_saki = bot.get_emoji(1008743964880412693)
        if payload.emoji == e_ick:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009106898995400805)
            await member.remove_roles(role)
        elif payload.emoji == e_shiho:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009108267546460321)
            await member.remove_roles(role)
        elif payload.emoji == e_hnm:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009107823621328973)
            await member.remove_roles(role)
        elif payload.emoji == e_saki:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009107495333154826)
            await member.remove_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1009125834063355944:  # remove MMJ roles
        e_mnr = bot.get_emoji(1008743974871257149)
        e_hrk = bot.get_emoji(1008743972740542666)
        e_airi = bot.get_emoji(1008743970211364936)
        e_szk = bot.get_emoji(1008743977169715200)
        if payload.emoji == e_mnr:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009108754656145571)
            await member.remove_roles(role)
        elif payload.emoji == e_hrk:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009109149734420540)
            await member.remove_roles(role)
        elif payload.emoji == e_airi:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009110585851523222)
            await member.remove_roles(role)
        elif payload.emoji == e_szk:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009111185192407090)
            await member.remove_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1009125928317755442:  # remove VBS roles
        e_khn = bot.get_emoji(1008743983972884541)
        e_an = bot.get_emoji(1008743981552775198)
        e_toya = bot.get_emoji(1008743986590130196)
        e_akt = bot.get_emoji(1008743979342377031)
        if payload.emoji == e_khn:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009111388414804038)
            await member.remove_roles(role)
        elif payload.emoji == e_an:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009111884189925568)
            await member.remove_roles(role)
        elif payload.emoji == e_toya:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009112780105859124)
            await member.remove_roles(role)
        elif payload.emoji == e_akt:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009112369177305138)
            await member.remove_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1009125956398624788:  # remove WS roles
        e_tks = bot.get_emoji(1008744013345587220)
        e_nene = bot.get_emoji(1008744008136282112)
        e_rui = bot.get_emoji(1008744010787074059)
        e_emu = bot.get_emoji(1008744005074440212)
        if payload.emoji == e_tks:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009113246562795591)
            await member.remove_roles(role)
        elif payload.emoji == e_nene:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009116832621408306)
            await member.remove_roles(role)
        elif payload.emoji == e_rui:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009117278937284718)
            await member.remove_roles(role)
        elif payload.emoji == e_emu:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009116588735201331)
            await member.remove_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1009125987914629201:  # remove 25 roles
        e_knd = bot.get_emoji(1008743953392222218)
        e_mfy = bot.get_emoji(1008743955946549409)
        e_mzk = bot.get_emoji(1008743958245028000)
        e_ena = bot.get_emoji(1008743950967906405)
        if payload.emoji == e_knd:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009117620525609072)
            await member.remove_roles(role)
        elif payload.emoji == e_mfy:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009117959177916476)
            await member.remove_roles(role)
        elif payload.emoji == e_mzk:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009118629926805656)
            await member.remove_roles(role)
        elif payload.emoji == e_ena:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009118300631990403)
            await member.remove_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1006518883068424252:  # remove functional roles
        e_burn_energy = bot.get_emoji(1006486489506525294)
        e_emergency = bot.get_emoji(1006484430677876836)
        e_crystal = bot.get_emoji(1006937407431639041)
        e_note = bot.get_emoji(1006937420148768890)
        if payload.emoji == e_burn_energy:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006517648324055140)
            await member.remove_roles(role)
        elif payload.emoji == e_emergency:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1006737042576773180)
            await member.remove_roles(role)
        elif payload.emoji == e_crystal:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009016057165533244)
            await member.remove_roles(role)
        elif payload.emoji == e_note:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009035513874874368)
            await member.remove_roles(role)
        elif payload.emoji.name == "🦐":
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1009650094666162228)
            await member.remove_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1029720118328053781:  # remove reminder roles
        reminder_0000 = bot.get_emoji(1008600859854241853)
        reminder_2157 = bot.get_emoji(1006937417900642426)
        if payload.emoji == reminder_0000:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1029704053665570836)
            await member.remove_roles(role)
        elif payload.emoji == reminder_2157:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1029703649749893160)
            await member.remove_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

    elif payload.message_id == 1043345445637857321: # remove 退車通知
        police = bot.get_emoji(1006480156258476042)
        if payload.emoji == police:
            role = discord.utils.get(bot.get_guild(guild_id).roles, id=1043345953589055498)
            await member.remove_roles(role)
        else:
            message = await bot.get_partial_messageable(payload.channel_id).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)


@bot.command(name="gacha",
             breif="抽卡",
             help="模擬游戲内抽卡")
async def gacha(ctx, number=1):
    if number > 10:
        await ctx.reply("每次最多十抽 <:ln_ick_eh:1008600861972369508>")
        return

    bg = Image.new("RGBA", (758, 323), (255, 255, 255))
    mask = Image.new("L", (128, 128), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, 128, 128), radius=8, fill=255)
    alpha = Image.new("L", (128, 128), 255)
    alpha.paste(mask)

    x = 25
    y = 25
    rarity_list = [2, 3, 4]
    rarity_2_count = 0
    async with ctx.typing():
        rarity_4_mention = ""
        for count in range(number):
            if rarity_2_count < 9:
                rarity = random.choices(rarity_list, weights=(88.5, 8.5, 3), k=1)[0]
            else:
                rarity = random.choices(rarity_list, weights=(0, 97, 3), k=1)[0]

            if rarity == 2:
                image_choice = random.choice(bot.card_list_2)
                frame = 'frame_2.png'
                rarity_2_count += 1
            elif rarity == 3:
                image_choice = random.choice(bot.card_list_3)
                frame = 'frame_3.png'
            else:
                image_choice = random.choice(bot.card_list_4)
                frame = 'frame_4.png'
                rarity_4_mention = "<@" + str(ctx.author.id) + ">"

            if image_choice.attribute == 'cool':
                attr = 'attr_cool.png'
            elif image_choice.attribute == 'cute':
                attr = 'attr_cute.png'
            elif image_choice.attribute == 'happy':
                attr = 'attr_happy.png'
            elif image_choice.attribute == 'mysterious':
                attr = 'attr_mysterious.png'
            else:
                attr = 'attr_pure.png'

            image_link = f"https://storage.sekai.best/sekai-jp-assets/thumbnail/chara_rip/" \
                         f"{image_choice.assetbundleName}_normal.webp"
            response = requests.get(image_link)
            card_image = Image.open(BytesIO(response.content)).convert("RGBA")

            frame_image = Image.open(frame).convert("RGBA")
            card_image.paste(frame_image, (0, 0), frame_image)

            attr_image = Image.open(attr).convert("RGBA")
            card_image.paste(attr_image, (1, 1), attr_image)

            card_image.putalpha(alpha)

            bg.paste(card_image, (x, y), card_image)

            if count == 4:
                x = 25
                y = 170
            else:
                x += 145

        bg.save('gacha_results.png')

    if rarity_4_mention != "":
        await ctx.reply("恭喜" + rarity_4_mention + "抽到4星 <:ln_shiho_good:1011638119667343481> ||別想逃||",
                        file=discord.File('gacha_results.png'))
    else:
        await ctx.reply(file=discord.File('gacha_results.png'), mention_author=False)

    card_image.close()
    bg.close()


door_font = ImageFont.truetype("Microsoft JhengHei Bold.ttf", 60)


@bot.command(name='door',
             brief='製作門的梗圖',
             help='製作門的梗圖')
async def door(ctx, name, character):
    if character not in ["ick", "shiho", "hnm", "saki",
                         "knd", "mfy", "ena", "mzk",
                         "khn", "an", "akt", "toya",
                         "mnr", "hrk", "airi", "szk",
                         "tks", "nene", "rui", "emu",
                         "miku", "luka", "rin", "len", "meiko", "kaito",
                         "25miku", "lnmiku", "vbsmiku", "mmjmiku", "wsmiku",
                         "nenerobot", "dd"]:
        await ctx.reply("角色名字不正確 <:ln_ick_eh:1008600861972369508>")
        return

    caption = name + "門"
    door_meme = Image.open('door.PNG')
    character_image = Image.open("characters/" + character + ".png")

    draw = ImageDraw.Draw(door_meme)
    w = draw.textlength(caption, font=door_font)
    draw.text(((550-w)/2, 430), caption, font=door_font, fill="black")

    door_meme.paste(character_image, (110, -25), character_image)
    door_meme.save("door_meme.png", "PNG")
    await ctx.send(file=discord.File('door_meme.png'))
    door_meme.close()


event_font = ImageFont.truetype("Microsoft JhengHei Bold.ttf", 40)
watermark_font = ImageFont.truetype("Microsoft JhengHei Bold.ttf", 15)

char_emotes = {1: "<:ln_ick:1008743962594525216>",
               2: "<:ln_saki:1008743964880412693>",
               3: "<:ln_hnm:1008743960434450444>",
               4: "<:ln_shiho:1008743967808036894>",
               5: "<:mmj_mnr:1008743974871257149>",
               6: "<:mmj_hrk:1008743972740542666>",
               7: "<:mmj_airi:1008743970211364936>",
               8: "<:mmj_szk:1008743977169715200>",
               9: "<:vbs_khn:1008743983972884541>",
               10: "<:vbs_an:1008743981552775198>",
               11: "<:vbs_akt:1008743979342377031>",
               12: "<:vbs_toya:1008743986590130196>",
               13: "<:ws_tks:1008744013345587220>",
               14: "<:ws_emu:1008744005074440212>",
               15: "<:ws_nene:1008744008136282112>",
               16: "<:ws_rui:1008744010787074059>",
               17: "<:25_knd:1008743953392222218>",
               18: "<:25_mfy:1008743955946549409>",
               19: "<:25_ena:1008743950967906405>",
               20: "<:25_mzk:1008743958245028000>",
               21: "<:vs_miku:1008743999441489991>",
               22: "<:vs_rin:1008744002461384824>",
               23: "<:vs_len:1008743991413588028>",
               24: "<:vs_luka:1008743994542543008>",
               25: "<:vs_meiko:1008743997134614708>",
               26: "<:vs_kaito:1008743988938948718>"}


@bot.command()
async def event(ctx, eventno: int, force=False):
    event = bot.events_df[bot.events_df["id"] == eventno]
    deckBonus = bot.deckBonus_df[bot.deckBonus_df["eventId"] == eventno]
    eventCards = bot.eventCards_df[bot.eventCards_df["eventId"] == eventno]

    server = "tc"
    e_name = event["name_tw"].values[0]
    if e_name:
        e_start = event["start_tw"].values[0]
        e_end = event["end_tw"].values[0]
    else:
        e_name = event["name_jp"].values[0]
        e_start = event["start_jp"].values[0]
        e_end = event["end_jp"].values[0]
        server = "jp"
    e_start = datetime.datetime.fromtimestamp(e_start, hktz)
    e_end = datetime.datetime.fromtimestamp(e_end, hktz)
    e_type = event["eventType"].values[0]
    if e_type == "marathon":
        e_type = "馬拉松"
    elif e_type == "world_bloom":
        e_type = "World link"
    else:
        e_type = "5v5"

    if e_type == "World link":
        e_data = event["unit"].values[0]
        if e_data == 'light_sound':
            unit_txt = 'Leo/need <:z_unit_ln:1006937278687490188>'
        elif e_data == 'idol':
            unit_txt = 'MORE MORE JUMP! <:z_unit_mmj:1006937280889507860>'
        elif e_data == 'street':
            unit_txt = 'Vivid BAD SQUAD <:z_unit_vbs:1006937282982449224>'
        elif e_data == 'theme_park':
            unit_txt = 'Wonderlands x Showtime <:z_unit_ws:1006937286950277180>'
        elif e_data == 'school_refusal':
            unit_txt = '25點，Nightcord見。 <:z_unit_25:1006937276711972974>'
        else:
            unit_txt = 'Virual Singer <:z_unit_vs:1006937284760842282>'
        wl_df = bot.worldLink_df[bot.worldLink_df["eventId"] == eventno]

    if server == 'tc':  # have tc data
        if e_type != "World link":
            await ctx.send(f"## {eventno}期 {e_name}\n"
                           f"{e_type} | {e_start.strftime('%d/%m/%Y')} - {e_end.strftime('%d/%m/%Y')} (台服)")
        else:
            ch_dates = ""
            count = 1
            for _, ch in wl_df.iterrows():
                gameCharId = ch['gameCharacterId']
                start = ch['chapterStartAt_tw']
                start = datetime.datetime.fromtimestamp(start, hktz)
                end = ch["aggregateAt_tw"]
                end = datetime.datetime.fromtimestamp(end, hktz)
                ch_dates = ch_dates + f"- Ch{count} {char_emotes[gameCharId]}: " \
                                      f"{start.strftime('%d/%m %H:%M')} - {end.strftime('%d/%m %H:%M')}\n"
                count += 1
            await ctx.send(f"## {eventno}期 {e_name}\n"
                           f"{e_type} | {e_start.strftime('%d/%m/%Y')} - {e_end.strftime('%d/%m/%Y')} (台服)\n"
                           f"團體: {unit_txt}\n"
                           f"{ch_dates}")
        if not force:
            if os.path.exists(f'event/event{eventno}_tc.png'):  # if made tc img: send img then return
                await ctx.send(file=discord.File(f"event/event{eventno}_tc.png"))
                return
            if eventno > bot.event_no:  # if search event is after current event - assets will only have jp
                if os.path.exists(f'event/event{eventno}_jp.png'):
                    await ctx.send(file=discord.File(f"event/event{eventno}_jp.png"))
                    return
    else:
        if e_type != "World link":
            await ctx.send(f"## {eventno}期 {e_name}\n"
                           f"{e_type} | {e_start.strftime('%d/%m/%Y')} - {e_end.strftime('%d/%m/%Y')} (日服)")
        else:
            ch_dates = ""
            count = 1
            for _, ch in wl_df.iterrows():
                gameCharId = ch['gameCharacterId']
                start = ch['chapterStartAt_jp']
                start = datetime.datetime.fromtimestamp(start, hktz)
                end = ch["aggregateAt_jp"]
                end = datetime.datetime.fromtimestamp(end, hktz)
                ch_dates = ch_dates + f"- Ch{count} {char_emotes[gameCharId]}: " \
                                      f"{start.strftime('%d/%m %H:%M')} - {end.strftime('%d/%m %H:%M')}\n"
                count += 1
            await ctx.send(f"## {eventno}期 {e_name}\n"
                           f"{e_type} | {e_start.strftime('%d/%m/%Y')} - {e_end.strftime('%d/%m/%Y')} (日服)\n"
                           f"團體: {unit_txt}\n"
                           f"{ch_dates}")
        if not force:
            if os.path.exists(f'event/event{eventno}_jp.png'):
                await ctx.send(file=discord.File(f"event/event{eventno}_jp.png"))
                return

    wait_msg = await ctx.send("-# 第一次生成圖片，請稍等片刻 <:ln_shiho_smile:1024352083173965857>")

    # ----- generate image -----

    async def get(url, session, index, group, results):
        async with session.get(url=url) as response:
            try:
                response.raise_for_status()  # Raise an error for bad responses
                resp = await response.read()
                results[group][index] = (resp, url)
            except aiohttp.client_exceptions.ClientResponseError:
                new_url = url.replace("_rip", "")
                async with session.get(url=new_url) as new_response:
                    try:
                        new_response.raise_for_status()
                        new_resp = await new_response.read()
                        results[group][index] = (new_resp, new_url)  # Store a tuple of (image data, url) in the results
                    except Exception:  # skip 2star cards
                        pass

    async def main(groups):
        results = {group: [None] * len(urls) for group, urls in groups.items()}  # Create a dictionary for results
        async with aiohttp.ClientSession() as session:
            tasks = []
            for group, urls in groups.items():
                for index, url in enumerate(urls):
                    tasks.append(get(url, session, index, group, results))
            await asyncio.gather(*tasks)

        # Open images using Pillow and keep track of URLs
        images_by_group = {}
        for group, data_list in results.items():
            images_by_group[group] = []
            for index, data in enumerate(data_list):
                if data is not None:
                    image_data, url = data  # Unpack the tuple
                    try:
                        image = Image.open(BytesIO(image_data)).convert("RGBA")
                        images_by_group[group].append((image, url))  # Store tuple of (image, url)
                    except PIL.UnidentifiedImageError:
                        new_url = url.replace("_rip", "")
                        res = requests.get(new_url)
                        image = Image.open(BytesIO(res.content)).convert("RGBA")
                        images_by_group[group].append((image, url))  # Store tuple of (image, url)
        return images_by_group  # Return the dictionary of opened images by group

    async with ctx.typing():
        bg = Image.new(mode="RGBA", size=(2000, 1920), color=(255, 255, 255, 0))

        urls = {"assets": [], "eventCards": [], "bonusCards": []}
        e_asset = event['assetbundleName'].values[0]
        urls["assets"] += [f'https://storage.sekai.best/sekai-tc-assets/home/banner/{e_asset}_rip/{e_asset}.webp',
                           f'https://storage.sekai.best/sekai-jp-assets/home/banner/{e_asset}_rip/{e_asset}.webp',
                           f'https://storage.sekai.best/sekai-tc-assets/honor/honor_bg_{e_asset[:-5]}_rip/degree_main.webp',
                           f'https://storage.sekai.best/sekai-jp-assets/honor/honor_bg_{e_asset[:-5]}_rip/degree_main.webp'
                           ]

        event_cards = eventCards['cardId'].values
        max_cid = 0
        for i in event_cards:
            card = bot.cards_df[bot.cards_df['id'] == i]
            card_asset = card['assetbundleName'].values[0]
            card_url = f"https://storage.sekai.best/sekai-jp-assets/thumbnail/chara_rip/{card_asset}_after_training.webp"
            urls["eventCards"].append(card_url)
            card_url = f"https://storage.sekai.best/sekai-jp-assets/thumbnail/chara_rip/{card_asset}_normal.webp"
            urls["eventCards"].append(card_url)
            if i > max_cid:
                max_cid = i

        if e_type != "World link":
            bonus_char_card_id = {}
            attr = deckBonus['cardAttr'].values[0]
            for cid in deckBonus['gameCharacterUnitId'].values:
                row = bot.characters[bot.characters['id'] == cid]
                gamecharid = row['gameCharacterId'].values[0]
                unit_data = row['unit'].values[0]
                if cid <= 20:  # ln/mmj/vbs/ws/25
                    char_cards = bot.cards_df[
                        (bot.cards_df['id'] <= max_cid) & (bot.cards_df['characterId'] == gamecharid) &
                        (bot.cards_df['attr'] == attr)]
                else:  # vs: filter unit
                    char_cards = bot.cards_df[
                        (bot.cards_df['id'] <= max_cid) & (bot.cards_df['characterId'] == gamecharid) &
                        (bot.cards_df['attr'] == attr) & (bot.cards_df['supportUnit'] == unit_data)]
                if not char_cards.empty:
                    bonus_char_card_id[cid] = []
                    for _, j in char_cards.iterrows():
                        card_id = j['id']
                        bonus_char_card_id[cid].append(card_id)
                        card = bot.cards_df[bot.cards_df['id'] == card_id]
                        card_asset = card['assetbundleName'].values[0]
                        card_url = f"https://storage.sekai.best/sekai-jp-assets/thumbnail/chara_rip/{card_asset}_after_training.webp"
                        urls["bonusCards"].append(card_url)
                        card_url = f"https://storage.sekai.best/sekai-jp-assets/thumbnail/chara_rip/{card_asset}_normal.webp"
                        urls["bonusCards"].append(card_url)

        images = await main(urls)

        if eventno > bot.event_no:
            im_server = "jp"
        else:
            im_server = "tc"
        assets_im = images["assets"]
        banner_im = [i[0] for i in assets_im if "/banner/" in i[1]]
        if banner_im:
            banner_im = banner_im[0]
            bg.paste(banner_im, (20, 20), banner_im)

        badge_im = [i[0] for i in assets_im if "/honor/" in i[1]]
        if badge_im:
            badge_im = badge_im[0]
            badge_im = badge_im.resize((badge_im.size[0] * 5 // 7, badge_im.size[1] * 5 // 7))
            if e_type != "World link":
                bg.paste(badge_im, (520, 20), badge_im)
            else:
                bg.paste(badge_im, (520, 50), badge_im)

        draw = ImageDraw.Draw(bg)
        if e_type != "World link":
            draw.text((530, 90), "加成屬性:", font=event_font, fill="black", stroke_width=2, stroke_fill='white')
            draw.text((530, 160), "加成角色:", font=event_font, fill="black", stroke_width=2, stroke_fill='white')

            attr = deckBonus['cardAttr'].values[0]
            attr_im = Image.open(f'attr_{attr}.png').resize((45, 45))
            bg.paste(attr_im, (725, 98), attr_im)

        chars = deckBonus['gameCharacterUnitId'].values.tolist()
        if len(chars) == 6:  # anniversary
            x = 725
            for c in chars:
                char = bot.characters[bot.characters['id'] == c]
                unit_data = char['unit'].values[0]
                if unit_data == 'light_sound':
                    unit = 'ln'
                elif unit_data == 'idol':
                    unit = 'mmj'
                elif unit_data == 'street':
                    unit = 'vbs'
                elif unit_data == 'theme_park':
                    unit = 'ws'
                elif unit_data == 'school_refusal':
                    unit = '25'
                unit_im = Image.open(f'char_unit/unit_{unit}.png')
                bbox = unit_im.getbbox()
                unit_im = unit_im.crop(bbox)
                bg.paste(unit_im, (x, 154), unit_im)
                bbox = unit_im.getbbox()
                x = x + (bbox[2] - bbox[0]) + 4
                char_path = char['img_path'].values[0]
                char_im = Image.open(f'characters/{char_path}.png')
                bbox = char_im.getbbox()
                char_im = char_im.crop(bbox)
                char_im = char_im.resize((char_im.size[0] // 3, char_im.size[1] // 3))
                bg.paste(char_im, (x, 154), char_im)
                bbox = char_im.getbbox()
                x = x + (bbox[2] - bbox[0]) + 20
            unit = 'mix'

        elif len(chars) != 5:  # 箱活
            x = 725
            for c in chars:
                char = bot.characters[bot.characters['id'] == c]
                if c <= 20:  # ln(1-4)/mmj(5-8)/vbs(9-12)/ws(13-16)/25(17-20)
                    char_path = char['img_path'].values[0]
                    char_im = Image.open(f'characters/{char_path}.png')
                    bbox = char_im.getbbox()
                    char_im = char_im.crop(bbox)
                    char_im = char_im.resize((char_im.size[0]//3, char_im.size[1]//3))
                    bbox = char_im.getbbox()
                    bg.paste(char_im, (x, 154), char_im)
                    x = x + (bbox[2] - bbox[0]) + 20
                else:
                    unit_data = char['unit'].values[0]
                    if unit_data == 'light_sound':
                        unit = 'ln'
                    elif unit_data == 'idol':
                        unit = 'mmj'
                    elif unit_data == 'street':
                        unit = 'vbs'
                    elif unit_data == 'theme_park':
                        unit = 'ws'
                    elif unit_data == 'school_refusal':
                        unit = '25'
                    unit_im = Image.open(f'char_unit/unit_{unit}.png')
                    bbox = unit_im.getbbox()
                    unit_im = unit_im.crop(bbox)
                    x += 5
                    bg.paste(unit_im, (x, 154), unit_im)
                    break
        else:  # 混活
            x = 725
            for c in chars:
                char = bot.characters[bot.characters['id'] == c]
                if c <= 20:  # ln(1-4)/mmj(5-8)/vbs(9-12)/ws(13-16)/25(17-20)
                    char_path = char['img_path'].values[0]
                    char_im = Image.open(f'characters/{char_path}.png')
                    bbox = char_im.getbbox()
                    char_im = char_im.crop(bbox)
                    char_im = char_im.resize((char_im.size[0] // 3, char_im.size[1] // 3))
                    bbox = char_im.getbbox()
                    bg.paste(char_im, (x, 154), char_im)
                    x = x + (bbox[2] - bbox[0]) + 20
                else:  # vs
                    unit_data = char['unit'].values[0]
                    if unit_data == 'light_sound':
                        unit = 'ln'
                    elif unit_data == 'idol':
                        unit = 'mmj'
                    elif unit_data == 'street':
                        unit = 'vbs'
                    elif unit_data == 'theme_park':
                        unit = 'ws'
                    elif unit_data == 'school_refusal':
                        unit = '25'
                    unit_im = Image.open(f'char_unit/unit_{unit}.png')
                    bbox = unit_im.getbbox()
                    unit_im = unit_im.crop(bbox)
                    bbox = unit_im.getbbox()
                    x += 15
                    bg.paste(unit_im, (x, 154), unit_im)
                    x = x + (bbox[2] - bbox[0]) + 6
                    char_path = char['img_path'].values[0]
                    char_im = Image.open(f'characters/{char_path}.png')
                    bbox = char_im.getbbox()
                    char_im = char_im.crop(bbox)
                    char_im = char_im.resize((char_im.size[0] // 3, char_im.size[1] // 3))
                    bg.paste(char_im, (x, 154), char_im)
            unit = 'mix'

        def card_info(card_id):
            card = bot.cards_df[bot.cards_df['id'] == card_id]
            card_asset = card['assetbundleName'].values[0]
            card_rarity = card['cardRarityType'].values[0]
            card_attr = card['attr'].values[0]
            return card_asset, card_rarity, card_attr

        draw.text((20, 250), "活動新卡:", font=event_font, fill="black", stroke_width=2, stroke_fill='white')
        x = 20
        max_cid = 0
        event_cards_im = images["eventCards"]
        for i in event_cards:
            assetbundleName, rarity, attr = card_info(i)
            card_im = [i[0] for i in event_cards_im if assetbundleName in i[1]]
            if card_im:
                card_im = card_im[0]
                if rarity == "rarity_2":
                    frame = 'frame_2.png'
                elif rarity == "rarity_3":
                    frame = 'frame_3.png'
                else:
                    frame = 'frame_4.png'
                frame_image = Image.open(frame).convert("RGBA")
                card_im.paste(frame_image, (0, 0), frame_image)

                card_attr = f"attr_{attr}.png"
                attr_image = Image.open(card_attr).convert("RGBA")
                card_im.paste(attr_image, (1, 1), attr_image)

                card_im = card_im.resize((110, 110))
                bg.paste(card_im, (x, 308), card_im)
                x += 120
                if i > max_cid:
                    max_cid = i

        if e_type != "World link":
            draw.text((20, 445), "同屬性同角色加成卡:", font=event_font, fill="black", stroke_width=2, stroke_fill='white')
            bonus_cards_im = images["bonusCards"]

            x = 20
            y = 503
            for char_id, card_id in bonus_char_card_id.items():
                for cid in card_id:
                    assetbundleName, rarity, attr = card_info(cid)
                    card_im = [i[0] for i in bonus_cards_im if assetbundleName in i[1]]
                    if card_im:
                        card_im = card_im[0]
                        if rarity == "rarity_2":
                            frame = 'frame_2.png'
                        elif rarity == "rarity_3":
                            frame = 'frame_3.png'
                        else:
                            frame = 'frame_4.png'
                        frame_image = Image.open(frame).convert("RGBA")
                        card_im.paste(frame_image, (0, 0), frame_image)

                        card_attr = f"attr_{card['attr'].values[0]}.png"
                        attr_image = Image.open(card_attr).convert("RGBA")
                        card_im.paste(attr_image, (1, 1), attr_image)

                        card_im = card_im.resize((110, 110))
                        bg.paste(card_im, (x, y), card_im)
                        x += 120
                y += 135
                x = 20

        if e_type == "World link":
            e_data = event["unit"].values[0]
            if e_data == 'light_sound':
                unit = 'ln'
            elif e_data == 'idol':
                unit = 'mmj'
            elif e_data == 'street':
                unit = 'vbs'
            elif e_data == 'theme_park':
                unit = 'ws'
            elif e_data == 'school_refusal':
                unit = '25'
            else:
                unit = 'mix'

        bg_bbox = bg.getbbox()
        h = bg_bbox[3] + 20
        w = h*2
        final = Image.open(f'background/bg_{unit}.png').resize((w, h))
        final.paste(bg, (0, 0), bg)
        if e_type != 'World link':
            final = final.crop((0, 0, bg_bbox[2] + 25, h))
        else:
            final = final.crop((0, 0, bg_bbox[2] + 20, h))

        draw = ImageDraw.Draw(final)
        draw.text((bg_bbox[2] - 230, 20), "Discord 日野森志步bot @sk0416", font=watermark_font, fill=(0, 0, 0, 150),
                  stroke_width=1, stroke_fill=(255, 255, 255, 180))

        final.save(f"event/event{eventno}_{im_server}.png", "PNG")

    await wait_msg.delete()
    await ctx.send(file=discord.File(f"event/event{eventno}_{im_server}.png"))


@bot.command()
async def badges(ctx, eventno: int):
    event = bot.events_df[bot.events_df["id"] == eventno]
    server = "tc"
    e_name = event["name_tw"].values[0]
    if not e_name:
        server = "jp"
    if server == "tc":
        if os.path.exists(f"badges/event{eventno}_badges_tc.png"):
            await ctx.send(file=discord.File(f"badges/event{eventno}_badges_tc.png"))
            return
    else:
        if os.path.exists(f"badges/event{eventno}_badges_jp.png"):
            await ctx.send(file=discord.File(f"badges/event{eventno}_badges_jp.png"))
            return

    wait_msg = await ctx.send("-# 第一次生成圖片，請稍等片刻 <:ln_shiho_smile:1024352083173965857>")
    async with ctx.typing():
        e_asset = event['assetbundleName'].values[0]
        try:
            badge = f'https://storage.sekai.best/sekai-{server}-assets/honor/honor_bg_{e_asset[:-5]}_rip/degree_main.webp'
            response = requests.get(badge)
            badge_im = Image.open(BytesIO(response.content)).convert("RGBA")
        except PIL.UnidentifiedImageError:
            badge = f'https://storage.sekai.best/sekai-{server}-assets/honor/honor_bg_{e_asset[:-5]}/degree_main.webp'
            response = requests.get(badge)
            badge_im = Image.open(BytesIO(response.content)).convert("RGBA")
        frame = Image.open("badges/frame.png").convert("RGBA")
        badge_im.paste(frame, (0, 0), frame)
        if eventno < 108:
            ranks = [1, 2, 3, 10]
            t10_star = 'nostar'
        else:
            ranks = list(range(1, 11))
            t10_star = 'star'
        h = 80*len(ranks) + 10*(len(ranks)-1) + 30  # badge h*num b + gap between b*(num b - 1) + top bottom pad 15
        bg = Image.new(mode="RGBA", size=(410, h), color=(255, 255, 255, 0))
        y = 15
        for i in ranks:
            badge_new = badge_im.copy()
            if i != 10:
                rank = Image.open(f"badges/rank/rank_{i}.png")
            else:
                rank = Image.open(f"badges/rank/rank_{i}_{t10_star}.png")
            badge_new.paste(rank, (200, 0), rank)
            bg.paste(badge_new, (15, y), badge_new)
            y += 90  # 80 + 10
        bg.save(f"badges/event{eventno}_badges_{server}.png", "PNG")

    await wait_msg.delete()
    await ctx.send(file=discord.File(f"badges/event{eventno}_badges_{server}.png"))


@bot.command(name='resize', hidden=True)
async def resize(ctx):
    list = ['attr_cool.png', 'attr_cute.png', 'attr_happy.png', 'attr_mysterious.png', 'attr_pure.png']
    for im in list:
        new = Image.open(im)
        new = new.resize((30, 30))
        new.save(im)
        print("done")


@bot.event
async def on_message(message):
    if message.channel.id != 1009700280285286411:
        await bot.process_commands(message)
        return
    if not message.attachments:
        await bot.process_commands(message)
        return

    for attachment in message.attachments:
        url = attachment.url
        resp = requests.get(url, stream=True).raw
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        org_image = image
        # img_blur = cv2.GaussianBlur(org_image, (5, 5), 0, 0)
        gray = cv2.cvtColor(org_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 200)
        """result = org_image.copy()
        result[edges != 0] = (0, 255, 0)
        cv2.imshow("result", result)
        cv2.waitKey(0)"""
        contours, hierarchy = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
        bbox = sorted_contours[0]
        x, y, w, h = cv2.boundingRect(bbox)
        # print(f"x={x}, y={y}, w={w}, h={h}")
        edge_w = math.floor(h * 0.048)
        cropped_contour = org_image[y-edge_w: y+h+edge_w, x-edge_w: x+w+edge_w]
        image_name = "result.png"
        cv2.imwrite(image_name, cropped_contour)

        """sorted_contours = [sorted_contours[0]]
        for (i, c) in enumerate(sorted_contours):
            x, y, w, h = cv2.boundingRect(c)
            print(f"x={x}, y={y}, w={w}, h={h}")
            cropped_contour = org_image[y-5:y+h+5, x-5:x+w+5]
            image_name = "result.png"
            cv2.imwrite(image_name, cropped_contour)"""

        cv2.destroyAllWindows()

        im_transparent = Image.open("result.png")
        im_transparent = im_transparent.resize((1148, 114))
        im_transparent.convert("RGBA")

        mask = Image.new("L", (1148, 114), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, 1148, 114), radius=20, fill=255)
        alpha = Image.new("L", (1148, 114), 255)
        alpha.paste(mask)

        im_transparent.putalpha(alpha)

        im_transparent.save("result_transparent.png")
        send_channel = bot.get_channel(1029205688817307669)
        await send_channel.send(file=discord.File("result_transparent.png"))
        im_transparent.close()
        mask.close()
        alpha.close()

    print("result images edited and sent")

    await bot.process_commands(message)


@bot.command(name="send", hidden=True)
async def send(ctx):
    """
    reminder_emojis = [ "<:0_tofukakin2:1008600859854241853>", "<:z_livebonus:1006937417900642426>"]
    reminder_message = await ctx.send(
        "按反應領取提醒身分組：\n"
        "<:0_tofukakin2:1008600859854241853> 00:00提醒你打挑戰、買體力包\n"
        "<:z_livebonus:1006937417900642426> 21:57提醒你要在消體房報班"
    )
    bot.reminder_message_id = reminder_message.id
    for i in range(2):
        await reminder_message.add_reaction(reminder_emojis[i])
    """

    reminder_emojis = ["<:25_knd_police:1006480156258476042>"]
    reminder_message = await ctx.send(
        "按反應領取 <#1043337218367955055> 身分組：\n"
        "<:25_knd_police:1006480156258476042> 有人退掉你開的消體車時會@你")
    bot.reminder_message_id = reminder_message.id
    for i in range(1):
        await reminder_message.add_reaction(reminder_emojis[i])


@bot.command(name='logo',
             brief='發出活動徽標',
             help='發出指定活動的徽標')
async def logo(ctx, event):
    events_url = 'https://sekai-world.github.io/sekai-master-db-tc-diff/events.json'
    events = urllib.request.urlopen(events_url)
    events_json = json.loads(events.read())
    for e in events_json:
        if e["id"] == int(event):
            assetBundleName = e["assetbundleName"]
            break

    try:
        logo_url = "https://storage.sekai.best/sekai-tc-assets/event/" + assetBundleName + "/logo_rip/logo.webp"
        logo_req = requests.get(logo_url)
        im = Image.open(BytesIO(logo_req.content))
    except PIL.UnidentifiedImageError:
        logo_url = "https://storage.sekai.best/sekai-tc-assets/event/" + assetBundleName + "/logo/logo.webp"
        logo_req = requests.get(logo_url)
        im = Image.open(BytesIO(logo_req.content))
    im.save("logo.png", "png")

    await ctx.send(file=discord.File("logo.png"))
    os.remove("logo.png")


@bot.command(name="cards")
async def cards(ctx, event):
    eventcards_url = "https://sekai-world.github.io/sekai-master-db-tc-diff/eventCards.json"
    eventcards = urllib.request.urlopen(eventcards_url)
    eventcards_json = json.loads(eventcards.read())
    card_ids = []
    flag = "n"
    for c in eventcards_json:
        if c["eventId"] == int(event):
            card_ids.append(c["cardId"])
            flag = "y"
        elif flag == "y":
            break

    all_cards = urllib.request.urlopen("https://sekai-world.github.io/sekai-master-db-tc-diff/cards.json")
    cards_json = json.loads(all_cards.read())
    for c in cards_json:
        if card_ids:
            if c["id"] in card_ids:
                if c["cardRarityType"] != "rarity_2":
                    name = c["assetbundleName"]
                    # https://storage.sekai.best/sekai-jp-assets/character/member/res019_no034/card_after_training.webp
                    try:
                        card_url = "https://storage.sekai.best/sekai-jp-assets/character/member/" + name + "_rip/card_normal.webp"
                        card_req = requests.get(card_url)
                        im = Image.open(BytesIO(card_req.content))
                    except PIL.UnidentifiedImageError:
                        card_url = "https://storage.sekai.best/sekai-jp-assets/character/member/" + name + "/card_normal.webp"
                        card_req = requests.get(card_url)
                        im = Image.open(BytesIO(card_req.content))
                    im.save("eventcard.png", "png")
                    await ctx.send(file=discord.File("eventcard.png"))
                    try:
                        card_url = "https://storage.sekai.best/sekai-tc-assets/character/member/" + name + "_rip/card_after_training.webp"
                        card_req = requests.get(card_url)
                        im = Image.open(BytesIO(card_req.content))
                    except PIL.UnidentifiedImageError:
                        card_url = "https://storage.sekai.best/sekai-tc-assets/character/member/" + name + "/card_after_training.webp"
                        card_req = requests.get(card_url)
                        im = Image.open(BytesIO(card_req.content))
                    im.save("eventcard.png", "png")
                    await ctx.send(file=discord.File("eventcard.png"))
                card_ids.remove(c["id"])
    os.remove("eventcard.png")


@bot.command(name="assets")
async def assets(ctx, event: str):
    async with ctx.typing():
        with ZipFile(event + "_assets.zip", 'w') as zip_file:
            # logo
            events_url = 'https://sekai-world.github.io/sekai-master-db-tc-diff/events.json'
            events = urllib.request.urlopen(events_url)
            events_json = json.loads(events.read())
            for e in events_json:
                if e["id"] == int(event):
                    assetBundleName = e["assetbundleName"]
                    break
            logo_url = "https://storage.sekai.best/sekai-tc-assets/event/" + assetBundleName + "/logo_rip/logo.webp"
            logo_req = requests.get(logo_url)
            logo_im = Image.open(BytesIO(logo_req.content))
            file_object = io.BytesIO()
            logo_im.save(file_object, "PNG")
            logo_im.close()
            zip_file.writestr("logo.png", file_object.getvalue())

            # cards
            eventcards_url = "https://sekai-world.github.io/sekai-master-db-tc-diff/eventCards.json"
            eventcards = urllib.request.urlopen(eventcards_url)
            eventcards_json = json.loads(eventcards.read())
            card_ids = []
            flag = "n"
            for c in eventcards_json:
                if c["eventId"] == int(event):
                    card_ids.append(c["cardId"])
                    flag = "y"
                elif flag == "y":
                    break

            all_cards = urllib.request.urlopen("https://sekai-world.github.io/sekai-master-db-tc-diff/cards.json")
            cards_json = json.loads(all_cards.read())
            for c in cards_json:
                if card_ids:
                    if c["id"] in card_ids:
                        if c["cardRarityType"] != "rarity_2":
                            name = c["assetbundleName"]
                            card_url = "https://storage.sekai.best/sekai-tc-assets/character/member/" + name + "_rip/card_normal.webp"
                            card_req = requests.get(card_url)
                            im = Image.open(BytesIO(card_req.content))
                            file_object = io.BytesIO()
                            im.save(file_object, "PNG")
                            im.close()
                            zip_file.writestr(f"card{c['id']}.png", file_object.getvalue())
                            card_url = "https://storage.sekai.best/sekai-tc-assets/character/member/" + name + "_rip/card_after_training.webp"
                            card_req = requests.get(card_url)
                            im = Image.open(BytesIO(card_req.content))
                            file_object = io.BytesIO()
                            im.save(file_object, "PNG")
                            im.close()
                            zip_file.writestr(f"card{c['id']}_trained.png", file_object.getvalue())
                        card_ids.remove(c["id"])
        await ctx.send(file=discord.File(event + "_assets.zip"))
    os.remove(event + "_assets.zip")


@bot.command(name="add_role", hidden=True)
async def add_role(ctx, uid: int, name, colour, image: int):
    if 1006476907367370824 not in [r.id for r in ctx.author.roles]:
        return
    async with ctx.typing():
        guild = bot.get_guild(1006236899570110614)
        colour = discord.Colour.from_str(colour)

        # image/emoji
        try:
            im_message = await bot.get_channel(1024326209066254356).fetch_message(image)
        except discord.errors.NotFound:
            try:
                im_message = await bot.get_channel(1007203228515057687).fetch_message(image)
            except discord.errors.NotFound:
                try:
                    im_message = await bot.get_channel(1007216201258238033).fetch_message(image)
                except discord.errors.NotFound:
                    await ctx.send("Message not found")
                    return
        if im_message.attachments:
            im = im_message.attachments[0]
            im_bytes = await im.read()
            print(f"image size: {im.size}")
            if im.size > 2048000:
                print("file too big, compressing now")
                resize_im = Image.open(io.BytesIO(im_bytes))
                max_size = (1000, 1000)
                resize_im.thumbnail(max_size)
                byte_arr = io.BytesIO()
                resize_im.save(byte_arr, format="PNG")
                byte_arr.seek(0)
                im_bytes = byte_arr.getvalue()
        elif "https://media.discordapp.net/attachments" in im_message.content:
            m_start = im_message.content.find("https:")
            m_end = im_message.content.find(".png")
            im_url = im_message.content[m_start:m_end + 4]
            print(f"Media url: {im_url}")
            im_bytes = requests.get(im_url).content
        else:
            print(im_message.content)
            m_start = im_message.content.find("<:")
            m_end = im_message.content.find(">")
            emoji_id = im_message.content[m_start:m_end].split(":")[2]
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
            print(emoji_url)
            im_bytes = requests.get(emoji_url).content

        new_role = await guild.create_role(name=name, colour=colour, display_icon=im_bytes)
        total_roles = await guild.fetch_roles()
        await new_role.edit(position=len(total_roles) - 30)
        user = guild.get_member(uid)
        await user.add_roles(new_role)
    await ctx.send("New role added <:ln_shiho_good:1011638119667343481>")


@bot.command(name="edit_role", hidden=True)
async def edit_role(ctx, old_roleId: int, name, colour, image: int):
    if 1006476907367370824 not in [r.id for r in ctx.author.roles]:
        return
    async with ctx.typing():
        guild = bot.get_guild(1006236899570110614)
        old_role = guild.get_role(old_roleId)
        colour = discord.Colour.from_str(colour)

        # image
        try:
            im_message = await bot.get_channel(1024326209066254356).fetch_message(image)
        except discord.errors.NotFound:
            try:
                im_message = await bot.get_channel(1007203228515057687).fetch_message(image)
            except discord.errors.NotFound:
                try:
                    im_message = await bot.get_channel(1007216201258238033).fetch_message(image)
                except discord.errors.NotFound:
                    await ctx.send("Message with image not found")
                    return
        if im_message.attachments:
            im = im_message.attachments[0]
            im_bytes = await im.read()
            print(f"image size: {im.size}")
            if im.size > 2048000:
                print("file too big, compressing now")
                resize_im = Image.open(io.BytesIO(im_bytes))
                max_size = (1000, 1000)
                resize_im.thumbnail(max_size)
                byte_arr = io.BytesIO()
                resize_im.save(byte_arr, format="PNG")
                byte_arr.seek(0)
                im_bytes = byte_arr.getvalue()
        elif "https://media.discordapp.net/attachments" in im_message.content:
            m_start = im_message.content.find("https:")
            m_end = im_message.content.find(".png")
            im_url = im_message.content[m_start:m_end + 4]
            print(f"Media url: {im_url}")
            im_bytes = requests.get(im_url).content
        else:
            print(im_message.content)
            m_start = im_message.content.find("<:")
            m_end = im_message.content.find(">")
            emoji_id = im_message.content[m_start:m_end].split(":")[2]
            emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
            print(emoji_url)
            im_bytes = requests.get(emoji_url).content

        await old_role.edit(name=name, colour=colour, display_icon=im_bytes)
    await ctx.send("Role successfully edited <:ln_shiho_good:1011638119667343481>")


'''
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
            for b in badges:
                image_message = await pm.fetch_message(b.id)
                image = image_message.attachments[0]
                image = await image.read()
                result = reader.readtext(image)
                for t in result:
                    bbox = t[0]
                    if 820 <= bbox[1][0] <= 828 and 25 <= bbox[1][1] <= 31 and 820 <= bbox[2][0] <= 828 and 72 <= bbox[2][1] <= 78:
                        pts = t[1]
                        break
                zip_file.writestr(pts + ".png", image)
                count += 1
    await ctx.send("成功自動命名及下載" + str(count) + "張成績圖 <:ln_shiho_smile:1024352083173965857>")
    await ctx.send(file=discord.File(event + ".zip"))
    os.remove(event + ".zip")
'''


@bot.command(help="志步的指令介紹",
             brief="指令介紹")
async def shiho(ctx, subset='all'):
    if subset == 'all':
        embed = discord.Embed(title="__志步指令表__",
                              description="日野森志步bot由SK所寫，主要提供娛樂、身分組和自動剪輯成績圖片的功能"
                                          "\n\n**&door <name> <character>**\n製作門的梗圖"
                                          "\ncharacter: 角色讀音有3個音則會用短寫，其他的就用全寫"
                                          "\n(例如 honami: hnm，shiho: shiho)"
                                          "\n\n**&gacha [number=1]**\n模擬游戲内抽卡\nnumber=10會保底一張3星"
                                          "\n\n**&event <event> [force=False]**\n查看指定活動的資訊和加成卡圖"
                                          "\nforce: 强行重新生成並更新原有圖檔，用來檢查有沒有更新了的台服圖檔 (默認不更新)"
                                          "\n\n**&badges <event>**\n查看指定活動T1-T10的牌子"
                                          "\n\n**&logo <event>**\n發出指定活動的徽標"
                                          "\n\n**&cards <event>**\n發出指定活動的3、4星卡片(特訓前後)"
                                          "\n\n**&assets <event>**\n發出存有指定活動的徽標和3、4星卡的zip file"
                                          "\n\n**&get_badges <event> <start_id> <end_id>**\n自動根據活動分數命名然後下載該活動的所有成績圖"
                                          "\n注意: 此指令必須要local run才能使用，有需要用請告訴SK，否則無法使用"
                                          "\nstart_id: 第一張要下載的成績圖前一個信息的id"
                                          "\nend_id: 最後一張要下載的成績圖之後一個信息的id"
                                          "\n\n**&add_role <uid> <name> <colour> <im_message_id>**\n管理專用: 為指定成員增加新身分組"
                                          "\nuid: 成員dc id"
                                          "\nname: 新身分組的稱號"
                                          "\ncolour: 格式為#xxxxxx (hex)"
                                          "\nim_message_id: 發送身分組圖片/表符的信息的id"
                                          "\n\n**&edit_role <old_role_id> <name> <colour> <im_message_id>**\n管理專用: 更改指定身分組"
                                          "\nold_role_id: 需要更改的身分組的id"
                                          "\nname, colour, im_message_id: 同上"
                                          "\n\n**&shiho [subset=all]**\n顯示此指令介紹，指令表會定期更新"
                                          "\nsubset: all(所有指令) | func(實用) | play(娛樂) | mod(管理專用)\n** **",
                              colour=0xadf252)
        embed.set_footer(text="最後更新: 16/1/2025")
    elif subset == "func":
        embed = discord.Embed(title="__志步指令表 (實用)__",
                              description="日野森志步bot由SK所寫，主要提供娛樂、身分組和自動剪輯成績圖片的功能"
                                          "\n\n**&event <event> [force=False]**\n查看指定活動的資訊和加成卡圖"
                                          "\nforce: 强行重新生成並更新原有圖檔，用來檢查有沒有更新了的台服圖檔 (默認不更新)"
                                          "\n\n**&badges <event>**\n查看指定活動T1-T10的牌子"
                                          "\n\n**&logo <event>**\n發出指定活動的徽標"
                                          "\n\n**&cards <event>**\n發出指定活動的3、4星卡片(特訓前後)"
                                          "\n\n**&assets <event>**\n發出存有指定活動的徽標和3、4星卡的zip file"
                                          "\n\n**&get_badges <event> <start_id> <end_id>**\n自動根據活動分數命名然後下載該活動的所有成績圖"
                                          "\n注意: 此指令必須要local run才能使用，有需要用請告訴SK，否則無法使用"
                                          "\nstart_id: 第一張要下載的成績圖前一個信息的id"
                                          "\nend_id: 最後一張要下載的成績圖之後一個信息的id"
                                          "\n\n**&shiho [subset=all]**\n顯示此指令介紹，指令表會定期更新"
                                          "\nsubset: all(所有指令) | func(實用) | play(娛樂) | mod(管理專用)\n** **",
                              colour=0xadf252)
        embed.set_footer(text="最後更新: 16/1/2025")
    elif subset == "play":
        embed = discord.Embed(title="__志步指令表 (娛樂)__",
                              description="日野森志步bot由SK所寫，主要提供娛樂、身分組和自動剪輯成績圖片的功能"
                                          "\n\n**&door <name> <character>**\n製作門的梗圖"
                                          "\ncharacter: 角色讀音有3個音則會用短寫，其他的就用全寫"
                                          "\n(例如 honami: hnm，shiho: shiho)\n** **",
                              colour=0xadf252)
        embed.set_footer(text="最後更新: 6/1/2025")
    elif subset == "mod":
        embed = discord.Embed(title="__志步指令表 (管理專用)__",
                              description="日野森志步bot由SK所寫，主要提供娛樂、身分組和自動剪輯成績圖片的功能"
                                          "\n\n**&add_role <uid> <name> <colour> <im_message_id>**\n管理專用: 為指定成員增加新身分組"
                                          "\nuid: 成員dc id"
                                          "\nname: 新身分組的稱號"
                                          "\ncolour: 格式為#xxxxxx (hex)"
                                          "\nim_message_id: 發送身分組圖片/表符的信息的id"
                                          "\n\n**&edit_role <old_role_id> <name> <colour> <im_message_id>**\n管理專用: 更改指定身分組"
                                          "\nold_role_id: 需要更改的身分組的id"
                                          "\nname, colour, im_message_id: 同上\n** **",
                              colour=0xadf252)
        embed.set_footer(text="最後更新: 6/1/2025")
    else:
        await ctx.send("指令格式不正確，subset = all | func | play | mod")
        return
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error


bot.run(TOKEN)
