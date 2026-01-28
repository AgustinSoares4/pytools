from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# Definimos qué datos necesitamos recibir desde el navegador

# Mirar y buscar errores o cositas que falten.
# Por ej, cuando hay AD - 40, y se resta el de 40, queda AD - 30, que no es válido. Plantear que hacemos ahi.


class MarcadorPadel(BaseModel):

    puntos_a: str           # Puntos del game actual (0, 15, 30, 40, Ventaja)
    puntos_b: str

    juegos_a: list[int]  # [0, 0, 0]
    juegos_b: list[int]     # [0, 0, 0]

    set_actual: int         # Set actual (0, 1 o 2)

    quien_suma: str         # "A", "B", "restar_A", "restar_B"

    saque: str              # "A" o "B"

    es_tiebreak: bool = False 
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
        # Suma un punto para el equipo A
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
                    nuevo_a = "AD"
                elif b == "AD":
                    nuevo_b = "40"
            elif a == "AD":
                nuevo_a = "Juego"
        # Suma un punto para el equipo B
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
                    nuevo_b = "AD"
                elif a == "AD":
                    nuevo_a = "40"
            elif b == "AD":
                nuevo_b = "Juego"
    else:
        # Resta un punto para el equipo A
        if accion == "restar_A":
            if a == "15":
                nuevo_a = "0"
            elif a == "30":
                nuevo_a = "15"
            elif a == "40":
                nuevo_a = "30"
            elif a == "AD":
                nuevo_a = "40"
        # Suma un punto para el equipo B
        elif accion == "restar_B":
            if b == "15":
                nuevo_b = "0"
            elif b == "30":
                nuevo_b = "15"
            elif b == "40":
                nuevo_b = "30"
            elif b == "AD":
                nuevo_b = "40"

    return nuevo_a, nuevo_b


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


def gestionar_puntos_tiebreak(a: str, b: str, accion: str):
    p_a, p_b = int(a), int(b)

    # Aplicación de la acción (Sumar o Restar)
    if "restar" not in accion:
        if accion == "A":
            p_a += 1
        else:
            p_b += 1
    else:
        if "A" in accion and p_a > 0:
            p_a -= 1
        if "B" in accion and p_b > 0:
            p_b -= 1

    # Verificación de condición de victoria (7 puntos y diferencia de 2)
    # Si se cumple, devolvemos los puntos y 'False' para cerrar el modo Tie-break
    if (p_a >= 7 or p_b >= 7) and abs(p_a - p_b) >= 2:
        return str(p_a), str(p_b), False

    return str(p_a), str(p_b), True



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
    # Paso 1: Bloqueo de seguridad si el partido ya terminó
    if data.partido_finalizado:
        return data

    # Paso 2: Inicialización de variables de estado local
    nuevo_set = data.set_actual
    juegos_a = list(data.juegos_a)
    juegos_b = list(data.juegos_b)
    saque = data.saque
    modo_tiebreak = data.es_tiebreak
    finalizado = False

    # Paso 3: Activación del modo Tie-break al llegar a 6-6
    if juegos_a[nuevo_set] == 6 and juegos_b[nuevo_set] == 6:
        modo_tiebreak = True

    # Paso 4: Cálculo de puntos según el modo de juego (Normal o Tie-break)
    if modo_tiebreak:
        nuevo_a, nuevo_b, sigue = gestionar_puntos_tiebreak(
            data.puntos_a, data.puntos_b, data.quien_suma)

        if not sigue:  # El Tie-break ha finalizado
            if data.quien_suma == "A":
                juegos_a[nuevo_set] += 1
            else:
                juegos_b[nuevo_set] += 1
            nuevo_a, nuevo_b, modo_tiebreak = "0", "0", False
            saque = "B" if saque == "A" else "A"
        else:  # Rotación de saque cada 2 puntos en Tie-break
            if "restar" not in data.quien_suma:
                puntos_totales = int(nuevo_a) + int(nuevo_b)
                if puntos_totales % 2 != 0:
                    saque = "B" if saque == "A" else "A"
    else:
        nuevo_a, nuevo_b = gestionar_puntos(data.puntos_a, data.puntos_b, data.quien_suma)

        # Paso 5: Gestión de victoria de juego normal y cambio de saque
        if nuevo_a == "Juego" or nuevo_b == "Juego":
            if nuevo_a == "Juego":
                juegos_a[nuevo_set] += 1
            else:
                juegos_b[nuevo_set] += 1
            nuevo_a, nuevo_b = "0", "0"
            saque = "B" if saque == "A" else "A"

    # Paso 6: Verificación de ganador de Set y actualización de la progresión
    ganador_set = verificar_set(juegos_a[nuevo_set], juegos_b[nuevo_set])
    if ganador_set:
        # Cálculo de sets totales para determinar fin del partido
        sets_a = sum(1 for i in range(3) if verificar_set(juegos_a[i], juegos_b[i]) == "A")
        sets_b = sum(1 for i in range(3) if verificar_set(juegos_a[i], juegos_b[i]) == "B")
        if sets_a == 2 or sets_b == 2 or nuevo_set == 2:
            finalizado = True
        else:
            nuevo_set += 1

    # Paso 7: Retorno del nuevo estado sincronizado
    return {
        "puntos_a": nuevo_a,
        "puntos_b": nuevo_b,
        "juegos_a": juegos_a,
        "juegos_b": juegos_b,
        "set_actual": nuevo_set,
        "saque": saque,
        "partido_finalizado": finalizado,
        "es_tiebreak": modo_tiebreak
    }
