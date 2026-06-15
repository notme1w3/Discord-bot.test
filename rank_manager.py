import json
import discord

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

RANKS = sorted(CONFIG["ranks"], key=lambda r: r["xp"])


def get_rank(xp):
    rank = RANKS[0]
    for r in RANKS:
        if xp >= r["xp"]:
            rank = r
        else:
            break
    return rank


def get_next(xp):
    for r in RANKS:
        if r["xp"] > xp:
            return r
    return None


def progress(xp):
    current = get_rank(xp)
    nxt = get_next(xp)

    if not nxt:
        return 100, current, None, 0

    total = nxt["xp"] - current["xp"]
    done = xp - current["xp"]

    pct = int((done / total) * 100)
    return pct, current, nxt, nxt["xp"] - xp


def bar(pct):
    filled = pct // 10
    return "█" * filled + "░" * (10 - filled)


async def sync(member: discord.Member, xp: int):
    guild = member.guild
    target = get_rank(xp)
    role = guild.get_role(target["role_id"])

    if not role:
        return None

    all_ids = [r["role_id"] for r in RANKS]

    to_remove = [
        r for r in member.roles
        if r.id in all_ids and r.id != role.id
    ]

    if to_remove:
        await member.remove_roles(*to_remove)

    if role not in member.roles:
        await member.add_roles(role)
        return target

    return None
