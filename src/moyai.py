print('Connecting...')

import os
import sys
import subprocess
import json
import random
import re

import discord

TOKEN = os.getenv('DISCORD_TOKEN')
stats_path = 'src/res/stats.json'
moyai_png_path = 'src/res/moyai.png'
if TOKEN == None:
	from config import TOKEN
	stats_path = 'res/stats.json'
	moyai_png_path = 'res/moyai.png'

client = discord.Client()

stats = {}

def isPlural(num):
	if num == 1:
		return ''
	else:
		return 's'

async def saveStats(stats):
	with open(stats_path, 'w') as file:
		json.dump(stats, file)

async def help(author):
	await author.create_dm()
	await author.dm_channel.send(content='```🗿 Help 🗿\n' +
		'\tMessages without 🗿 in them will be deleted.\n' +
		'\tMessages with a 🗿 in them will always award the sender exactly 1 point, regardless of how many 🗿 are in a single message.\n' +
		'\tFor each message, there is a 1 in 100 chance to spawn the golden 🗿, which will award you 100 points!\n\n' +
		'🗿 Commands 🗿\n' +
		'Enter any of the following words in the 🗿 server to get a response:\n' +
		'\thelp: The bot will dm you this message.\n' +
		'\tscore OR points: The bot will display your 🗿 points.\n' +
		'\ttop OR leaderboard: The bot will display a leaderboard of the users with the top 10 highest 🗿 points.\n' +
		'\tbet <points> OR gamble <points>: Bet the amount of <points> specified on a coin flip, 1:1 payout.\n' +
		'\tstats: Displays your gambling statistics.```')

async def top(channel, stats):
	leaderboard = ''
	i = 1
	stats_sort = sorted(stats.items(), key=lambda x: x[1]['points'], reverse=True)
	for user, user_stats in stats_sort:
		points = user_stats['points']
		leaderboard += f'{i}. {user}: {points} 🗿 point{isPlural(points)}.\n'
		i += 1
		if i == 11:
			break
	await channel.send(content=f'```🗿 Leaderboard 🗿\n{leaderboard}```')

async def displayStats(channel, author, author_stats):
	profit = author_stats["profit"]
	sign = ''
	if profit > 0:
		sign = '+'
	
	num_bets = author_stats["num_bets"]
	winrate = 0
	if num_bets != 0:
		winrate = author_stats["num_wins"] / num_bets * 100
	
	statistics = f'Total points bet for: {author_stats["total_points_bet"]}\n' + \
		f'Number of bets: {num_bets}\n' + \
		f'Winrate: {winrate:.2f}%\n' + \
		f'Profit: {sign}{profit}\n' + \
		f'Biggest win: +{author_stats["biggest_win"]}\n' + \
		f'Biggest loss: -{author_stats["biggest_loss"]}'
	
	await channel.send(content=f'```🗿 {author}\'s Gambling Statistics 🗿\n{statistics}```')

@client.event
async def on_message(message):
	global stats
	name = message.author.name
	author = message.author.name + '#' + message.author.discriminator
	# if the author of the message is this bot then do nothing
	if author == str(client.user):
		return
	author_stats = stats[author]
	points = author_stats['points']
	channel = message.channel
	
	if '🗿' in message.content:
		if random.randint(1,100) == 100:
			await message.channel.send(f'A RARE GOLDEN 🗿 APPEARED!!!\n{name.upper()} JUST EARNED 100 🗿 POINTS!', file=discord.File(moyai_png_path))
			author_stats['points'] = points + 100
		else:
			author_stats['points'] = points + 1
		await saveStats(stats)
		return
	
	await message.delete()
	
	content = message.content.lower()
	
	if content == 'help':
		await help(message.author)
	
	elif content == 'score' or content == 'points':
		await channel.send(f'```{name} has {points} 🗿 point{isPlural(points)}.```')
	
	elif content == 'top' or content == 'leaderboard':
		await top(channel, stats)
	
	elif content == 'stats':
		await displayStats(channel, author, author_stats)
	
	elif re.search('^bet ', content) or re.search('^gamble ', content):
		digit_start = 4
		if re.search('^gamble ', content):
			digit_start = 7
		
		if content[digit_start:].isdigit():
			bet = int(content[digit_start:])
			if bet == 0:
				await channel.send('```ERROR: You can\'t bet 0 points!```')
				return
			
			if bet > points:
				await channel.send(f'```You currently have {points} 🗿 point{isPlural(points)}, you cannot bet {bet} 🗿 point{isPlural(bet)}.```')
				return
			
			author_stats['total_points_bet'] += bet
			author_stats['num_bets'] += 1
			
			if random.randint(1,100) >= 50:
				author_stats['points'] = points + bet
				author_stats['num_wins'] += 1
				author_stats['profit'] += bet
				if bet > author_stats['biggest_win']:
					author_stats['biggest_win'] = bet
				await channel.send(f'```{name} won {bet} 🗿 point{isPlural(bet)} and now has {points + bet} 🗿 point{isPlural(points + bet)}.```')
			
			else:
				author_stats['points'] = points - bet
				author_stats['profit'] -= bet
				if bet > author_stats['biggest_loss']:
					author_stats['biggest_loss'] = bet
				await channel.send(f'```{name} lost {bet} 🗿 point{isPlural(bet)} and now has {points - bet} 🗿 point{isPlural(points - bet)}.```')
			
			await saveStats(stats)
		
		else:
			await channel.send(f'```ERROR: Your bet must be a positive integer. ex: bet 10 OR gamble 10```')

@client.event
async def on_message_edit(before, after):
	# if the author of the message is this bot then do nothing
	if before.author == client.user:
		return
	
	if not '🗿' in after.content:
		await after.delete()

@client.event
async def on_member_join(member):
	global stats
	member_str = str(member)
	for key in ['points', 'total_points_bet', 'num_bets', 'num_wins', 'profit', 'biggest_win', 'biggest_loss']:
		stats[member_str][key] = 0
	await member.edit(nick='🗿')
	await saveStats(stats)

@client.event
async def on_ready():
	global stats
	
	with open(stats_path) as file:
		stats = json.load(file)
	
	print('Ready!')

client.run(TOKEN)
