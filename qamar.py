import os
import json
import discord
from discord import app_commands
from discord.ext import commands

ALLOWED_USER_ID = 298902527846645760
ALLOWED_COMMAND_ROLE_ID = 1507828479666950154

Token = os.env("TOKEN")

COUNTRY_ROLE_NAMES = [
    "Kanada",
    "Zjednoczone Królestwo",
    "Wolna Francja",
    "Włochy",
    "USA",
    "Wielka Rzesza Niemiecka",
    "Japonia",
    "Szwecja",
    "Polska Podziemna",
    "Argentyna",
    "Finlandia",
]

FACTION_ROLE_NAMES = [
    "Einheitspakt",
    "OFN",
    "Dai Toa Kyōeiken",
    "Triumwirat",
]

COUNTRY_TO_FACTION = {
    "Kanada": "OFN",
    "Zjednoczone Królestwo": "Einheitspakt",
    "Wolna Francja": None,
    "Włochy": "Triumwirat",
    "USA": "OFN",
    "Wielka Rzesza Niemiecka": "Einheitspakt",
    "Japonia": "Dai Toa Kyōeiken",
    "Szwecja": None,
    "Polska Podziemna": None,
    "Argentyna": None,
    "Finlandia": None,
}

COUNTRY_TO_CHANNEL_ID = {
    "Kanada": 1521466418221158432,
    "Zjednoczone Królestwo": 1521479709920198686,
    "Wolna Francja": 1521492913857495103,
    "Włochy": 1521829876292915230,
    "USA": 1521905327233171646,
    "Wielka Rzesza Niemiecka": 1521939168790319214,
    "Japonia": 1522237147921383454,
    "Szwecja": 1522742232883663029,
    "Polska Podziemna": 1522936671429984256,
    "Argentyna": 1523038903093952676,
    "Finlandia": 1523040427861606532,
}

FACTION_TO_CHANNEL_ID = {
    "OFN": 1523121316608086069,
    "Einheitspakt": 1523121315748516020,
    "Triumwirat": 1523121318701174866,
    "Dai Toa Kyōeiken": 1523121317707124922,
}

EMBASSY_CATEGORY_ID = 1523370205110075553
NEWSPAPER_CATEGORY_ID = 1523371339149480088
DEV_GUILD_ID = 1507828479624876143
EMBASSY_STATE_FILE = "embassies.json"
NEWSPAPER_STATE_FILE = "newspapers.json"
embassies: dict[str, dict[str, dict[str, int | str]]] = {}
newspapers: dict[str, dict[str, dict[str, int | str]]] = {}

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


async def ensure_role(guild: discord.Guild, role_name: str) -> discord.Role:
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        role = await guild.create_role(name=role_name, permissions=discord.Permissions.none())
    return role


async def grant_channel_access(guild: discord.Guild, role: discord.Role, channel_id: int) -> None:
    channel = guild.get_channel(channel_id)
    if channel is None:
        return
    overwrite = discord.PermissionOverwrite(view_channel=True, send_messages=True)
    await channel.set_permissions(role, overwrite=overwrite)


def has_command_role(member: discord.Member) -> bool:
    if isinstance(member, discord.Member) and (
        member.guild_permissions.administrator or member.id == ALLOWED_USER_ID
    ):
        return True
    return any(role.id == ALLOWED_COMMAND_ROLE_ID for role in member.roles)


def load_embassies() -> None:
    global embassies
    if not os.path.exists(EMBASSY_STATE_FILE):
        embassies = {}
        return
    try:
        with open(EMBASSY_STATE_FILE, "r", encoding="utf-8") as state_file:
            embassies = json.load(state_file)
    except (json.JSONDecodeError, OSError):
        embassies = {}


def save_embassies() -> None:
    try:
        with open(EMBASSY_STATE_FILE, "w", encoding="utf-8") as state_file:
            json.dump(embassies, state_file, ensure_ascii=False, indent=2)
    except OSError:
        pass


def get_embassy_data(guild_id: int, channel_id: int) -> dict[str, int | str] | None:
    return embassies.get(str(guild_id), {}).get(str(channel_id))


