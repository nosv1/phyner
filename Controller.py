''' IMPORTS '''

import discord
import asyncio
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random
from pytz import timezone
import traceback
import gspread
import mysql.connector
from types import SimpleNamespace
import os
import re

from dotenv import load_dotenv
load_dotenv()


import Logger
import Database
import Support
import Help
import Embed
import General
import Delete
import Guilds
import CustomCommands
import Events



''' CONSTANTS '''

intents = discord.Intents.all()
client = discord.Client(intents = intents)

connected = None
host = os.getenv("HOST")

guild_prefixes = Guilds.get_guild_prefixes()

restart = 1 # the host runs this Controller.py in a loop, when Controller disconnects, it returns 1 or 0 depending if @Phyner restart is called, 1 being restart, 0 being exit loop
restart_time = datetime.utcnow() # this is used to not allow commands a minute before restart happens


''' FUNCTIONS '''

@client.event
async def on_ready():
    error = None
    try:
        global connected
        connected = True
        Logger.log("Connection", f"{host} Controller Connected")

        await client.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing, name="@Phyner is finer."
            )
        )
    
    except:
        error = traceback.format_exc()

    if error:
        await Logger.log_error(client, error)
# end on_ready


@client.event
async def on_raw_message_edit(payload):
    if not connected: # we aint ready yet
        return

    error = False
    message = None
    try:

        pd = payload.data

        channel_id = int(pd["channel_id"])
        message_id = int(pd["id"])

        channel = client.get_channel(channel_id)
        channel = channel if channel else await client.fetch_channel(channel_id) # if DM, get_channel is none, i think

        message = await channel.fetch_message(message_id)

        if not message.author.bot and connected:
            try:
                pd["content"]
                await on_message(message)
            except KeyError: # when content was not updated
                pass

    except discord.errors.NotFound:
        await Logger.log("message edit erorr", traceback.format_exc())
    
    except:
        error = traceback.format_exc()

    if error:
        await Logger.log_error(client, error)
# end on_raw_message_edit


@client.event
async def on_message(message):
    global restart 
    global restart_time
    global guild_prefixes

    if not connected: # we aint ready yet
        return

    error = False
    try:
        # prep message content for use
        mc = message.content
        mc = re.sub(r"[“”]", '"', message.content)
        mc = re.sub(r"[\n\t\r]", ' ', message.content)
        mc += " "
        while "  " in mc:
            mc = mc.replace("  ", " ")
        args = mc.split(" ")

        author_perms = Support.get_member_perms(message.channel, message.author)


        ''' BEGIN CHECKS '''

        if not message.author.bot: # not a bot

            try:
                guild_prefix = guild_prefixes[message.guild.id if message.guild else message.author.id]
            except KeyError:
                guild_prefix = None

            if (
                (
                    host == "PI4" and # is PI4
                    (
                        (message.mentions and message.mentions[0].id == Support.ids.phyner_id) or # @Phyner command
                        mc[:len(str(guild_prefix))+1] == guild_prefix + " " # start of content = guild prefix
                    )
                ) or (
                    host == "PC" and # is PC
                        (args[0] == "``p") # ..p command
                )
            ):
                Logger.log("COMMAND", f"{message.author.id}, '{message.content}'\n")

                phyner = Support.get_phyner_from_channel(message.channel)
                is_mo = message.author.id == Support.ids.mo_id


                ''' COMMAND CHECKS '''
                    
                # \TODO @phyner todo, encrpyt, and how to intuitiviely remove a todo
                # TODO Invite Phyner Support
                # TODO request feature for money
                # TODO Donations
                # TODO @Phyner ids
                # TODO @Phyner copy
                # TODO @Phyner replace
                # TODO @Phyner command create/edit
                # TODO @Phyne watch -- <webhook_id> Events handling from webhooks


                ## CHECK FOR UPCOMING RESTART ##

                restart_delta = (restart_time - datetime.utcnow()).seconds
                if restart_delta < 60 and restart_delta > 0:
                    await Support.simple_bot_response(message.channel, description=f"**{phyner.mention} is about to restart. Try again in {restart_delta + 60} seconds.**", reply_message=message)
                    return

                ## MO ##

                if is_mo:
                    if args[1] == "test":
                        await message.channel.send("test done")
                        return
                        
                    elif args[1] == "setavatar":
                        with open('Images/62a3c8.png', 'rb') as f:
                            await client.user.edit(avatar=f.read())
                        return

                    elif args[1] in ["close", "restart"]:
                        restart = await Support.restart(client, restart=args[1] == "restart")
                        restart = 1 if restart else 0 # set restart
                        restart_time = datetime.utcnow() + relativedelta(seconds=60) # set new restart time
                        while restart and (restart_time - datetime.utcnow()).seconds != 1: # loop until then
                            continue
                        await client.close() # close
                        
                
                ## HELP + GENERAL ##

                if args[1] in ["?", "search"]:
                    await Help.search(message, args)

                elif args[1] in ["help", "h"]:
                    await Help.help(message)

                elif args[1] == "ping":
                    await General.send_ping(client, message.channel)

                elif args[1] in Delete.delete_aliases:
                    await Delete.main(client, message, args, author_perms)

                elif args[1] in General.say_aliases:
                    await General.say(message, args)



                ## EMBED ##

                elif args[1] == Embed.embed_aliases:
                    await Embed.main(client, message, args, author_perms)



                ## GUILDS ##

                elif args[1] == "prefix":
                    await Guilds.set_prefix(message, args, author_perms)
                    guild_prefixes = Guilds.get_guild_prefixes()

                
                ## CUSTOM COMMANDS ##

                # elif args[1] in CustomCommands.custom_command_aliases:
                    # await CustomCommands.main(args, author_perms)


                ## WATCH ##

                elif args[1] in Events.events_aliases:
                    await Events.main(message, args[2:], author_perms)


                else:
                    await Help.simple_help(message)

                ''' END COMMAND CHECKS '''

    except RuntimeError:
        Logger.log("Connection", f"{host} Disconnected")

    except SystemExit:
        pass
    
    except:
        error = traceback.format_exc()

    if error:
        await Logger.log_error(client, error)
# end on_message


Logger.create_log_file()
Logger.log("Connection", f"{host} Controller Connecting")
client.run(os.getenv("DISCORD_TOKEN"))
print(restart)