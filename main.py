import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from gtts import gTTS
from datetime import datetime
import os
import asyncio
from keep_alive import keep_alive
from collections import deque
import pytz
import re
from datetime import datetime, timedelta
import random
import sqlite3



conn = sqlite3.connect('giveaways.db')
c = conn.cursor()

queue = deque()
keep_alive()
ffmpegOptions = {'options': "-vn"}

os.system('clear')


class color():
    green = '\033[92m'
    pink = '\033[95m'
    red = '\33[91m'
    yellow = '\33[93m'
    blue = '\33[94m'
    gray = '\33[90m'
    reset = '\33[0m'
    bold = '\33[1m'
    italic = '\33[3m'
    unline = '\33[4m'

bot = commands.Bot(command_prefix='_', intents=discord.Intents.all())
bot.remove_command('help')
voice = None
playing = False


@bot.event
async def on_ready():
    print(
        f'{color.gray + color.bold}{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {color.blue}CONSOLE{color.reset}  {color.pink}discord.on_ready{color.reset} Đã đăng nhập bot {color.bold}{bot.user}{color.reset}'
    )
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(
                                  type=discord.ActivityType.listening,
                                  name='Bích Phương\'s playlist'))

async def send_welcome_message(channel, message, color=0xFFFF00):
    try:
        embed = discord.Embed(description=message, color=color)
        await channel.send(embed=embed)
    except Exception as e:
        print(e)


@bot.event
async def on_voice_state_update(member, before, after):
    global voice
    if voice is None:
        return

    if len(voice.channel.members) > 1:
        if member == bot.user:
            await send_welcome_message(
                voice.channel,
                f" <:pinkdotlkn:1196832522319962193> Hello <a:zduoitrailkn:1227211088433512509><@{member.id}><a:zduoiphailkn:1227211085359091742> bạn vừa rơi vào phòng <#{after.channel.id}> <a:3Kellylkng:1192105215474798632> 𝑇𝑖𝑚𝑒 𝑡𝑜 𝑟𝑒𝑙𝑎𝑥 <:abrightheart:1170204306507563068>"
            )
            return

    if before.channel != after.channel:
        if after.channel is not None:
            if member.bot:
                await send_bot_welcome_message(after.channel, member)
            else:
                await send_welcome_message(
                    after.channel,
                    f"<:pinkdotlkn:1196832522319962193> Hello  <a:zduoitrailkn:1227211088433512509> <@{member.id}> <a:zduoiphailkn:1227211085359091742>  bạn vừa rơi vào phòng <#{after.channel.id}><a:3Kellylkng:1192105215474798632> 𝑇𝑖𝑚𝑒 𝑡𝑜 𝑟𝑒𝑙𝑎𝑥  <:abrightheart:1170204306507563068>"
                )

        if before.channel is not None:
            if member == bot.user:
                return
            await send_welcome_message(
                before.channel,
                f" <:pinkdotlkn:1196832522319962193> {member.display_name} đã đi ngủ <:3kellysleep:1192450487295942717>",
                color=0xFF0000)

async def send_bot_welcome_message(channel, bot):
    try:
        bot_mention = bot.mention
        embed = discord.Embed(
            description=f"<:pinkdotlkn:1196832522319962193> Triệu hồi thành công {bot_mention}",
            color=0xFFFF00)
        await channel.send(embed=embed)
    except Exception as e:
        print(e)


@bot.command(name='join')
async def join(ctx):
    global voice

    if ctx.author.voice is None:
        await ctx.send('Tạo room voice chat đi bae ~')
        return

    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(ctx.author.voice.channel)
    else:
        voice = await ctx.author.voice.channel.connect()


@bot.command(name='s')
async def s(ctx, *, arg: str):
    global voice, playing

    if not arg:
        return

    if ctx.message.author.voice is None:
        await ctx.send('Tạo room voicechat đê!')
        return

    if ctx.guild.voice_client is None:
        try:
            voice = await ctx.message.author.voice.channel.connect()
        except Exception as e:
            print('error', e)
            return
    elif ctx.guild.voice_client.channel != ctx.message.author.voice.channel:
        await ctx.send('Đang ở voice chat khác')
        return

    tts = gTTS(text=arg, lang='vi')
    tts.save('tts-audio.mp3')
    queue.append(('tts-audio.mp3', ctx))
    if not playing:
        await play_next()

async def play_next():
    global playing, voice

    if not voice.is_connected():
        print("Bot is not connected to a voice channel.")
        return

    if queue:
        playing = True
        file, ctx = queue.popleft()
        voice.play(discord.FFmpegPCMAudio(file), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(), bot.loop))
        while voice.is_playing():
            await asyncio.sleep(1)
        os.remove(file)
        playing = False
    else:
        playing = False


@bot.event
async def on_message(message):
    target_channel_id = 1160783455706161243

    if message.channel.id == target_channel_id:
        await message.delete()

    await bot.process_commands(message)
@bot.command(name='leave')
async def leave(ctx):
    global voice, playing

    if ctx.guild.voice_client is None:
        await ctx.send('Bot không ở trong room này')
        return

    if voice is not None and voice.is_playing():
        voice.stop()

    await ctx.guild.voice_client.disconnect()
    voice = None
    playing = False

@bot.event
async def on_guild_channel_create(channel):
    # Kiểm tra nếu kênh mới tạo là một phòng voice chat
    if isinstance(channel, discord.VoiceChannel):
        # Gửi trạng thái bot nhạc vào phòng voice chat mới tạo sau 3 giây
        await asyncio.sleep(3)
        await musicbot(channel)


