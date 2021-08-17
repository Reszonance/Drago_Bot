# Stuff to Add
#	Add a queue for music (https://drive.google.com/file/d/1B1LrGxt7lbqUkZ3-99M-xmvfewuw0hCw/view) check this for inspiration
#	Add moderation stuff (moving users) Ex: https://probot.io/commands
#	Add a recording / clipping / youtube video cutting feature

# if you get ffmpeg/avcpro not found then run sublime text 3 in admin

import time
import datetime
import os
import random
import discord
import youtube_dl
import asyncio
import urllib.parse, urllib.request, re
from discord.ext import commands
from dotenv import load_dotenv
from discord.utils import get
from bs4 import BeautifulSoup
from youtube_search import YoutubeSearch
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import *
from forex_python.converter import CurrencyRates

# Gets the tokens from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# To call a command on discord use $ (Ex: $help)
bot = commands.Bot(command_prefix='$')
players = {}
connected = False

# Events that happen on runtime
@bot.event
async def on_ready():
	print(bot.user.name + ' has started')
	await bot.change_presence(
			status = discord.Status.online,											# Status: online, idle, dnd, invisible
			activity = discord.Game('twitch.tv/reszonance'),
		)

# Combine all commands for on_message to work
@bot.event
async def on_message(message):
	if message.content.startswith('$clip'):
		# Finds the first link based on first items Found video matching search description
		results = YoutubeSearch(message.content[6:], max_results=10).to_dict()
		links = re.findall(r'/watch\?v=[a-zA-Z0-9_-]*', str(results))
		duration = re.findall(r'\'\d{0,2}:?\d{0,2}:?\d{0,2}\'', str(results))
		duration = duration[0].replace('\'', '')
		vidlength = duration.split(':')
		directory = r'C:\Users\rocke\Desktop\USB\Discord Bot'

		filelist = [ f for f in os.listdir(directory) if f.endswith(".mp3") ]
		for f in filelist:
		    os.remove(os.path.join(directory, f))

		channel = message.channel

		await channel.send('Downloading...')

		# Rewrites file of song file every time new song is played
		song_there = os.path.isfile("cut_song.mp3")
		try:
			if song_there:
				os.remove("cut_song.mp3")
				print("Removed old song file")
		except PermissionError: #remove later
			print("Trying to delete song file, but it's being played")
			return

		ydl_opts = {
		    'format': 'bestaudio/best',
		    'postprocessors': [{
		        'key': 'FFmpegExtractAudio',
		        'preferredcodec': 'mp3',
		        'preferredquality': '192',
		    }],
		}

		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		    print("Downloading audio now\n")
		    ydl.download(["www.youtube.com" + str(links[0])])

		for file in os.listdir("./"):
		    if file.endswith(".mp3"):
		    	if not os.path.exists('cut_song.mp3'):
			        name = file
			        print(f"Renamed File: {file}\n")
			        os.rename(file, "cut_song.mp3")

		print(duration)
		print(vidlength)

		await channel.send('Preview: ', file=discord.File('cut_song.mp3'))

		if(len(vidlength) == 3):
			await channel.send('The video is ' + vidlength[0] + ' hours' + vidlength[1] + ' minutes ' + vidlength[2] + ' seconds long.')
		elif (len(vidlength) == 2):
			await channel.send('The video is ' + vidlength[0] + ' minutes ' + vidlength[1] + ' seconds long.')

		# Create a preview option that plays the music
		timestamp = ''
		channel = message.channel
		await channel.send('Please enter a start and end time Ex: (0:36, 2:32) ')

		def check(m):
			timestamp = re.findall(r'\d{0,2}:?\d{1,2}:\d{2}', str(m.content))
			splitContent = m.content.split(', ')
			if (len(timestamp) == 2):
				return m.content == (timestamp[0] + ', ' + timestamp[1]) and m.channel == channel

		try:
			msg = await bot.wait_for('message', check=check, timeout=60.0)
		except asyncio.TimeoutError:
			await channel.send('Timeout Error')
		else:
			split = msg.content.split(', ')
			await channel.send('Trimming from {} to {}'.format(split[0], split[1]))

			def get_sec(time_str):
				lsTimes = time_str.split(':')
				if (len(lsTimes) == 3):
					h, m, s = lsTimes
					return int(h) * 3600 + int(m) * 60 + int(s)
				elif (len(lsTimes) == 2):
					m, s = lsTimes
					return int(m) * 60 + int(s)

			clip = AudioFileClip('cut_song.mp3')
			editedClip = clip.subclip(get_sec(split[0]), get_sec(split[1]))
			editedClip.write_audiofile('clip.mp3')
			await channel.send('Finished clipping!')
			await channel.send('Download: ', file=discord.File('clip.mp3'))


	await bot.process_commands(message)

