from fastapi import FastAPI
from app.api.endpoints import router as player_router
from app.db.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Valorant Player Service",
    description="Сервис для управления профилями игроков и рейтингом",
    version="1.0.0"
)

app.include_router(player_router, prefix="/api/v1", tags=["Players"])

@app.get("/")
def health_check():
    return {"status": "alive", "service": "player-service"}