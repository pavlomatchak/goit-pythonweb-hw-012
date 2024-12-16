from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
import cloudinary
import cloudinary.uploader
import aioredis

from api import utils, contacts, auth, users

app = FastAPI()

origins = [
  "<http://localhost:3000>"
]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
  return JSONResponse(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    content={"error": "Перевищено ліміт запитів. Спробуйте пізніше."},
  )

@app.on_event("startup")
async def startup():
  app.state.redis = await aioredis.from_url("redis://localhost", decode_responses=True)

@app.on_event("shutdown")
async def shutdown():
  await app.state.redis.close()

app.include_router(utils.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")

cloudinary.config(
  cloud_name="your_cloud_name",
  api_key="your_api_key",
  api_secret="your_api_secret"
)

if __name__ == "__main__":
  import uvicorn

  uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

