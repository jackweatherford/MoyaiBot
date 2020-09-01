print('Connecting...')

import discord
import os
import sys
import subprocess
import json
import random

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN == None:
	from config import TOKEN

client = discord.Client()

scores = {}

@client.event
async def on_ready():
	global scores, wait
	with open("scores.json") as file:
		scores = json.load(file)
	print('Ready!')

async def saveScores():
	global scores
	with open("scores.json", "w") as file:
		json.dump(scores, file)

@client.event
async def on_message(message):
	global scores
	# if the author of the message is this bot then do nothing
	if message.author == client.user:
		return
	
	if '🗿' in message.content:
		if random.randint(1,100) == 100:
			await message.channel.send(f"A RARE GOLDEN 🗿 APPEARED!!!\n{message.author.name} JUST EARNED 100 🗿", file=discord.File('moyai.png'))
			scores[message.author.name] = scores[message.author.name] + 100
			await saveScores()
			return
		scores[message.author.name] = scores[message.author.name] + 1
		await saveScores()
		return
	
	await message.delete()
	
	if message.content.lower() == 'top':
		leaderboard = ''
		i = 1
		scores_sort = sorted(scores.items(), key=lambda x: x[1], reverse=True)
		for name, score in scores_sort:
			leaderboard += f'{i}. {name}: {score}\n'
			i += 1
			if i == 11:
				break
		await message.channel.send(content=f'```{"🗿 Leaderboard 🗿"}\n{leaderboard}```')
	
	if message.content.lower() == 'score':
		await message.channel.send(f'{message.author.name} has {scores[message.author.name]} 🗿')
	
	if message.content.lower() == 'help':
		await message.author.create_dm()
		await message.author.dm_channel.send(content=f'```{"🗿 Commands 🗿"}\n{"Enter any of the following words in the 🗿 server to get a response:"}\n\n{"help: The bot will dm you this message"}\n{"score: The bot will post your 🗿 count"}\n{"top: The bot will post a leaderboard of the users with the highest 🗿 counts"}```')

@client.event
async def on_message_edit(before, after):
	global scores
	
	if not '🗿' in after.content :
		scores[before.author.name] = scores[before.author.name] - 1
		await saveScores()
		await after.delete()

@client.event
async def on_message_delete(message):
	global scores
	
	if '🗿' in message.content:
		scores[message.author.name] = scores[message.author.name] - 1
		await saveScores()

@client.event
async def on_member_join(member):
	global scores
	scores[member.name] = 0
	await member.edit(nick='🗿')
	await saveScores()

client.run(TOKEN)
