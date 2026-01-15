from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI(title="PyTools Hub API")

# Esto servirá tus archivos HTML automáticamente
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    # Cuando entres a la web, te mandará al index de tu carpeta static
    return RedirectResponse(url="/static/index.html")


@app.get("/api/health")
def health():
    return {"status": "online", "message": "Ready to build tools!"}
