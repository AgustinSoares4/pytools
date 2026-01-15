from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# Definimos qué datos necesitamos recibir desde el navegador


class MarcadorPadel(BaseModel):
    # Puntos del game actual (0, 15, 30, 40, Ventaja)
    puntos_a: str
    puntos_b: str
    # Juegos ganados en cada set (Ej: [6, 3, 0])
    juegos_a: list[int]
    juegos_b: list[int]
    # Set actual (0, 1 o 2)
    set_actual: int
    # Quién realiza la acción
    quien_suma: str  # "A", "B", o incluso podríamos añadir "restar_A", "restar_B"


def gestionar_puntos(a: str, b: str, accion: str):
    """
    Lógica pura de puntos: 0, 15, 30, 40, Ventaja, Juego.
    Devuelve (nuevo_a, nuevo_b)
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


def verificar_set(juegos_a: int, juegos_b: int):
    """
    Determina si un equipo ha ganado el set.
    Devuelve "A" si gana el equipo A, "B" si gana el B, o None si el set continúa.
    """

    # Lógica para el Equipo A
    if juegos_a >= 6 and (juegos_a - juegos_b) >= 2:
        return "A"
    elif juegos_a == 7 and juegos_b == 5:
        return "A"
    elif juegos_a == 7 and juegos_b == 6:  # Caso Tie-break (7-6)
        return "A"

    # Lógica para el Equipo B
    if juegos_b >= 6 and (juegos_b - juegos_a) >= 2:
        return "B"
    elif juegos_b == 7 and juegos_a == 5:
        return "B"
    elif juegos_b == 7 and juegos_a == 6:  # Caso Tie-break (7-6)
        return "B"

    return None


@router.post("/actualizar")
async def actualizar_marcador(data: MarcadorPadel):
    # 1. Calculamos los puntos
    nuevo_a, nuevo_b = gestionar_puntos(
        data.puntos_a, data.puntos_b, data.quien_suma)

    # Copiamos datos actuales para no modificar el original directamente
    nuevos_juegos_a = list(data.juegos_a)
    nuevos_juegos_b = list(data.juegos_b)
    nuevo_set_actual = data.set_actual

    # 2. ¿Alguien ganó un juego?
    if nuevo_a == "Juego":
        nuevos_juegos_a[nuevo_set_actual] += 1
        nuevo_a, nuevo_b = "0", "0"  # Reset de puntos

    elif nuevo_b == "Juego":
        nuevos_juegos_b[nuevo_set_actual] += 1
        nuevo_a, nuevo_b = "0", "0"  # Reset de puntos

    # 3. Verificamos si con ese nuevo juego alguien cerró el SET
    ganador_set = verificar_set(nuevos_juegos_a[nuevo_set_actual],
                                nuevos_juegos_b[nuevo_set_actual])

    if ganador_set:
        # Si el set terminó, pasamos al siguiente (si no es el último)
        if nuevo_set_actual < 2:
            nuevo_set_actual += 1
        else:
            print(f"¡Partido terminado! Ganador: {ganador_set}")
            # Aquí podrías añadir una variable 'partido_finalizado': True

    return {
        "puntos_a": nuevo_a,
        "puntos_b": nuevo_b,
        "juegos_a": nuevos_juegos_a,
        "juegos_b": nuevos_juegos_b,
        "set_actual": nuevo_set_actual
    }
