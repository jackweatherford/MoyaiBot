print('Connecting...')

import os
import sys
import subprocess
import json
import random
import re

import discord

TOKEN = os.getenv('DISCORD_TOKEN')
scores_path = 'src/res/scores.json'
stats_path = 'src/res/stats.json'
moyai_png_path = 'src/res/moyai.png'
if TOKEN == None:
	from config import TOKEN
	scores_path = 'res/scores.json'
	stats_path = 'res/stats.json'
	moyai_png_path = 'res/moyai.png'

client = discord.Client()

scores = {}
stats = {}

def isPlural(num):
	if num == 1:
		return ''
	else:
		return 's'

async def saveScores():
	global scores
	with open(scores_path, 'w') as file:
		json.dump(scores, file)

async def saveStats():
	global stats
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

async def top(channel):
	global scores
	leaderboard = ''
	i = 1
	scores_sort = sorted(scores.items(), key=lambda x: x[1], reverse=True)
	for user, points in scores_sort:
		leaderboard += f'{i}. {user}: {points} 🗿 point{isPlural(points)}.\n'
		i += 1
		if i == 11:
			break
	await channel.send(content=f'```🗿 Leaderboard 🗿\n{leaderboard}```')

async def displayStats(channel, author):
	global stats
	
	author_stats = stats[author]
	
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
	global scores, stats
	name = message.author.name
	author = message.author.name + '#' + message.author.discriminator
	# if the author of the message is this bot then do nothing
	if author == str(client.user):
		return
	score = scores[author]
	author_stats = stats[author]
	channel = message.channel
	
	if '🗿' in message.content:
		if random.randint(1,100) == 100:
			await message.channel.send(f'A RARE GOLDEN 🗿 APPEARED!!!\n{name.upper()} JUST EARNED 100 🗿 POINTS!', file=discord.File(moyai_png_path))
			scores[author] = score + 100
		else:
			scores[author] = score + 1
		await saveScores()
	else:
		await message.delete()
	
	content = message.content.lower()
	
	if content == 'help':
		await help(message.author)
	
	elif content == 'points' or content == 'score':
		await channel.send(f'```{name} has {score} 🗿 point{isPlural(score)}.```')
	
	elif content == 'top' or content == 'leaderboard':
		await top(channel)
	
	elif content == 'stats':
		await displayStats(channel, author)
	
	elif re.search('^bet ', content) or re.search('^gamble ', content):
		digit_start = 4
		if re.search('^gamble ', content):
			digit_start = 7
		
		if content[digit_start:].isdigit():
			points = int(content[digit_start:])
			if points == 0:
				await channel.send('```ERROR: You can\'t bet 0 points!```')
				return
			
			if points > score:
				await channel.send(f'```You currently have {score} 🗿 point{isPlural(score)}, you cannot bet {points} 🗿 point{isPlural(points)}.```')
				return
			
			author_stats['total_points_bet'] += points
			author_stats['num_bets'] += 1
			
			if random.randint(1,100) >= 50:
				scores[author] = score + points
				author_stats['num_wins'] += 1
				author_stats['profit'] += points
				if points > author_stats['biggest_win']:
					author_stats['biggest_win'] = points
				await channel.send(f'```{name} won {points} 🗿 point{isPlural(points)} and now has {scores[author]} 🗿 point{isPlural(scores[author])}.```')
			
			else:
				scores[author] = score - points
				author_stats['profit'] -= points
				if points > author_stats['biggest_loss']:
					author_stats['biggest_loss'] = points
				await channel.send(f'```{name} lost {points} 🗿 point{isPlural(points)} and now has {scores[author]} 🗿 point{isPlural(scores[author])}.```')
			
			await saveScores()
			await saveStats()
		
		else:
			await channel.send(f'```ERROR: Your bet must be a positive integer. ex: bet 10 OR gamble 10```')

@client.event
async def on_message_edit(before, after):
	global scores
	# if the author of the message is this bot then do nothing
	if before.author == client.user:
		return
	
	if not '🗿' in after.content:
		await after.delete()

@client.event
async def on_member_join(member):
	global scores, stats
	scores[str(member)] = 0
	await saveScores()
	new_stats = {}
	for key in ['total_points_bet', 'num_bets', 'num_wins', 'profit', 'biggest_win', 'biggest_loss']:
		new_stats[key] = 0
	stats[str(member)] = new_stats
	await saveStats()
	await member.edit(nick='🗿')

@client.event
async def on_ready():
	global scores, stats
	with open(scores_path) as file:
		scores = json.load(file)
	with open(stats_path) as file:
		stats = json.load(file)
	print('Ready!')

client.run(TOKEN)
