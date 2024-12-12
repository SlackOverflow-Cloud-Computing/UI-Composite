import logging
from fastapi import Depends, FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from app.routers import users
from app.routers import playlists
from app.routers import recommendations

app = FastAPI()

# origins = [
#     "http://localhost:3000" # React UI
# ]

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=["*"]
)



app.include_router(users.router)
app.include_router(playlists.router)
app.include_router(recommendations.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