async def musicbot(voice_channel):
    music_role_id = 1152916515591561239
    guild = voice_channel.guild

    music_members = [
        member for member in guild.members
        if any(role.id == music_role_id for role in member.roles)
    ]
    active_members = [
        member for member in voice_channel.members if member in music_members
    ]

    if not active_members:
        return

    total_active_bots = len(active_members)

    active_embed = discord.Embed(
        title="Thông tin bot nhạc<a:aPanheart2:1164812699482468422>",
        color=discord.Color.green())
    active_embed.add_field(name="Tổng số bot nhạc đang phát",
                           value=f"{total_active_bots}",
                           inline=False)
    active_embed.add_field(
        name=f"Phòng: {voice_channel.mention}",
        value=" ".join([member.display_name for member in active_members]),
        inline=False)

    # Gửi embed vào phòng voice chat mới tạo
    await voice_channel.send(embed=active_embed)


@bot.command(name='musicbot')
async def musicbot(ctx):
    music_role_id = 1152916515591561239
    voice_channels = ctx.guild.voice_channels

    if not voice_channels:
        await ctx.send("Không có bot nhạc nào đang hoạt động trong server")
        return

    active_music_bots = {}
    inactive_music_bots = set()
    error_music_bots = set()  # Danh sách bot không online

    music_members = [
        member for member in ctx.guild.members
        if any(role.id == music_role_id for role in member.roles)
    ]

    total_music_bots = len(music_members)
    total_active_bots = 0

    # Tạo danh sách bot lỗi và bot chưa được sử dụng
    for member in music_members:
        if member.status == discord.Status.offline:
            error_music_bots.add(
                member)  # Thêm bot không online vào danh sách bot lỗi
        elif member.voice:  # Kiểm tra bot đang ở trong phòng voice chat
            total_active_bots += 1
        else:
            inactive_music_bots.add(
                member
            )  # Thêm bot không đang hoạt động vào danh sách bot chưa được sử dụng

    active_embed = discord.Embed(
        title="Thông tin bot nhạc<a:aPanheart2:1164812699482468422>",
        color=discord.Color.red())
    active_embed.add_field(name="Tổng số bot nhạc đang phát",
                           value=f"{total_active_bots}/{total_music_bots}",
                           inline=False)
    for voice_channel in voice_channels:
        active_members = [
            member for member in voice_channel.members
            if member in music_members
        ]
        if active_members:
            bot_list = ""
            for bot in active_members:
                bot_list += f"{bot.display_name}\n"
            active_embed.add_field(
                name=f"Phòng: {voice_channel.mention}",
                value=bot_list,
                inline=False)  # Sử dụng voice_channel.mention để tag tên phòng

    # Tạo embed cho bot chưa được sử dụng
    inactive_embed = discord.Embed(
        title="Bot nhạc còn trống <a:aflash2:1160601026697641984>",
        color=discord.Color.green())
    for bot in inactive_music_bots:
        inactive_embed.add_field(
            name=bot.display_name, value="",
            inline=False)  # Đề cập đến bot chưa được sử dụng

    # Tạo embed cho bot lỗi
    error_embed = discord.Embed(
        title="Bot đang bảo trì <:cmlosed1:1187589874962944092>",
        color=discord.Color.yellow())
    for bot in error_music_bots:
        error_embed.add_field(name=bot.display_name, value="",
                              inline=False)  # Đề cập đến bot lỗi

    # Gửi các embed
    await ctx.send(embed=active_embed)
    await ctx.send(embed=inactive_embed)
    await ctx.send(embed=error_embed)



c.execute('''CREATE TABLE IF NOT EXISTS giveaways
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              prize TEXT,
              duration TEXT,
              num_winners INTEGER,
              author_id INTEGER,
              start_message_id INTEGER,
              channel_id INTEGER,
              end_time TEXT)''')
conn.commit()

giveaway_count = 0  # Khởi tạo biến giveaway_count

def parse_time(duration: str) -> int:
    minutes = 0
    match = re.match(r'(\d+)\s*(m|h|d)', duration)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        if unit == 'm':
            minutes = value
        elif unit == 'h':
            minutes = value * 60
        elif unit == 'd':
            minutes = value * 1440  # 1 ngày có 1440 phút
    return minutes

def create_start_embed(ctx, prize: str, duration: str, author: discord.User, num_winners: int, giveaway_id: int) -> discord.Embed:
    global giveaway_count
    giveaway_count += 1

    hanoi_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
    current_datetime = datetime.now(hanoi_timezone).strftime("%d/%m/%Y %H:%M:%S")

    title = f"<a:zduoitrailkn:1227211088433512509>__Giveaway Bắt Đầu__<a:zduoiphailkn:1227211085359091742>"
    start_embed = discord.Embed(title=title, color=discord.Color.yellow())

    author_avatar_url = author.avatar.url if author.avatar else "https://discord.com/assets/dd4dbc0016779df1378e7812eabaa04d.png"
    start_embed.set_thumbnail(url=author_avatar_url)
    start_embed.set_footer(text=f"Mã số {giveaway_id} Giveaways  {(current_datetime)}", icon_url=author_avatar_url)

    start_embed.description = f"<a:zcuplkn:1201121029863522405>Giải thưởng: {prize}\n<a:zletterlkn:1231863248543027240>Thời gian: {duration}\n<a:zspellbooklkn:1201122043916201994>Số lượng giải: {num_winners}\n <:zMeowlkn:1231863246697398302>Tổ chức bởi <@{author.id}>\n\n _Thả react  🎁  để tham gia_"
    return start_embed

