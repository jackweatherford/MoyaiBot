from os import getenv
from random import randint
from re import search

from json import dump, load
from urllib import request

from discord import Client, File
from boto3 import client

stats_path = 'src/res/stats.json'
moyai_png_path = 'src/res/moyai.png'

# Discord Token
TOKEN = getenv('DISCORD_TOKEN')
# AWS Access Keys
AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = getenv('AWS_SECRET_KEY')
# AWS S3 Stats JSON
S3_URL = getenv('S3_URL')

# If environment variables aren't set, grab from config.py + update filepaths
if TOKEN == None:
	from config import TOKEN, AWS_ACCESS_KEY_ID, AWS_SECRET_KEY, S3_URL
	stats_path = 'res/stats.json'
	moyai_png_path = 'res/moyai.png'

# Discord Client
discord_client = Client()

# S3 Client
s3_client = client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_KEY)

stats = {}

def isPlural(num): # Return 's' if num is plural
	if num == 1:
		return ''
	else:
		return 's'

def saveStats(stats): # Save stats
	with open(stats_path, 'w') as file:
		dump(stats, file)
	# Send stats.json to S3
	s3_client.upload_file(stats_path, 'jackweatherford-bucket', 'stats.json', ExtraArgs={'GrantRead': 'uri="http://acs.amazonaws.com/groups/global/AllUsers"'})

async def initMember(member):
	global stats
	for key in ['points', 'total_points_bet', 'num_bets', 'num_wins', 'profit', 'biggest_win', 'biggest_loss']:
		stats[member][key] = 0
	saveStats(stats)

async def help(message): # Send a help message to author
	author = message.author
	await message.channel.send(f'```Sent {author.name} a 🗿 help message.```')
	await author.create_dm()
	await author.dm_channel.send(content='```🗿 Moyai Bot 🗿\n' +
		'\t🗿 MOYAI BOT 🗿 is a simple Discord economy bot that uses the 🗿 emoji as its currency. Features include gambling, stats, leaderboards, and more.\n' +
		'\tMessages with a 🗿 in them will always award the sender exactly 1 point, regardless of how many 🗿 are in a single message.\n' +
		'\tFor each message sent that has a 🗿, there is a 1 in 100 chance to spawn the GOLDEN 🗿, which will award the sender 100 points!\n\n' +
		'🗿 Commands 🗿\n' +
		'Enter any of the following commands in any of the server\'s channels to get a response:\n' +
		'\tm help: The bot will dm you this message.\n' +
		'\tm score OR m points: Displays your 🗿 points.\n' +
		'\tm top OR m leaderboard: Displays a leaderboard of the users with the top 10 highest 🗿 points.\n' +
		'\tm bet <points> OR m gamble <points>: Bet the amount of <points> specified on a coin flip, 1:1 payout.\n' +
		'\tm stats: Displays your gambling statistics.```')

async def top(channel, stats): # Show top points
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

async def displayStats(channel, author, author_stats): # Show author's stats
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
	
	await channel.send(content=f'```🗿 {author[:-5]}\'s Gambling Statistics 🗿\n{statistics}```')

@discord_client.event
async def on_message(message): # When a message is sent
	global stats
	name = message.author.name
	author = message.author.name + '#' + message.author.discriminator
	# if the author of the message is this bot then do nothing
	if author == str(discord_client.user):
		return
	try:
		author_stats = stats[author]
	except KeyError:
		await initMember(author, stats)
		author_stats = stats[author]
	
	points = author_stats['points']
	channel = message.channel
	
	if '🗿' in message.content:
		if randint(1,100) == 100: # Golden moyai
			await message.channel.send(f'A RARE GOLDEN 🗿 APPEARED!!!\n{name.upper()} JUST EARNED 100 🗿 POINTS!', file=File(moyai_png_path))
			author_stats['points'] = points + 100
		else:
			author_stats['points'] = points + 1
		saveStats(stats)
		return
	
	# await message.delete() # For complete chaos, if message has no moyai
	
	content = message.content.lower()
	
	if content == 'm help':
		await help(message)
	
	elif content == 'm score' or content == 'm points':
		await channel.send(f'```{name} has {points} 🗿 point{isPlural(points)}.```')
	
	elif content == 'm top' or content == 'm leaderboard':
		await top(channel, stats)
	
	elif content == 'm stats':
		await displayStats(channel, author, author_stats)
	
	elif search('^m bet ', content) or search('^m gamble ', content):
		digit_start = 6 # If command was 'bet '
		if search('^m gamble ', content):
			digit_start = 9 # If command was 'gamble '
		
		bet_str = content[digit_start:]
		if bet_str.isdigit() or bet_str == 'all':
			if bet_str == 'all':
				bet = points
			else:
				bet = int(bet_str)
			if bet == 0:
				await channel.send('```ERROR: You can\'t bet 0 points!```')
				return
			
			if bet > points: # If not enough points to bet
				await channel.send(f'```You currently have {points} 🗿 point{isPlural(points)}, you cannot bet {bet} 🗿 point{isPlural(bet)}.```')
				return
			
			author_stats['total_points_bet'] += bet
			author_stats['num_bets'] += 1
			
			if randint(1,100) >= 50: # If win
				author_stats['points'] = points + bet
				author_stats['num_wins'] += 1
				author_stats['profit'] += bet
				if bet > author_stats['biggest_win']:
					author_stats['biggest_win'] = bet
				await channel.send(f'```{name} won {bet} 🗿 point{isPlural(bet)} and now has {points + bet} 🗿 point{isPlural(points + bet)}.```')
			
			else: # If lose
				author_stats['points'] = points - bet
				author_stats['profit'] -= bet
				if bet > author_stats['biggest_loss']:
					author_stats['biggest_loss'] = bet
				await channel.send(f'```{name} lost {bet} 🗿 point{isPlural(bet)} and now has {points - bet} 🗿 point{isPlural(points - bet)}.```')
			
			saveStats(stats)
		
		else: # If bet isn't an integer
			await channel.send(f'```ERROR: Your bet must be a positive integer. ex: m bet 10 OR m gamble 10```')

'''
# For complete chaos
@discord_client.event
async def on_message_edit(before, after): # When a message is edited
	# if the author of the message is this bot then do nothing
	if before.author == discord_client.user:
		return
	
	if not '🗿' in after.content:
		await after.delete()
'''

@discord_client.event
async def on_member_join(member): # When a new member joins
	global stats
	# Initialize member stats
	member_str = str(member)
	await initMember(member_str)
	# await member.edit(nick='🗿') # For complete chaos

@discord_client.event
async def on_ready(): # When the bot is ready
	global stats
	
	# Load stats from S3
	stats = load(request.urlopen(S3_URL + 'stats.json'))
	
	print('Ready!')

print('Connecting...')
# Put the bot online
discord_client.run(TOKEN)