# Makes bot join voice chat
@bot.command(pass_context=True)
async def join(ctx):
	global connected
	channel = ctx.author.voice.channel
	print(bot.user.name + f' has connected to {channel}')
	await channel.connect()
	connected = True

# Kicks bot out of voice chat
@bot.command(pass_context=True, aliases=['l', 'k', 'kick', 'dis', 'disc', 'disconnect'])
async def leave(ctx):
	global connected
	channel = ctx.author.voice.channel
	voice = get(bot.voice_clients, guild=ctx.guild)

	if voice and voice.is_connected():
		await voice.disconnect()
		print(bot.user.name + f' has disconnected from {channel}')
		await ctx.send(bot.user.name + f' left {channel}')
		connected = False
	else:
		print(bot.user.name + ' was told to leave voice channel, but was not in one')
		await ctx.send(bot.user.name + ' is not in a voice channel')

# Plays music
@bot.command(pass_context=True, aliases=['p', 'pla'])
async def play(ctx, *, search):
	global connected
	# Checks if bot is already connected to voice
	if connected == False:
		channel = ctx.author.voice.channel
		print(bot.user.name + ' has connected to voice')
		await channel.connect()
		connected = True

	# Finds the first link based on first itemsFound video matching search description
	results = YoutubeSearch(search, max_results=10).to_dict()
	links = re.findall(r'/watch\?v=[a-zA-Z0-9_-]*', str(results))

	# Rewrites file of song file every time new song is played
	song_there = os.path.isfile("song.mp3")
	try:
		if song_there:
			os.remove("song.mp3")
			print("Removed old song file")
	except PermissionError:
		print("Trying to delete song file, but it's being played")
		await ctx.send("ERROR: Music playing")
		return

	voice = get(bot.voice_clients, guild=ctx.guild)

	ydl_opts = {
	    'format': 'bestaudio/best',
	    'postprocessors': [{
	        'key': 'FFmpegExtractAudio',
	        'preferredcodec': 'mp3',
	        'preferredquality': '192',
	    }],
	}

	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
	    print("Downloading audio now\n")
	    ydl.download(["www.youtube.com" + str(links[0])])

	for file in os.listdir("./"):
	    if file.endswith(".mp3"):
	        name = file
	        print(f"Renamed File: {file}\n")
	        os.rename(file, "song.mp3")

	voice.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: print("Song done!"))
	voice.source = discord.PCMVolumeTransformer(voice.source)
	# Adjust volume with float value between 0.0 - 1.0
	voice.source.volume = 0.3

	nname = name.rsplit("-", 2)
	await ctx.send(f"Playing: {nname[0]}")
	print("playing\n")

# Pauses music
@bot.command(pass_context=True, aliases=['pa', 'pau'])
async def pause(ctx):

    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_playing():
        print("Music paused")
        voice.pause()
        await ctx.send("Music paused")
    else:
        print("Music not playing failed pause")
        await ctx.send("Music not playing failed pause")