def create_end_embed(ctx, prize: str, winners_mentions: str, giveaway_id: int) -> discord.Embed:
    global giveaway_count

    hanoi_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
    current_datetime = datetime.now(hanoi_timezone).strftime("%d/%m/%Y %H:%M:%S")

    end_embed = discord.Embed(
        title="<a:zduoitrailkn:1227211088433512509>__Giveaway Kết Thúc__ <a:zduoiphailkn:1227211085359091742>",
        color=discord.Color.pink()
    )

    author_avatar_url = ctx.author.avatar.url if ctx.author.avatar else "https://discord.com/assets/dd4dbc0016779df1378e7812eabaa04d.png"
    end_embed.set_thumbnail(url=author_avatar_url)
    end_embed.set_footer(text=f"Mã số {giveaway_id} giveaways  {(current_datetime)}", icon_url=author_avatar_url)

    end_embed.description = f"<a:zcuplkn:1201121029863522405>Giải thưởng: {prize}\n<a:zcuplkn:1201121029863522405>Người thắng: {winners_mentions}\n <:zMeowlkn:1231863246697398302>Tổ chức bởi <@{ctx.author.id}>"
    return end_embed

async def announce_giveaway_in_text_channels(ctx, prize, num_winners, duration):
    guild = ctx.guild
    text_channels = guild.text_channels

    for text_channel in text_channels:
        if text_channel.permissions_for(guild.me).send_messages:
            await text_channel.send(
                f"Hi mọi người, mình đang tổ chức giveaway với phần thưởng: **{prize}**. "
                f"Số lượng người thắng: **{num_winners}**. Thời gian: **{duration}**. "
                f"Tham gia ngay để có cơ hội trúng giải!"
            )
