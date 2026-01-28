from api.routes import currency, padel
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


app = FastAPI(title="PyTools Hub API")


@app.get("/")
async def root():
    # Cuando entres a la web, te mandará al index de tu carpeta static
    index_path = os.path.join("static", "index.html")
    return FileResponse(index_path)


@app.get("/api/health")
def health():
    return {"status": "online", "message": "Ready to build tools!"}


# Incluimos las rutas del submódulo de pádel
app.include_router(padel.router, prefix="/api/padel", tags=["Padel"])
app.include_router(currency.router, prefix="/api/currency", tags=["Currency"])

# Esto servirá tus archivos HTML automáticamente
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