# Resumes music
@bot.command(pass_context=True, aliases=['r', 'res'])
async def resume(ctx):

    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_paused():
        print("Resumed music")
        voice.resume()
        await ctx.send("Resumed music")
    else:
        print("Music is not paused")
        await ctx.send("Music is not paused")

# Stops music
@bot.command(pass_context=True, aliases=['s', 'sto'])
async def stop(ctx):

    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_playing():
        print("Music stopped")
        voice.stop()
        await ctx.send("Music stopped")
    else:
        print("No music playing failed to stop")
        await ctx.send("No music playing failed to stop")



# Other commands
@bot.command(name='time')
async def Cmds(ctx):
	currentTime = datetime.datetime.now()
	weekday = datetime.datetime.today().weekday()
	month = currentTime.month
	day = currentTime.day
	year = currentTime.year
	hour = currentTime.hour
	minute = currentTime.minute
	second = currentTime.second
	timeofday = ''
	# Saturday, August 8, 2020 11:57:43 PM

	if weekday == 0:
		weekday = 'Monday'
	elif weekday == 1:
		weekday = 'Tuesday'
	elif weekday == 2:
		weekday = 'Wednesday'
	elif weekday == 3:
		weekday = 'Thursday'
	elif weekday == 4:
		weekday = 'Friday'
	elif weekday == 5:
		weekday = 'Saturday'
	elif weekday == 6:
		weekday = 'Sunday'

	if month == 1:
		month = 'January'
	elif month == 2:
		month = 'February'
	elif month == 3:
		month = 'March'
	elif month == 4:
		month = 'April'
	elif month == 5:
		month = 'May'
	elif month == 6:
		month = 'June'
	elif month == 7:
		month = 'July'
	elif month == 8:
		month = 'August'
	elif month == 9:
		month = 'September'
	elif month == 10:
		month = 'October'
	elif month == 11:
		month = 'November'
	elif month == 12:
		month = 'December'

	if hour > 12:
		hour -= 12
		timeofday = 'PM'
	else:
		timeofday = 'AM'

	await ctx.send(str(weekday) + ', ' + str(month) + ' ' + str(day) + ', ' + str(year) + ' ' + str(hour) + ':' + str(minute) + ' ' + str(timeofday))


# Finds the prices and quantities of CSGO stickers 
@bot.command(name='csgo-stickers')
async def Cmds(ctx):

    rate = CurrencyRates().get_rate('USD', 'CAD')
    print('the rate is ' + rate)

    pages = ["https://steamcommunity.com/market/search?q=holo+2019#p1_default_desc",
                "https://steamcommunity.com/market/search?q=holo+2019#p2_default_desc",
                "https://steamcommunity.com/market/search?q=holo+2019#p3_default_desc",
                "https://steamcommunity.com/market/search?q=holo+2019#p4_default_desc",
                "https://steamcommunity.com/market/search?q=holo+2019#p5_default_desc",
                "https://steamcommunity.com/market/search?q=holo+2019#p6_default_desc"
            ]

    lstStickers = ["Sticker | Tyloo (Holo) | Katowice 2019",
                    "Sticker | Cloud9 (Holo) | Katowice 2019",
                    "Sticker | Natus Vincere (Holo) | Katowice 2019",
                    "Sticker | FaZe Clan (Holo) | Katowice 2019",
                    "Sticker | Astralis (Holo) | Katowice 2019",
                    "Sticker | Tyloo (Holo) | Berlin 2019",
                    "Sticker | Astralis (Holo) | Berlin 2019"
                    ]

    for page in pages:
        result = urllib.request.urlopen(page)
        soup = BeautifulSoup(result, 'lxml')

        pricePage = soup.find_all("span", {"class": "market_table_value normal_price"})

        priceRegexUSD = re.findall(r'[\$][0-9]{1,5}[.][0-9]{2}\s\w{3}', str(pricePage))
        del priceRegexUSD[1::2]
        #print(priceRegexUSD)


        priceRegexCDN = re.findall(r'[$](\d+.\d{2})\s\w{3}', str(priceRegexUSD))
        # Changing USD to CDN
        for i in range(itemsFound):
            priceRegexCDN[i] = str("{0:.2f}".format(float(priceRegexCDN[i]) * rate))
        # Adding the dollar sign and CDN back to each item
        for i in range(itemsFound):
            priceRegexCDN[i] = '$' + str(priceRegexCDN[i]) + ' CDN'

        #print(priceRegexCDN)

        namePage = soup.findAll("span", {"class": "market_listing_item_name"})
        nameRegex = re.findall(r'>([A-Za-z0-9\s|()\/]+)<\/span>', str(namePage))
        #print(nameRegex)

        qtyPage = soup.find_all("span", {"class": "market_listing_num_listings_qty"})
        qtyRegex = re.findall(r'\d+', str(qtyPage))

        del qtyRegex[1::2]
        #print(qtyRegex)

        for i in range(itemsFound):
            await ctx.send('Name: ' + nameRegex[i])
            await ctx.send('Price (USD): ' + priceRegexUSD[i])
            await ctx.send('Price (CDN): ' + priceRegexCDN[i])
            await ctx.send('Quantity: ' + qtyRegex[i] + '\n')

        time.sleep(20)

    await ctx.send('Done!')

