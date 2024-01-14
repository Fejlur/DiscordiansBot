import coc
import asyncio
import json
import logging
import logging.handlers
import random

import discord
from discord.ext import commands

with open("credentials.json") as creds:
    credentials = json.load(creds)

class Bot(commands.Bot):
    def __init__(self):
        self.coc_client = coc.EventsClient()
        self.war_logs_channel_id = 1193549391080980561

        super().__init__(command_prefix=".", intents=discord.Intents.all())

    async def on_ready(self):
        logging.info(f"logged in as {self.user.name}")

    async def on_command_error(self, ctx, error):
        await ctx.send(embed=discord.Embed(colour=0xa83232, title="❌ Not found"))
        logging.critical(error)

bot = Bot()

@bot.event
async def on_ready():
    logging.info(f"logged in as {bot.user.name}")

@bot.command(name="ping")
async def _ping(ctx):
    await ctx.send("pong")

@bot.command(name="echo")
async def _echo(ctx, *args):
    ret = " ".join(args)
    await ctx.send(ret)

@bot.command(name="warinfo")
async def _warinfo(ctx):
    war = await bot.coc_client.get_clan_war(credentials["clan_tag"])
    await ctx.send(f"{war.state}, {war.status}")

@bot.command(name="lastwarinfo")
@commands.is_owner()
async def _lastwarinfo(ctx):
    warlog = await ctx.bot.coc_client.get_war_log(credentials["clan_tag"], limit=1)
    war = warlog[0]
    clan1 = war.clan
    clan2 = war.opponent
    result = war.result

    e = discord.Embed(title="Last war", description=f"**{clan1.name}** | {clan1.tag} vs **{clan2.name}** {clan2.tag}")
    e.add_field(name=f"Result: {result}", value=f"{clan1.name} ⭐{clan1.stars}/{clan1.max_stars} | {clan2.name} ⭐{clan2.stars}/{clan2.max_stars}", inline=False)

    await ctx.send(embed=e)

@bot.command(name="player")
async def _player(ctx, tag: str):
    player = await ctx.bot.coc_client.get_player(tag)
    e = discord.Embed(title="Player Info", description=tag)
    e.add_field(name="Player", value="", inline=False)
    e.add_field(name="", value=f"**nick:** {player.name}", inline=False)
    e.add_field(name="IP:",
                value=f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}",
                inline=False)
    #print(type(player.clan), type(player))
    if player.clan is not None:
        e.add_field(name="Clan", value="", inline=False)
        e.add_field(name="", value=f"**rank:** {player.role}", inline=False)
        e.add_field(name="", value=f"**donations g/r:** {player.donations} / {player.received}")

    await ctx.send(embed=e)

@coc.ClanEvents.member_donations()
async def coc_member_donation(old_member, new_member):
    ch = bot.get_channel(1193546532700565576)
    final_donated_troops = new_member.donations - old_member.donations

    await ch.send(embed=discord.Embed(title=f"{new_member} of {new_member.clan} just donated {final_donated_troops} troops.", description="", colour=discord.Colour.dark_magenta()))

@coc.ClanEvents.member_join()
async def coc_member_join(member, clan):
    ch = bot.get_channel(1193546532700565576)
    e = discord.Embed(colour=0xffc0cb, title=f"{member.name} has joined {clan.name} :3")

    await ch.send(embed=e)

@coc.ClanEvents.member_leave()
async def coc_member_leave(member, clan):
    ch = bot.get_channel(1193546532700565576)
    e = discord.Embed(colour=0xffc0cb, title=f"{member.name} has left {clan.name} D:")

    await ch.send(embed=e)

