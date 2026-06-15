RANKS = [
    (100, "Miembro"),
    (250, "Miembro Respetado"),
    (500, "Halconcillo"),
    (750, "Pistolero"),
    (850, "Asesino"),
    (950, "Soldado"),
    (1000, "Reclutador"),
    (1300, "Sicario"),
    (1750, "Chofer"),
    (2500, "Teniente"),
    (3000, "Jefe de Plaza"),
    (3500, "Comandante"),
    (4500, "Salamanca Familia"),
    (5500, "Jefe de Operaciones"),
    (6000, "Mano Derecha"),
]


# =========================
# CORE XP CONSUME ENGINE
# =========================

async def apply_xp(get_user, update_user, user_id: int, added_xp: int):

    xp = added_xp
    index = 0

    # rebuild from stored state if needed
    _, current_index = await get_user(user_id)

    index = current_index

    while index < len(RANKS) and xp >= RANKS[index][0]:
        xp -= RANKS[index][0]
        index += 1

    await update_user(user_id, xp, index)

    return xp, index
