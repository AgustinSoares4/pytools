from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# Definimos qué datos necesitamos recibir desde el navegador


class MarcadorPadel(BaseModel):

    puntos_a: str           # Puntos del game actual (0, 15, 30, 40, Ventaja)
    puntos_b: str

    juegos_a: list[int]  # [0, 0, 0]
    juegos_b: list[int]     # [0, 0, 0]

    set_actual: int         # Set actual (0, 1 o 2)

    quien_suma: str         # "A", "B", "restar_A", "restar_B"

    saque: str              # "A" o "B"

    partido_finalizado: bool = False


# (puntos_a, puntos_b, quien_suma)
def gestionar_puntos(a: str, b: str, accion: str):
    """
    Lógica pura de puntos: 0, 15, 30, 40, Ventaja, Juego.
    Devuelve (nuevo_a, nuevo_b)

    Si el equipo A tiene 0 puntos y suma, pasa a 15. De 15 a 30, de 30 a 40, de 40 a Juego (si el otro tiene menos de 40).
    Si ambos tienen 40 y uno suma, pasa a Ventaja.
    Si el que tiene Ventaja suma, gana el juego.
    Si el que no tiene Ventaja suma, vuelve a 40 ambos.
    Y lo mismo para el equipo B.

    También permite restar puntos con "restar_A" y "restar_B", para corregir errores.
    """
    nuevo_a, nuevo_b = a, b

    if "restar" not in accion:
        if accion == "A":
            if a == "0":
                nuevo_a = "15"
            elif a == "15":
                nuevo_a = "30"
            elif a == "30":
                nuevo_a = "40"
            elif a == "40":
                if b in ["0", "15", "30"]:
                    nuevo_a = "Juego"
                elif b == "40":
                    nuevo_a = "Ventaja"
                elif b == "Ventaja":
                    nuevo_b = "40"
            elif a == "Ventaja":
                nuevo_a = "Juego"

        elif accion == "B":
            if b == "0":
                nuevo_b = "15"
            elif b == "15":
                nuevo_b = "30"
            elif b == "30":
                nuevo_b = "40"
            elif b == "40":
                if a in ["0", "15", "30"]:
                    nuevo_b = "Juego"
                elif a == "40":
                    nuevo_b = "Ventaja"
                elif a == "Ventaja":
                    nuevo_a = "40"
            elif b == "Ventaja":
                nuevo_b = "Juego"
    else:
        if accion == "restar_A":
            if a == "15":
                nuevo_a = "0"
            elif a == "30":
                nuevo_a = "15"
            elif a == "40":
                nuevo_a = "30"
            elif a == "Ventaja":
                nuevo_a = "40"
        elif accion == "restar_B":
            if b == "15":
                nuevo_b = "0"
            elif b == "30":
                nuevo_b = "15"
            elif b == "40":
                nuevo_b = "30"
            elif b == "Ventaja":
                nuevo_b = "40"

    return nuevo_a, nuevo_b

# (juegos_a, juegos_b)


def verificar_set(juegos_a: int, juegos_b: int):
    """
    Determina si un equipo ha ganado el set.
    Devuelve "A" si gana el equipo A, "B" si gana el B, o None si el set continúa.

    Si el equipo A llega a 6 juegos con una diferencia de 2, gana el set.
    Si llega a 7 juegos y el otro tiene 5 o 6 (tie-break), gana el set.
    Lo mismo con el equipo B.
    """

    # Lógica para el Equipo A
    if juegos_a >= 6 and (juegos_a - juegos_b) >= 2:
        return "A"
    elif juegos_a == 7 and (juegos_b == 5 or juegos_b == 6):
        return "A"

    # Lógica para el Equipo B
    if juegos_b >= 6 and (juegos_b - juegos_a) >= 2:
        return "B"
    elif juegos_b == 7 and (juegos_a == 5 or juegos_a == 6):
        return "B"

    return None


# Endpoint para reiniciar el partido
@router.post("/reiniciar")
async def reiniciar_partido():
    return {
        "puntos_a": "0",
        "puntos_b": "0",
        "juegos_a": [0, 0, 0],
        "juegos_b": [0, 0, 0],
        "set_actual": 0,
        "saque": "A",
        "partido_finalizado": False
    }


@router.post("/actualizar")
async def actualizar_marcador(data: MarcadorPadel):
    if data.partido_finalizado:
        return data  # Si ya terminó, no hacemos nada

    nuevo_a, nuevo_b = gestionar_puntos(
        data.puntos_a, data.puntos_b, data.quien_suma)

    nuevos_juegos_a = list(data.juegos_a)
    nuevos_juegos_b = list(data.juegos_b)
    nuevo_set_actual = data.set_actual
    nuevo_saque = data.saque
    finalizado = False

    # Lógica de Juego y Saque
    if nuevo_a == "Juego" or nuevo_b == "Juego":
        # 1. Sumar el juego al que corresponda
        if nuevo_a == "Juego":
            nuevos_juegos_a[nuevo_set_actual] += 1
        if nuevo_b == "Juego":
            nuevos_juegos_b[nuevo_set_actual] += 1

        # 2. Reset de puntos
        nuevo_a, nuevo_b = "0", "0"

        # 3. CAMBIO DE SAQUE
        nuevo_saque = "B" if nuevo_saque == "A" else "A"

    # Verificar Set
    ganador_set = verificar_set(
        nuevos_juegos_a[nuevo_set_actual], nuevos_juegos_b[nuevo_set_actual])

    if ganador_set:
        # Aquí una lógica simple: si alguien tiene 2 sets, se acabó.
        # Contamos sets ganados recorriendo las listas
        sets_ganados_a = sum(1 for i in range(3) if verificar_set(
            nuevos_juegos_a[i], nuevos_juegos_b[i]) == "A")
        sets_ganados_b = sum(1 for i in range(3) if verificar_set(
            nuevos_juegos_a[i], nuevos_juegos_b[i]) == "B")

        if sets_ganados_a == 2 or sets_ganados_b == 2 or nuevo_set_actual == 2:
            finalizado = True
        else:
            nuevo_set_actual += 1

    return {
        "puntos_a": nuevo_a,
        "puntos_b": nuevo_b,
        "juegos_a": nuevos_juegos_a,
        "juegos_b": nuevos_juegos_b,
        "set_actual": nuevo_set_actual,
        "saque": nuevo_saque,
        "partido_finalizado": finalizado
    }