def add_embassy(guild_id: int, channel_id: int, founder_id: int, player_id: int, name: str) -> None:
    guild_key = str(guild_id)
    channel_key = str(channel_id)
    embassies.setdefault(guild_key, {})[channel_key] = {
        "founder_id": founder_id,
        "player_id": player_id,
        "name": name,
    }
    save_embassies()


def remove_embassy(guild_id: int, channel_id: int) -> None:
    guild_key = str(guild_id)
    channel_key = str(channel_id)
    guild_embassies = embassies.get(guild_key)
    if not guild_embassies or channel_key not in guild_embassies:
        return
    del guild_embassies[channel_key]
    if not guild_embassies:
        embassies.pop(guild_key, None)
    save_embassies()


def normalize_channel_name(name: str, prefix: str | None = None) -> str:
    sanitized = "".join(
        ch.lower() if ch.isalnum() or ch in "-_" else "-" for ch in name.strip()
    ).strip("-")
    if not sanitized:
        sanitized = prefix or "kanał"
    return sanitized if prefix is None else f"{prefix}-{sanitized}"


def load_newspapers() -> None:
    global newspapers
    if not os.path.exists(NEWSPAPER_STATE_FILE):
        newspapers = {}
        return
    try:
        with open(NEWSPAPER_STATE_FILE, "r", encoding="utf-8") as state_file:
            newspapers = json.load(state_file)
    except (json.JSONDecodeError, OSError):
        newspapers = {}


def save_newspapers() -> None:
    try:
        with open(NEWSPAPER_STATE_FILE, "w", encoding="utf-8") as state_file:
            json.dump(newspapers, state_file, ensure_ascii=False, indent=2)
    except OSError:
        pass


def get_newspaper_data(guild_id: int, channel_id: int) -> dict[str, int | str] | None:
    return newspapers.get(str(guild_id), {}).get(str(channel_id))


def get_newspaper_by_founder(guild_id: int, founder_id: int) -> tuple[str, dict[str, int | str]] | None:
    guild_newspapers = newspapers.get(str(guild_id), {})
    for channel_key, data in guild_newspapers.items():
        if data.get("founder_id") == founder_id:
            return channel_key, data
    return None


def add_newspaper(guild_id: int, channel_id: int, founder_id: int, name: str) -> None:
    guild_key = str(guild_id)
    channel_key = str(channel_id)
    newspapers.setdefault(guild_key, {})[channel_key] = {
        "founder_id": founder_id,
        "creator_id": founder_id,
        "name": name,
    }
    save_newspapers()


def update_newspaper_name(guild_id: int, channel_id: int, name: str) -> None:
    guild_key = str(guild_id)
    channel_key = str(channel_id)
    guild_newspapers = newspapers.get(guild_key)
    if not guild_newspapers or channel_key not in guild_newspapers:
        return
    guild_newspapers[channel_key]["name"] = name
    save_newspapers()


def remove_newspaper(guild_id: int, channel_id: int) -> None:
    guild_key = str(guild_id)
    channel_key = str(channel_id)
    guild_newspapers = newspapers.get(guild_key)
    if not guild_newspapers or channel_key not in guild_newspapers:
        return
    del guild_newspapers[channel_key]
    if not guild_newspapers:
        newspapers.pop(guild_key, None)
    save_newspapers()


@bot.event
async def on_ready() -> None:
    print(f"Zalogowano jako {bot.user}")
    registered = [cmd.name for cmd in bot.tree.walk_commands()]
    print(f"Zarejestrowane komendy slash w drzewie: {registered}")
    guild = bot.get_guild(DEV_GUILD_ID)
    print(f"Bot jest w guild: {bot.guilds}")
    if guild is None:
        print(f"Nie znaleziono guilda o ID {DEV_GUILD_ID}. Nie można zsynchronizować lokalnych komend.")
        return
    try:
        synced_local = await bot.tree.sync(guild=guild)
        print(f"Zsynchronizowano {len(synced_local)} komend slash dla serwera deweloperskiego {DEV_GUILD_ID}")
    except Exception as exc:
        print(f"Błąd synchronizacji komend dla serwera deweloperskiego: {exc}")


