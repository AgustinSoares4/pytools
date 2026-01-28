from fastapi import APIRouter, HTTPException
import requests

router = APIRouter()

# Usaremos una URL de acceso libre para este ejemplo
API_URL = "https://open.er-api.com/v6/latest/"


@router.get("/convertir")
async def convertir_divisa(base: str, destino: str, cantidad: float):
    try:
        # Petición a la API de tipos de cambio
        response = requests.get(f"{API_URL}{base}")
        data = response.json()

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al obtener tasas")

        # Cálculo de la conversión
        tasas = data.get("rates", {})
        tasa_destino = tasas.get(destino)

        if not tasa_destino:
            raise HTTPException(status_code=400, detail="Moneda no soportada")

        resultado = cantidad * tasa_destino

        return {
            "cantidad_original": cantidad,
            "moneda_base": base,
            "moneda_destino": destino,
            "tasa": tasa_destino,
            "resultado": round(resultado, 2),
            "ultima_actualizacion": data.get("time_last_update_utc")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