@bot.command(name='ga')
async def ga(ctx, duration: str, num_winners: int, *, prize: str):
    global giveaway_running, countdown_task, start_message_id, end_time, winners, channel

    required_role_id = 1231827110159716453
    if required_role_id not in [role.id for role in ctx.author.roles]:
        error_embed = discord.Embed(
            description=f"Hello <a:zduoitrailkn:1227211088433512509> {ctx.author.mention} <a:zduoiphailkn:1227211085359091742> để tổ chức Giveaway vui lòng liên hệ <@389039417383452692> hoặc <@1080633133248032788> để được hướng dẫn bạn nha",
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed)
        return

    minutes = parse_time(duration)
    if minutes == 0:
        return await ctx.send("Vui lòng sử dụng đúng định dạng giờ m, h, d tương ứng với phút, giờ, ngày")

    end_time = datetime.utcnow() + timedelta(minutes=minutes)
    channel = ctx.channel

    c.execute('''INSERT INTO giveaways (prize, duration, num_winners, author_id, start_message_id, channel_id, end_time)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', (prize, duration, num_winners, ctx.author.id, None, channel.id, end_time.strftime("%Y-%m-%d %H:%M:%S")))
    giveaway_id = c.lastrowid
    conn.commit()
    start_embed = create_start_embed(ctx, prize, duration, ctx.author, num_winners, giveaway_id)
    start_message = await channel.send(embed=start_embed)
    start_message_id = start_message.id

    c.execute('UPDATE giveaways SET start_message_id = ? WHERE id = ?', (start_message.id, giveaway_id))
    conn.commit()
    try:
        await ctx.message.delete()
    except discord.errors.NotFound:
        pass

    emoji = discord.utils.get(ctx.guild.emojis, name='Zstarlkn')
    if emoji:
        await start_message.add_reaction(emoji)
    else:
        await ctx.send("Emoji không tồn tại hoặc bot không có quyền sử dụng emoji này.")

    await announce_giveaway_in_voice_channels(ctx, prize, num_winners, duration)

    await asyncio.sleep(minutes * 60)

    try:
        message = await channel.fetch_message(start_message_id)
        reaction = discord.utils.get(message.reactions, emoji=emoji)

        await handle_giveaway_end(ctx, reaction, prize, num_winners, channel, giveaway_id)

    except discord.errors.NotFound:
        await ctx.send("Tin nhắn bắt đầu giveaway không tồn tại.")

    return giveaway_id

async def handle_giveaway_end(ctx, reaction, prize, num_winners, channel, giveaway_id):
    c.execute('SELECT * FROM giveaways WHERE id = ?', (giveaway_id,))
    giveaway_info = c.fetchone()

    if not giveaway_info:
        return await ctx.send("Thông tin giveaway không tồn tại trong hệ thống.")
    if reaction:
        reaction_count = reaction.count - 1
        if reaction_count < num_winners:
            await ctx.send("Không đủ người tham gia để chọn số lượng người thắng đã chỉ định.")
        else:
            eligible_users = []
            async for user in reaction.users():
                if not user.bot:
                    eligible_users.append(user)

            winners = random.sample(eligible_users, num_winners)

            if winners:
                winners_mentions = ' '.join([winner.mention for winner in winners])
                end_embed = create_end_embed(ctx, prize, winners_mentions, giveaway_id)
                await channel.send(embed=end_embed)
                role_id = 1231827110159716453
                guild = ctx.guild
                role = discord.utils.get(guild.roles, id=role_id)
                if role:
                    topic = f"Trao giải Giveaways"
                    thread = await channel.create_thread(name=topic, type=discord.ChannelType.public_thread)

                    # Tạo embed màu hồng
                    thread_embed = discord.Embed(
                        description=f"Xin chúc mừng <a:lkn37:1267105053345316997> {winners_mentions} <a:lkn38:1267105087386550456> đã trở thành người chiến thắng giải *{prize}*! <a:lkn34:1267095219141349439>\n<@&{role_id}> vui lòng trao giải <a:lkn36:1267104774625689601>.\nMã số giveaway: {giveaway_id}",
                        color=discord.Color.pink()
                    )
                    await thread.send(embed=thread_embed)
                    
                else:
                    await ctx.send("Role không tồn tại.")
            else:
                await ctx.send(" Không đủ người tham gia giveaway!\n")
    else:
        await ctx.send("Không đủ người tham gia giveaway!\n")
@bot.command(name='spamga')
async def spamga(ctx, num_spams: int, duration: str, num_winners: int, *, prize: str):
    async def run_ga_with_delay(ctx, duration, num_winners, prize, delay):
        await asyncio.sleep(delay)
        await ga(ctx, duration, num_winners, prize=prize)

    tasks = []
    for i in range(num_spams):
        task = asyncio.create_task(run_ga_with_delay(ctx, duration, num_winners, prize, i * 30))
        tasks.append(task)

    await asyncio.gather(*tasks)
@bot.event
async def on_ready():
    print(f'Đăng nhập thành công {bot.user}')

@bot.event
async def on_disconnect():
    conn.close()

@bot.command()
async def start_giveaway(ctx, duration: str, num_winners: int, *, prize: str):
    global giveaway_running, current_giveaway_info

    required_role_id = 1231827110159716453
    if required_role_id not in [role.id for role in ctx.author.roles]:
        await ctx.send("Bạn không có quyền bắt đầu giveaway.")
        return

    minutes = parse_time(duration)
    if minutes == 0:
        await ctx.send("Vui lòng sử dụng định dạng thời gian hợp lệ (m, h, d).")
        return

    end_time = datetime.utcnow() + timedelta(minutes=minutes)

    start_embed = create_start_embed(ctx, prize, duration, ctx.author, num_winners)
    start_message = await ctx.send(embed=start_embed)

    current_giveaway_info = {
        'end_time': end_time,
        'num_winners': num_winners,
        'prize': prize,
        'message_id': start_message.id,
        'channel_id': ctx.channel.id
    }
    giveaway_running = True

    emoji = discord.utils.get(ctx.guild.emojis, name='Zstarlkn')
    if emoji:
        await start_message.add_reaction(emoji)
    else:
        await ctx.send("Emoji không tồn tại hoặc bot không có quyền sử dụng emoji này.")
        return

intents = discord.Intents.default()
intents.messages = True
intents.members = True  # Enable the members intent

confession_channel_id = 1174673765871927346
log_channel_id = 1163074681046315148
reply_log_channel_id = 1240127905984549024


@bot.event
async def on_ready():
    print('Bot is ready')
    global confession_count
    confession_count = load_confession_count()
    print(f'Current confession count: {confession_count}')
INITIAL_CONFESSION_COUNT = 265
confession_threads = {}
confession_count = INITIAL_CONFESSION_COUNT
CONFESSION_COUNT_FILE = 'confession_count.txt'

def save_confession_count(count):
    with open(CONFESSION_COUNT_FILE, 'w') as file:
        file.write(str(count))

def load_confession_count():
    if os.path.exists(CONFESSION_COUNT_FILE):
        with open(CONFESSION_COUNT_FILE, 'r') as file:
            return int(file.read().strip())
    return 265  # Số confession bắt đầu từ 170
confession_channel_ids = [1153156079388205157, 1155081908103954503, 1153156755098968114, 1156927838113513614, 1153155832679235614]
emojis = [
    "<:zlikelkn:1240186553922224188>",
    "<a:zheartlkn:1240186551904895028>",
    "<a:zhahalkn:1240186556845785108>",
    "<a:zthuongthuonglkn:1240186558750134315>",
    "<a:sadlkn:1240186545953046559>",
    "<:zdislikelkn:1240186548981600336>"
]

async def add_reactions_with_retry(message, emojis, max_retries=5):
    for emoji in emojis:
        for attempt in range(max_retries):
            try:
                await message.add_reaction(emoji)
                await asyncio.sleep(1)  # Thêm thời gian chờ giữa các yêu cầu để tránh rate limit
                break  # Thoát khỏi vòng lặp nếu thành công
            except discord.errors.HTTPException as e:
                if e.status == 429:
                    retry_after = e.retry_after if hasattr(e, 'retry_after') else 2 ** attempt
                    await asyncio.sleep(retry_after)
                else:
                    print(f"Failed to add reaction: {emoji}. Error: {e}")
                    break

@bot.command(name='cfan')
async def cfan_command(ctx, *, confession_text):
    global confession_count
    confession_count += 1
    save_confession_count(confession_count)

    confession_channel = bot.get_channel(confession_channel_id)
    log_channel = bot.get_channel(log_channel_id)

    if confession_channel and log_channel:
        confession_color = random.randint(0, 0xFFFFFF)  # Tạo màu ngẫu nhiên
        confession_embed = discord.Embed(
            title=f" <a:zspellbooklkn:1201122043916201994> Chuyện của làng, lá thư số `#{confession_count}` <a:zletterlkn:1231863248543027240>",
            description="\u200B" + confession_text,
            color=confession_color
        )

        # Thêm thông tin "Được gửi bởi 1 lữ khách ven đường" vào footer của Embed
        confession_embed.set_footer(text="💖Gửi bởi lữ khách ven đường🍀 discord.gg/langkhongngu")

        # Gửi confess embed vào kênh confess
        confess_message = await confession_channel.send(embed=confession_embed)

        # Tạo chủ đề mới trong kênh confess
        topic = f"Rep confess #{confession_count} tại đây "
        new_thread = await confess_message.create_thread(name=topic, auto_archive_duration=1440)
        guide_embed = discord.Embed(
            description="Để rep ẩn danh vui lòng sử dụng lệnh _rcfs [ mã số ] [ nội dung ]",
            color=0xFF0000  # Màu đỏ
        )
        await new_thread.send(embed=guide_embed)
        # Xóa tin nhắn confess
        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            print("Tin nhắn không tồn tại hoặc đã bị xóa, không thể xóa tin nhắn này.")

        # Thả emoji vào tin nhắn confession
        await add_reactions_with_retry(confess_message, emojis)

        # Ghi lại ID của confession và thread trong log channel
        log_message = f"[Confession #{confession_count}] từ {ctx.author.name} ({ctx.author.id}) đã gửi: {confession_text} (Message ID: {confess_message.id}, Thread ID: {new_thread.id})"
        await log_channel.send(log_message)

    else:
        await ctx.send("Không tìm thấy kênh confession hoặc kênh log, vui lòng cài đặt lại đúng cách.")

@bot.command(name='cfs')
async def cfs_command(ctx, *, confession_text):
    global confession_count
    confession_count += 1

    save_confession_count(confession_count)  # Lưu số confession hiện tại vào tệp

    confession_channel = bot.get_channel(confession_channel_id)
    log_channel = bot.get_channel(log_channel_id)

    if confession_channel and log_channel:
        confession_color = random.randint(0, 0xFFFFFF)  # Tạo màu ngẫu nhiên

        # Tạo thông điệp confession với xuống dòng
        confession_message = f"Được gửi bởi: {ctx.author.mention}\n*{confession_text}*"

        # Tạo Embed confession với title giữ nguyên
        confession_embed = discord.Embed(
            title=f"<a:zspellbooklkn:1201122043916201994> Chuyện của làng, lá thư số `#{confession_count}` <a:zletterlkn:1231863248543027240>",
            description=confession_message,
            color=confession_color
        )

        # Thêm thông tin "được gửi bởi" vào footer của embed và icon tròn avatar
        author_avatar_url = ctx.author.avatar.url if ctx.author.avatar else "https://discord.com/assets/dd4dbc0016779df1378e7812eabaa04d.png"
        confession_embed.set_footer(text=f"discord.gg/langkhongngu ", icon_url=author_avatar_url)

        if ctx.author.avatar:
            confession_embed.set_thumbnail(url=ctx.author.avatar.url)

        # Gửi confession embed vào kênh confess
        confess_message = await confession_channel.send(embed=confession_embed)

        # Tạo chủ đề mới trong kênh confess
        topic = f"Rep confess #{confession_count} tại đây "
        new_thread = await confess_message.create_thread(name=topic, auto_archive_duration=1440)
        guide_embed = discord.Embed(
            description="Để rep ẩn danh vui lòng sử dụng lệnh _rcfs [ mã số ] [ nội dung ]",
            color=0xFF0000  # Màu đỏ
        )
        await new_thread.send(embed=guide_embed)
        # Xóa tin nhắn confess
        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            print("Tin nhắn không tồn tại hoặc đã bị xóa, không thể xóa tin nhắn này.")

        # Thả emoji vào tin nhắn confession
        await add_reactions_with_retry(confess_message, emojis)

        # Ghi lại ID của confession và thread trong log channel
        log_message = f"[Confession #{confession_count}] từ {ctx.author.name} ({ctx.author.id}) đã gửi: {confession_text} (Message ID: {confess_message.id}, Thread ID: {new_thread.id})"
        await log_channel.send(log_message)

    else:
        await ctx.send("Không tìm thấy kênh confession hoặc kênh log, vui lòng cài đặt lại đúng cách.")



@bot.command()
async def rcfs(ctx, confession_number: int, *, reply_text):
    confession_channel = bot.get_channel(confession_channel_id)
    log_channel = bot.get_channel(log_channel_id)
    reply_log_channel = bot.get_channel(reply_log_channel_id)

    if confession_channel and log_channel and reply_log_channel:
        # Tìm tin nhắn log chứa confession_number
        async for log_message in log_channel.history(limit=200):
            if f"[Confession #{confession_number}]" in log_message.content:
                # Lấy message ID và thread ID từ log message
                try:
                    parts = log_message.content.split('(Message ID: ')[1].split(', Thread ID: ')
                    message_id = int(parts[0])
                    thread_id = int(parts[1].split(')')[0])
                except (IndexError, ValueError):
                    await ctx.send(f"Không thể tìm thấy thông tin Message ID và Thread ID trong log cho confession #{confession_number}")
                    return

                thread = bot.get_channel(thread_id)
                if thread:
                    reply_embed = discord.Embed(
                        description=f"> <a:Zdomdomlkn:1235512517359308840> {reply_text}")

                    # Lấy thông tin người đăng bài từ tin nhắn log
                    try:
                        original_author_id = int(log_message.content.split(')')[0].split('(')[1])
                        original_author = await bot.fetch_user(original_author_id)
                    except (IndexError, ValueError):
                        await ctx.send(f"Không thể tìm thấy thông tin người đăng bài trong log cho confession #{confession_number}")
                        return

                    # Kiểm tra xem người dùng là người đăng bài gốc hay không
                    if ctx.author.id == original_author.id:
                        reply_embed.set_footer(text="Phản hồi bởi người đăng bài")
                    else:
                        reply_embed.set_footer(text="Phản hồi bởi người dân trong làng")

                    await thread.send(embed=reply_embed)

                    # Gửi phản hồi vào kênh reply_log_channel
                    await reply_log_channel.send(
                        f"{ctx.author.mention} vừa phản hồi confession #{confession_number} với nội dung: {reply_text}"
                    )

                    # Xóa tin nhắn rcfs của người dùng
                    try:
                        await ctx.message.delete()
                    except discord.errors.NotFound:
                        print("Tin nhắn không tồn tại hoặc đã bị xóa, không thể xóa tin nhắn này.")
                    return

        await ctx.send(f"Không tìm thấy confession #{confession_number} trong dữ liệu")
    else:
        await ctx.send("Không tìm thấy kênh confession, log hoặc kênh phản hồi, vui lòng cài đặt lại đúng cách.")


confession_channel_ids = [1153156079388205157, 1155081908103954503, 1153156755098968114, 1156927838113513614, 1153155832679235614]
@bot.event
async def on_message(message):
    if message.channel.id in confession_channel_ids:
        topic = f"Bình luận tại đây"
        new_thread = await message.create_thread(name=topic, auto_archive_duration=None)

    await bot.process_commands(message)



@bot.command(name='help')
async def help_command(ctx):
    # Tạo một embed Discord
    embed = discord.Embed(title="Bảng lệnh hướng dẫn sử dụng bot",
                          description="Dưới đây là danh sách các lệnh bot:",
                          color=0x00ff00)

    # Thêm các trường vào embed để hiển thị các lệnh và mô tả của chúng
    embed.add_field(name="<:pinkdotlkn:1196832522319962193> _s [nội dung]",
                    value="Chuyển văn bản thành giọng nói",
                    inline=False)
    embed.add_field(name="<:pinkdotlkn:1196832522319962193> _cfs [nội dung]",
                    value="Đăng câu chuyện công khai",
                    inline=False)
    embed.add_field(name="<:pinkdotlkn:1196832522319962193> _cfan [nội dung]",
                    value="Đăng câu chuyện ẩn danh",
                    inline=False)
    embed.add_field(name="<:pinkdotlkn:1196832522319962193> _rcfs [mã số] [nội dung]",
    value="Phản hồi ẩn danh",
    inline=False)
    embed.add_field(name="<:pinkdotlkn:1196832522319962193> _join",
                    value="Tham gia vào phòng thoại mà bạn đang ở",
                    inline=False)
    embed.add_field(name="<:pinkdotlkn:1196832522319962193> _leave",
                    value="Rời khỏi phòng thoại hiện tại.",
                    inline=False)
    embed.add_field(name="<:pinkdotlkn:1196832522319962193> _musicbot",
                    value="Kiểm tra tình trạng bot nhạc",
                    inline=False)

    # Gửi embed vào kênh của người gửi lệnh
    await ctx.send(embed=embed)


CHUI_FILE_PATH = 'cauchui.txt'
ALLOWED_ROLE_ID = 1241318523872219186

@bot.command()
async def chui(ctx, member: discord.Member):
    # Kiểm tra xem người gửi có role được phép không
    allowed_role = discord.utils.get(ctx.guild.roles, id=ALLOWED_ROLE_ID)
    if allowed_role not in ctx.author.roles:
        await ctx.send("Muốn chửi thuê á? Liên hệ admin đê.")
        return

    # Xóa tin nhắn chứa lệnh _chui
    await ctx.message.delete()

    # Đọc nội dung từ file chứa các câu chửi
    with open(CHUI_FILE_PATH, 'r', encoding='utf-8') as f:
        chui_lines = f.readlines()

    # Chọn ngẫu nhiên 10 câu chửi
    selected_chui = random.sample(chui_lines, min(len(chui_lines), 10))

    # Phản hồi với các câu chửi và @ người được tag
    for chui_msg in selected_chui:
        await ctx.send(f'{member.mention} {chui_msg.strip()}')
        await asyncio.sleep(2)  # Chờ 2 giây trước khi gửi câu chửi tiếp theo

class AvatarView(discord.ui.View):
    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    @discord.ui.button(label="Check avatar cá nhân", style=discord.ButtonStyle.secondary)
    async def user_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(color=0xffb782)
        embed.set_author(name=f"{self.member.name}", icon_url=self.member.avatar.url)
        embed.set_image(url=self.member.avatar.url)
        embed.set_footer(text=f"Yêu cầu bởi {interaction.user}", icon_url=interaction.user.avatar.url)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Check avatar guild", style=discord.ButtonStyle.primary)
    async def server_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.member.guild_avatar:
            embed = discord.Embed(color=0xff0000)
            embed.set_author(name=f"{self.member.name}#{self.member.discriminator}", icon_url=self.member.guild_avatar.url)
            embed.set_image(url=self.member.guild_avatar.url)
            embed.set_footer(text=f"Yêu cầu bởi {interaction.user}", icon_url=interaction.user.avatar.url)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("Người dùng này không có avatar server.", ephemeral=True)

    @discord.ui.button(label="Check ảnh bìa", style=discord.ButtonStyle.success)
    async def personal_banner(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = await bot.fetch_user(self.member.id)
        if user.banner:
            embed = discord.Embed(color=0xffb782)
            embed.set_author(name=f"{self.member.name}", icon_url=user.avatar.url)
            embed.set_image(url=user.banner.url)
            embed.set_footer(text=f"Yêu cầu bởi {interaction.user}", icon_url=interaction.user.avatar.url)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("Người dùng này không có banner cá nhân.", ephemeral=True)


AUTHORIZED_ROLE_ID = 1264730107654967407
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def check(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    embed = discord.Embed(title=f"Xin chào, bạn cần check gì ở {member}", color=0xffb782)
    embed.set_footer(text=f"Yêu cầu bởi {ctx.author}", icon_url=ctx.author.avatar.url)
    view = AvatarView(member)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def role(ctx, member: discord.Member, *, args: str):
    await ctx.message.delete()

    authorized_role = discord.utils.get(ctx.guild.roles, id=AUTHORIZED_ROLE_ID)
    if authorized_role not in ctx.author.roles:
        await ctx.send("Vai trò quá thấp để dùng chức năng này")
        return

    match = re.match(r"(.+)\((.+)\)", args)
    if not match:
        await ctx.send("Lệnh: `_role @user role1, role2 (nội dung)`")
        return

    roles_part, content = match.groups()
    role_names = [role.strip() for role in roles_part.split(",")]

    guild = ctx.guild
    roles = [discord.utils.find(lambda r: r.name.lower() == role_name.lower(), guild.roles) for role_name in role_names]

    if any(role is None for role in roles):
        await ctx.send(f'Sai tên role, hoặc role chưa được tạo: {", ".join(role_names)}.')
        return

    bot_member = guild.get_member(bot.user.id)
    bot_top_role = bot_member.top_role

    if any(ctx.author.top_role <= role or bot_top_role <= role for role in roles):
        await ctx.send("Bot không có quyền quản lý role này.")
        return

    added_roles = []
    removed_roles = []
    for role in roles:
        if role in member.roles:
            await member.remove_roles(role)
            removed_roles.append(role)
        else:
            await member.add_roles(role)
            added_roles.append(role)

    role_statuses = []
    for role in added_roles:
        role_statuses.append(f"{role.name} <a:lkn29:1266651900577714178>")
    for role in removed_roles:
        role_statuses.append(f"{role.name} <a:lkn28:1266651903849271337>")

    role_statuses_str = ", ".join(role_statuses)

    description = (
        f"**<:lkn32:1266657066789896275> Người dùng: {member.mention}**\n"
        f"**<:lkn26:1266109059598254191> Role: {role_statuses_str}**\n"
        f"**<:lkn31:1266661236796297268> Nội dung: {content.strip()}**\n"
        f"**<a:lkn30:1266651899088732242> Thao tác bởi: {ctx.author.mention}**"
    )

    embed = discord.Embed(description=description, color=discord.Color.red())

    await ctx.send("**_<a:lkn35:1267100833200341014>Điều phối vai trò <a:lkn35:1267100833200341014>_**", embed=embed)

REQUIRED_ROLE_ID = 1264730107654967407
def has_required_role():
    async def predicate(ctx):
        role = discord.utils.get(ctx.guild.roles, id=REQUIRED_ROLE_ID)
        if role in ctx.author.roles:
            return True
        else:
            await ctx.send("Bạn không có quyền sử dụng lệnh này.")
            return False
    return commands.check(predicate)
@bot.command()
async def donate(ctx, member: discord.Member, *, amount: str):
    await ctx.message.delete()
    donation_date = datetime.now().strftime("%d-%m-%Y")
    sender_mention = ctx.message.author.mention
    avatar_url = member.avatar.url
    embed = discord.Embed(
        description=(
            f"**<:lkn26:1266109059598254191> Cảm ơn {member.mention}<a:lkn34:1267095219141349439> đã donate cho server _{amount}_. Chúc bạn luôn vui tươi ạ <a:lkn27:1266253627459371091>  **\n"
            f"**<a:lkn32:1267091332862836799> Ngày donate: {donation_date}**\n"
            f"**<:lkn32:1266657066789896275> Thao tác bởi: {sender_mention}**"
        ),
        color=discord.Color.yellow()
    )

    embed.set_thumbnail(url=avatar_url)

    # Gửi tin nhắn với nội dung "Donor Information" bên ngoài embed
    await ctx.send(content=" **_<a:lkn30:1266651899088732242>Thư cảm ơn<a:lkn30:1266651899088732242>_**", embed=embed)
@donate.error
async def donate_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("Vui lòng dùng đúng lệnh `_donate @member nội dung`")
    else:
        await ctx.send("Vui lòng dùng đúng lệnh `_donate @member nội dung`")

intents = discord.Intents.default()
intents.members = True

from discord.ext import commands
from discord.ui import Button, View

class ButtonView(View):
    def __init__(self, member):
        super().__init__(timeout=None)  # Đặt timeout thành None để View không bao giờ hết hạn
        self.member = member

    @discord.ui.button(label="Vẫy tay để chào", style=discord.ButtonStyle.secondary, emoji="👋", custom_id="greet_button")
    async def greet_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Kiểm tra nếu người dùng có role cần thiết
        required_role_id = 1268943736516378719
        if any(role.id == required_role_id for role in interaction.user.roles):
            # Danh sách các đường link sticker hoặc ảnh
            sticker_urls = [
                'https://cdn.discordapp.com/attachments/1269438411874504825/1269438464735187058/Screenshot_2024-08-01_051622.png?ex=66b01033&is=66aebeb3&hm=abee1e0d7c3a643788154946cf376f7610a86f3fec44bc908047d37aa81bc96f&',
                'https://media.discordapp.net/attachments/1269438411874504825/1269611938086785096/xinchao.gif?ex=66b0b1c2&is=66af6042&hm=4f99beb292444786dac861a94ace3616225a393b5c4db70faac11d797d075a26&=',
                'https://media.discordapp.net/attachments/1269438411874504825/1269611936870301757/xinchao3.gif?ex=66b0b1c1&is=66af6041&hm=7c551746a992f238df9d6bd3b989720cc7c8d0d95d1c6741d993e985d1c608b8&=',
                'https://media.discordapp.net/attachments/1269438411874504825/1269611936492818432/xinchao4.gif?ex=66b0b1c1&is=66af6041&hm=5801da56594ca8bf9c7d2a72d612facb314c30818a659050d0afa0f27bc46aa2&=',
                'https://media.discordapp.net/attachments/1269438411874504825/1269611936056873000/xinchao5.gif?ex=66b0b1c1&is=66af6041&hm=1cf59216361ad476f207f78c7ffc417f9a8000583f756c153ec9c5fe04b2a939&=',
                'https://media.discordapp.net/attachments/1269438411874504825/1269611935695896627/xinchao6.gif?ex=66b0b1c1&is=66af6041&hm=f210cfd46eb07c75278353d02fcdfc12dd8a5ea5ed0a602f80583d8207066f16&=',
                'https://media.discordapp.net/attachments/1269438411874504825/1269611935091921007/xinchao8.gif?ex=66b0b1c1&is=66af6041&hm=9f6a8c0802b1112f8e3bb5f4e5f027d4b5d1427015367cf3f6287db184eca165&=',
                'https://media.discordapp.net/attachments/1269438411874504825/1269611933921706156/xinchao7.gif?ex=66b0b1c1&is=66af6041&hm=9a7db583b304cf5663d5c5705ad71f293a298209ac593176031ce2a913e344db&=',
                'https://media.discordapp.net/attachments/1269438411874504825/1269611937470353448/xinchao2.gif?ex=66b0b1c2&is=66af6042&hm=1558bc13b5a9cd5be3e612f3a3205bc4a41329e4d3b3f0da384f42d81e3947cb&='
            ]
            # Danh sách các câu chào
            greetings = [
                f"Xin chào {self.member.mention}<a:lkn2:1269636424785723473>, thật vui vì bạn đã ở đây <a:lkn1:1269635885352226816>. Mình là {interaction.user.mention} thuộc bộ phận <@&1269485249818263588> <:lkn3:1269641694521856143> của server, rất vui được làm quen với bạn<a:lkn4:1269641958738100306>",
                f"Rất vui được đón tiếp bạn {self.member.mention}<a:lkn5:1269648486190551160>. Mình là {interaction.user.mention} thuộc bộ phận <@&1269485249818263588> <:lkn3:1269641694521856143> của server, cần giúp đỡ gọi mình nhé",
                f"Heyy {self.member.mention}<a:lkn5:1269648486190551160>, đập tay cái nào <a:lkn1:1269635885352226816>. Tớ là {interaction.user.mention} and nice to meet u bae~ <a:lkn6:1269649714484219987>"
            ]
            # Danh sách các câu ngẫu nhiên
            random_messages = [
                "Wishing you endless joy and laughter!",
                "May your days be filled with happiness and smiles.",
                "Hoping you always find reasons to smile.",
                "Sending you all the positive vibes for a happy life!",
                "May your life be as bright and cheerful as your smile.",
                "Here’s to a life full of joy and unforgettable moments!",
                "May happiness follow you wherever you go.",
                "Hope your days are filled with sunshine and joy.",
                "Wishing you a life full of laughter and love.",
                "May every day bring you a reason to smile."
            ]

            # Chọn ngẫu nhiên một đường link từ danh sách
            sticker_url = random.choice(sticker_urls)

            # Chọn ngẫu nhiên một câu chào từ danh sách
            greeting_message = random.choice(greetings)

            # Chọn ngẫu nhiên một câu ngẫu nhiên từ danh sách
            random_message = random.choice(random_messages)

            await interaction.response.send_message(
                content=greeting_message,
                embed=discord.Embed(
                    description=f"_**{random_message}**_ <a:lkn6:1269649714484219987>",
                    color=discord.Color.yellow()
                ).set_image(url=sticker_url)
            )
        else:
            await interaction.response.send_message(
                content="Chức năng này chỉ dành cho đội nghi lễ tiếp khách",
                ephemeral=True
            )

@bot.event
async def on_member_join(member):
    guild = member.guild
    welcome_channel = bot.get_channel(1154671456383414342)  # Sử dụng ID kênh cụ thể

    # Danh sách các câu chào mừng
    greetings = [
        f'Chào mừng {member.mention} đã tham gia vào máy chủ {guild.name}!',
        f'Rất vui vì {member.mention} đã gia nhập máy chủ {guild.name}!'
    ]

    # Chọn ngẫu nhiên một câu chào
    greeting_message = random.choice(greetings)

    # Tạo embed màu đỏ không có tiêu đề
    embed = discord.Embed(
        description=greeting_message,
        color=discord.Color.red()  # Màu đỏ
    )

    # Kiểm tra nếu thành viên có avatar
    if member.avatar:
        # Thêm ảnh đại diện của thành viên vào embed
        embed.set_thumbnail(url=member.avatar.url)

    # Kiểm tra xem kênh có tồn tại không
    if welcome_channel is not None:
        # Tạo và gửi view với nút, truyền thông tin về thành viên mới vào
        view = ButtonView(member)
        await welcome_channel.send(embed=embed, view=view)
bot.run(os.environ.get('TOKEN'))