@coc.WarEvents.war_attack()
async def coc_new_attack(attack, war):
    ch = bot.get_channel(bot.war_logs_channel_id)
    homeclan = await bot.coc_client.get_clan(credentials["clan_tag"])
    logging.critical(f"attacker: {attack.attacker.clan} {attack.attacker.name} | defender: {attack.defender.clan} {attack.defender.name}")
    if attack.attacker.clan.tag == homeclan.tag:
        e = discord.Embed(title="New attack", description=f"{attack.stars} ⭐ {attack.destruction}%", colour=0x03fc77)
    else:
        e = discord.Embed(title="New defense",description=f"{attack.stars} ⭐ {attack.destruction}%", colour=0xfc0303)

    e.add_field(name="Attacker", value=f"{attack.attacker.map_position}. **{attack.attacker.name}** | Tag: {attack.attacker_tag}", inline=False)
    e.add_field(name="Defender", value=f"{attack.defender.map_position}. **{attack.defender.name}** | Tag: {attack.defender_tag}", inline=False)

    await ch.send(embed=e)

@coc.WarEvents.state()
async def coc_war_end(old_war, new_war):
    assert old_war.state != new_war.state

    if new_war.state == "warEnded":
        ch = bot.get_channel(bot.war_logs_channel_id)
        war = new_war
        clan1 = war.clan
        clan2 = war.opponent
        result = "win" if clan1.stars > clan2.stars else "lose"
        if clan1.stars == clan2.stars:
            result = "win" if clan1.destruction > clan2.destruction else "lose"
            if clan1.destruction == clan2.destruction: result = "draw"

        e = discord.Embed(title="**The war has ended!**", description=f"**{clan1.name} | {clan1.tag}** vs **{clan2.name} {clan2.tag}**")
        e.add_field(name=f"Result: {result}", value=f"{clan1.name} ⭐{clan1.stars}/{clan1.max_stars} | {clan2.name} ⭐{clan2.stars}/{clan2.max_stars}", inline=False)
        try:
            e.add_field(name="Attacks", value="".join(f":crossed_swords: **{attack.attacker.name}** attacked **{attack.defender.name}**.\n**Result:** {attack.stars} :star2: {attack.destruction}%\n" for attack in clan1.attacks))
            e.add_field(name="Defenses", value="".join(f":shield: **{attack.defender.name}** has been attacked by **{attack.attacker.name}**.\n**Result:** {attack.stars} :star2: {attack.destruction}%\n" for attack in clan2.attacks))
        except Exception as err:
            logging.critical(f"Error: {err}")

        await ch.send(embed=e)

@coc.WarEvents.new_war()
async def coc_new_war(war):
    ch = bot.get_channel(bot.war_logs_channel_id)

    clan1 = war.clan
    clan2 = war.opponent
    e = discord.Embed(title="A new war has begun!", description=f"{clan1.name} | {clan1.tag} vs {clan2.name} {clan2.tag}", colour=0xffc0cb)
    e.add_field(name=f"Players from {clan1.name}:", value=f"".join([f"{member.map_position}.{member.name} TH{member.town_hall}| {member.tag}\n" for member in clan1.members]), inline=False)
    e.add_field(name=f"Players from {clan2.name}:", value=f"".join([f"{member.map_position}.{member.name} TH{member.town_hall}| {member.tag}\n" for member in clan2.members]), inline=False)

    await ch.send(embed=e)

@coc.ClientEvents.event_error()
async def coc_error(cls):
    logging.critical(cls)

async def main():
    coc_client = coc.EventsClient()

    try:
        await coc_client.login_with_tokens(credentials["coc_token"])
    except coc.InvalidCredentials as error:
        exit(error)
    discord.utils.setup_logging(level=logging.INFO, root=True)

    bot.coc_client = coc_client

    clan = await coc_client.get_clan(credentials["clan_tag"])
    bot.coc_client.add_player_updates(*[member.tag for member in clan.members])
    bot.coc_client.add_clan_updates(credentials["clan_tag"])
    bot.coc_client.add_war_updates(credentials["clan_tag"])

    bot.coc_client.add_events(
        coc_member_donation,
        coc_member_join,
        coc_member_leave,
        coc_new_attack,
        coc_new_war,
        coc_war_end
        )

    await bot.start(credentials["discord_token"])

asyncio.run(main())