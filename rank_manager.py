# =========================
# EL MANCHO XP SYSTEM V2
# =========================

RANKS = [
    (0, "Miembro"),
    (100, "Miembro Respetado"),
    (250, "Halconcillo"),
    (500, "Pistolero"),
    (750, "Asesino"),
    (850, "Soldado"),
    (950, "Reclutador"),
    (1000, "Sicario"),
    (1300, "Chofer"),
    (1750, "Teniente"),
    (2500, "Jefe de Plaza"),
    (3000, "Comandante"),
    (3500, "Salamanca Familia"),
    (4500, "Jefe de Operaciones"),
    (5500, "Mano Derecha"),
]


# =========================
# HELPERS
# =========================

def get_rank(index: int):
    return {
        "xp": RANKS[index][0],
        "name": RANKS[index][1]
    }


def get_next(index: int):
    if index + 1 < len(RANKS):
        return RANKS[index + 1]
    return RANKS[index]


def get_threshold(index: int):
    return RANKS[index][0]


# =========================
# CORE SYNC LOGIC (FIXED)
# =========================

async def sync_progress(get_user, update_user, user_id: int, added_xp: int):
    """
    CORE SYSTEM:
    - XP carries over
    - threshold increases per rank
    - multi-level ups supported
    """

    xp, index = await get_user(user_id)

    xp += added_xp

    while index < len(RANKS) - 1:
        threshold = RANKS[index + 1][0]

        if xp >= threshold:
            index += 1
        else:
            break

    await update_user(user_id, xp, index)

    return xp, index


async def remove_progress(get_user, update_user, user_id: int, removed_xp: int):

    xp, index = await get_user(user_id)

    xp -= removed_xp

    while index > 0 and xp < RANKS[index][0]:
        index -= 1

    if xp < 0:
        xp = 0

    await update_user(user_id, xp, index)

    return xp, index