# Finds prices and quantities of CSGO items using keywords of their name
@bot.command(name='price')
async def Cmds(ctx, *, item):
    rate = CurrencyRates().get_rate('USD', 'CAD')
    #.replace(item, '|', '%7C').replace(item, '(', '%28').replace(item, ')', '%29')
    item = str.replace(item, ' ', '+')

    print('Retrieving: ' + str(item) + '...')

    page = 'https://steamcommunity.com/market/search?appid=730&q=' + str(item)

    result = urllib.request.urlopen(page)
    soup = BeautifulSoup(result, 'html.parser')

    pricePage = soup.find_all("span", {"class": "market_table_value normal_price"})

    itemsFound = len(pricePage)
    print(str(itemsFound) + ' items found')

    if (itemsFound != 0):

        priceRegexUSD = re.findall(r'\$\d{1,3}[.|,]\d{1,3}[,|.|]*\d{1,3}\s\w{3}', str(pricePage))
        del priceRegexUSD[1::2]
        print(priceRegexUSD)


        priceRegexCDN = re.findall(r'\d{1,3}[.|,]\d{1,3}[,|.|]*\d{1,3}', str(priceRegexUSD))

        print(priceRegexCDN)


        # Removing commas for anything $1,000 and above
        for i in range(itemsFound):
            priceRegexCDN[i] = str.replace(priceRegexCDN[i], ',', '')

        print(priceRegexCDN)

        # Changing USD to CDN
        for i in range(itemsFound):
            priceRegexCDN[i] = str("{0:.2f}".format(float(priceRegexCDN[i]) * rate))


        # Adding the dollar sign and CDN back to each item
        for i in range(itemsFound):
            priceRegexCDN[i] = '$' + str(priceRegexCDN[i]) + ' CDN'

    # Fix error for glove case random characters like the star in hydra glove case
        namePage = soup.findAll("span", {"class": "market_listing_item_name"})
        nameRegex = re.findall(r'>([A-Za-z0-9�\s|()\/-]+)</span>', str(namePage))
        print(nameRegex)

        qtyPage = soup.find_all("span", {"class": "market_listing_num_listings_qty"})
        qtyRegex = re.findall(r'\d+', str(qtyPage))

        del qtyRegex[1::2]


        await ctx.send('Name: ' + nameRegex[0])
        await ctx.send('Price (CDN): ' + priceRegexCDN[0])
        await ctx.send('Price (USD): ' + priceRegexUSD[0])
        await ctx.send('Quantity: ' + qtyRegex[0] + '\n')

        print('Finished Sending Prices')

        await ctx.send('Done!')
    else:
        await ctx.send('Item Does Not Exist!')

    bot.run(TOKEN)