@app_commands.default_permissions(administrator=True)
@bot.tree.command(name="setup", description="Tworzy role krajów i frakcji", guild=discord.Object(id=DEV_GUILD_ID))
async def setup(interaction: discord.Interaction) -> None:
    if not interaction.guild:
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    user = interaction.user
    is_allowed = user.guild_permissions.administrator or user.id == ALLOWED_USER_ID
    if not is_allowed:
        await interaction.response.send_message("Nie masz uprawnień do użycia tej komendy.", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message("Bot nie ma uprawnienia Manage Roles.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    created: list[str] = []
    existing: list[str] = []

    for role_name in COUNTRY_ROLE_NAMES + FACTION_ROLE_NAMES:
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role is None:
            await interaction.guild.create_role(name=role_name, permissions=discord.Permissions.none())
            created.append(role_name)
        else:
            existing.append(role_name)

    for country_name in COUNTRY_ROLE_NAMES:
        country_role = await ensure_role(interaction.guild, country_name)
        country_channel_id = COUNTRY_TO_CHANNEL_ID.get(country_name)
        if country_channel_id is not None:
            await grant_channel_access(interaction.guild, country_role, country_channel_id)

        faction_name = COUNTRY_TO_FACTION.get(country_name)
        if faction_name:
            faction_role = await ensure_role(interaction.guild, faction_name)
            faction_channel_id = FACTION_TO_CHANNEL_ID.get(faction_name)
            if faction_channel_id is not None:
                await grant_channel_access(interaction.guild, faction_role, faction_channel_id)

    message = "Gotowe."
    if created:
        message += f" Utworzono role: {', '.join(created)}."
    if existing:
        message += f" Istniejące role: {', '.join(existing)}."

    await interaction.followup.send(message, ephemeral=True)



@app_commands.describe(member="Użytkownik, któremu nadajesz państwo", country="Wybierz państwo")
@app_commands.choices(country=[app_commands.Choice(name=name, value=name) for name in COUNTRY_ROLE_NAMES])
@app_commands.default_permissions(administrator=True)
@bot.tree.command(name="givecountry", description="Nadaje rolę państwa i frakcji użytkownikowi", guild=discord.Object(id=DEV_GUILD_ID))
async def givecountry(interaction: discord.Interaction, member: discord.Member, country: str) -> None:
    if not interaction.guild:
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    user = interaction.user
    is_allowed = user.guild_permissions.administrator or user.id == ALLOWED_USER_ID
    if not is_allowed:
        await interaction.response.send_message("Nie masz uprawnień do użycia tej komendy.", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message("Bot nie ma uprawnienia Manage Roles.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    country_role = await ensure_role(interaction.guild, country)
    faction_name = COUNTRY_TO_FACTION.get(country)
    faction_role = await ensure_role(interaction.guild, faction_name) if faction_name else None

    country_channel_id = COUNTRY_TO_CHANNEL_ID.get(country)
    if country_channel_id is not None:
        await grant_channel_access(interaction.guild, country_role, country_channel_id)

    if faction_role is not None:
        faction_channel_id = FACTION_TO_CHANNEL_ID.get(faction_role.name)
        if faction_channel_id is not None:
            await grant_channel_access(interaction.guild, faction_role, faction_channel_id)

    roles_to_remove = [
        role for role in member.roles
        if role.name in COUNTRY_ROLE_NAMES + FACTION_ROLE_NAMES
    ]
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="Zmieniono państwo")

    await member.add_roles(country_role, reason="Nadaję państwo")
    if faction_role is not None:
        await member.add_roles(faction_role, reason="Nadaję frakcję")

    message = f"Nadano {member.mention} rolę państwa: {country}"
    if faction_role is not None:
        message += f" oraz frakcji: {faction_role.name}"

    await interaction.followup.send(message, ephemeral=True)



@app_commands.default_permissions(administrator=True)
@bot.tree.command(name="givecoountry", description="Alias komendy givecountry", guild=discord.Object(id=DEV_GUILD_ID))
async def givecoountry(interaction: discord.Interaction, member: discord.Member, country: str) -> None:
    await givecountry(interaction, member, country)


@bot.command(name="synccommands")
async def synccommands(ctx: commands.Context) -> None:
    if ctx.guild:
        try:
            synced = await bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"Zsynchronizowano {len(synced)} komend slash dla serwera {ctx.guild.id}.")
        except Exception as exc:
            await ctx.send(f"Błąd synchronizacji komend dla serwera: {exc}")
    else:
        try:
            synced = await bot.tree.sync()
            await ctx.send(f"Zsynchronizowano {len(synced)} komend slash globalnie.")
        except Exception as exc:
            await ctx.send(f"Błąd globalnej synchronizacji komend: {exc}")



@app_commands.describe(member="Użytkownik, dla którego tworzysz ambasadę", name="Nazwa kanału ambasady")
@bot.tree.command(name="ambasada", description="Tworzy prywatny kanał ambasady dla założyciela i gracza", guild=discord.Object(id=DEV_GUILD_ID))
async def ambasada(interaction: discord.Interaction, member: discord.Member, name: str) -> None:
    if not interaction.guild:
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if not has_command_role(interaction.user):
        await interaction.response.send_message("Nie masz wymaganej roli, aby użyć tej komendy.", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.manage_channels:
        await interaction.response.send_message("Bot nie ma uprawnień Manage Channels.", ephemeral=True)
        return

    category = interaction.guild.get_channel(EMBASSY_CATEGORY_ID)
    if category is None or not isinstance(category, discord.CategoryChannel):
        await interaction.response.send_message("Nie znaleziono kategorii ambasady.", ephemeral=True)
        return

    channel_name = normalize_channel_name(name)
    existing_names = {channel.name for channel in category.channels}
    suffix = 1
    unique_name = channel_name
    while unique_name in existing_names:
        suffix += 1
        unique_name = f"{channel_name}-{suffix}"

    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True, send_messages=True),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }

    channel = await interaction.guild.create_text_channel(
        name=unique_name,
        category=category,
        overwrites=overwrites,
        reason="Tworzenie ambasady",
    )

    add_embassy(interaction.guild.id, channel.id, interaction.user.id, member.id, name)
    await interaction.response.send_message(
        f"Utworzono kanał {channel.mention} w kategorii ambasady. Tylko ty i {member.mention} macie dostęp.",
        ephemeral=True,
    )



@app_commands.describe(name="Nazwa Twojej gazety")
@bot.tree.command(name="stworzgazete", description="Tworzy kanał gazety i zapisuje, kto jest twórcą", guild=discord.Object(id=DEV_GUILD_ID))
async def stworzgazete(interaction: discord.Interaction, name: str) -> None:
    if not interaction.guild:
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if not has_command_role(interaction.user):
        await interaction.response.send_message("Nie masz wymaganej roli, aby użyć tej komendy.", ephemeral=True)
        return

    if get_newspaper_by_founder(interaction.guild.id, interaction.user.id) is not None:
        await interaction.response.send_message("Masz już jedną gazetę. Nie możesz stworzyć kolejnej.", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.manage_channels:
        await interaction.response.send_message("Bot nie ma uprawnień Manage Channels.", ephemeral=True)
        return

    category = interaction.guild.get_channel(NEWSPAPER_CATEGORY_ID)
    if category is None or not isinstance(category, discord.CategoryChannel):
        await interaction.response.send_message("Nie znaleziono kategorii gazety.", ephemeral=True)
        return

    channel_name = normalize_channel_name(name)
    existing_names = {channel.name for channel in category.channels}
    suffix = 1
    unique_name = channel_name
    while unique_name in existing_names:
        suffix += 1
        unique_name = f"{channel_name}-{suffix}"

    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
        interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }

    channel = await interaction.guild.create_text_channel(
        name=unique_name,
        category=category,
        overwrites=overwrites,
        reason="Tworzenie gazety",
    )

    add_newspaper(interaction.guild.id, channel.id, interaction.user.id, name)
    await interaction.response.send_message(
        f"Utworzono gazetę {channel.mention}. Tylko ty możesz w niej pisać.",
        ephemeral=True,
    )



@app_commands.describe(name="Nowa nazwa gazety")
@bot.tree.command(name="gazetanazwa", description="Zmienia nazwę kanału gazety tylko dla założyciela", guild=discord.Object(id=DEV_GUILD_ID))
async def gazetanazwa(interaction: discord.Interaction, name: str) -> None:
    if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message("Ta komenda działa tylko na kanale tekstowym na serwerze.", ephemeral=True)
        return

    if not has_command_role(interaction.user):
        await interaction.response.send_message("Nie masz wymaganej roli, aby użyć tej komendy.", ephemeral=True)
        return

    newspaper_data = get_newspaper_data(interaction.guild.id, interaction.channel.id)
    if newspaper_data is None:
        await interaction.response.send_message("To nie jest kanał gazety zarządzany przez bota.", ephemeral=True)
        return

    is_founder = interaction.user.id == newspaper_data.get("founder_id")
    is_admin = isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator

    if not is_founder and not is_admin:
        await interaction.response.send_message("Tylko założyciel gazety lub administrator może zmienić jej nazwę.", ephemeral=True)
        return

    new_channel_name = normalize_channel_name(name)
    existing_names = {channel.name for channel in interaction.guild.channels if isinstance(channel, discord.TextChannel)}
    suffix = 1
    unique_name = new_channel_name
    while unique_name in existing_names and unique_name != interaction.channel.name:
        suffix += 1
        unique_name = f"{new_channel_name}-{suffix}"

    await interaction.channel.edit(name=unique_name, reason="Zmiana nazwy gazety")
    update_newspaper_name(interaction.guild.id, interaction.channel.id, name)
    await interaction.response.send_message(
        f"Nazwa gazety została zmieniona na {unique_name}.",
        ephemeral=True,
    )



@bot.tree.command(name="usungazete", description="Usuwa Twoją gazetę", guild=discord.Object(id=DEV_GUILD_ID))
async def usungazete(interaction: discord.Interaction) -> None:
    if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message("Ta komenda działa tylko na kanale tekstowym.", ephemeral=True)
        return

    newspaper_data = get_newspaper_data(interaction.guild.id, interaction.channel.id)
    if newspaper_data is None:
        await interaction.response.send_message("To nie jest kanał gazety zarządzany przez bota.", ephemeral=True)
        return

    is_founder = interaction.user.id == newspaper_data.get("founder_id")
    is_admin = isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator

    if not is_founder and not is_admin:
        await interaction.response.send_message("Tylko założyciel gazety lub administrator może ją usunąć.", ephemeral=True)
        return

    await interaction.response.send_message("Usuwanie gazety...", ephemeral=True)
    await interaction.channel.delete(reason="Usuwanie gazety na prośbę użytkownika")



@bot.tree.command(name="usunambasade", description="Usuwa ambasadę, której jesteś założycielem", guild=discord.Object(id=DEV_GUILD_ID))
async def usunambasade(interaction: discord.Interaction) -> None:
    if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message("Ta komenda działa tylko na kanale tekstowym.", ephemeral=True)
        return

    embassy_data = get_embassy_data(interaction.guild.id, interaction.channel.id)
    if embassy_data is None:
        await interaction.response.send_message("To nie jest kanał ambasady zarządzany przez bota.", ephemeral=True)
        return

    is_founder = interaction.user.id == embassy_data.get("founder_id")
    is_admin = isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator

    if not is_founder and not is_admin:
        await interaction.response.send_message("Tylko założyciel ambasady lub administrator może ją usunąć.", ephemeral=True)
        return

    await interaction.response.send_message("Usuwanie ambasady...", ephemeral=True)
    await interaction.channel.delete(reason="Usuwanie ambasady na prośbę użytkownika")



@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel) -> None:
    if not isinstance(channel, discord.TextChannel):
        return
    remove_embassy(channel.guild.id, channel.id)
    remove_newspaper(channel.guild.id, channel.id)


load_embassies()
load_newspapers()

bot.run(Token)
