import json
import discord

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

RANKS = CONFIG["ranks"]


def get_rank(index):
    return RANKS[index]


def get_next(index):
    if index + 1 >= len(RANKS):
        return None
    return RANKS[index + 1]


async def sync(member: discord.Member, user_data):
    xp, index = user_data

    rank = get_rank(index)
    role = member.guild.get_role(rank["role_id"])

    # remove old rank roles
    all_roles = [r["role_id"] for r in RANKS]

    to_remove = [
        r for r in member.roles
        if r.id in all_roles
    ]

    if to_remove:
        await member.remove_roles(*to_remove)

    if role not in member.roles:
        await member.add_roles(role)

    return rank


def can_level_up(xp, index):
    # each rank uses fixed threshold (you can adjust)
    return xp >= 100
