# uvicorn main:app --host 127.0.0.1 --port 8000 --reload
#http://127.0.0.1:8000/docs - swagger open
# pip install -r requirements.txt
# sphinx-quickstart docs


import re
from ipaddress import ip_address
from typing import Callable
from contextlib import asynccontextmanager
import sys
import os
import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi import FastAPI, status, Request
from fastapi_limiter import FastAPILimiter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.routes.contact_router import router as contact_router
from src.routes.email_router import router as email_router
from src.routes.auth_router import router as auth_router
from src.routes.user_router import router as user_router

# Loads environment variables from a .env file for use in the FastAPI application.
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    The lifespan function initializes a connection to Redis and sets up FastAPI Limiter.

    :param app: The FastAPI application instance.
    """

    r = await redis.Redis(
        host="localhost", port=6379, db=0, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(r)
    yield
    await r.close()


app = FastAPI(lifespan=lifespan)

# Include API routers
app.include_router(contact_router, prefix="/contacts", tags=["contacts"])
app.include_router(email_router, prefix="/email", tags=["email"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, prefix="/user", tags=["user"])

# Adding the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# List of banned IPs
banned_ips = [
    ip_address("192.168.1.1"),
    ip_address("192.168.1.2"),
    # ip_address("127.0.0.1"),  # hometest
]
# CORS settings (Cross-Origin Resource Sharing)
origins = ["*"]

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow all origins
    allow_credentials=True,  # Allow credentials, such as cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers (including 'Authorization')
)

# List of user-agent patterns to ban (regular expressions)
user_agent_ban_list = [
    r"Googlebot",  # Block Googlebot
    r"Python-urllib",  # Block Python urllib user-agent
]


# Middleware to block requests based on banned IPs or user-agent patterns
@app.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    """

    The user_agent_ban_middleware function checks the user-agent and IP address of incoming requests.
    If the IP is banned or the user-agent matches any banned pattern,
    the request is rejected with a 403 Forbidden response.

    :param: request (Request): The incoming request
    :param: call_next (Callable): The next function in the middleware chain
    :returns: JSONResponse: Forbidden response if the IP or user-agent is banned.
        Else, returns the response of the next middleware

    """

    ip = ip_address(request.client.host)
    if ip in banned_ips:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content={"detail": "You are banned"}
        )
    # print(request.headers.get("Authorization")) # Вывод: Bearer your_access_token_here

    user_agent = request.headers.get("user-agent")
    # print(user_agent)
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "You are banned"},
            )
    response = await call_next(request)
    return response

@app.get("/")
def read_root():
    return {"message": "Hello, fastapi application from main.py!"}


@app.get("/healthchecker")
async def root():
    """
    The root function confirm the FastAPI application is up and running.

    Returns: dict.: JSON with  a welcome message indicating that the API is available
    """

    return {"message": "Welcome to FastAPI from healthchecker rout!"}


# if __name__ == '__main__':
#     result=main()
#     import uvicorn
#     uvicorn.run(app, host=config.HOST, port=config)
