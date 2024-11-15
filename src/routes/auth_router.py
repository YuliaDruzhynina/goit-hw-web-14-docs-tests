from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Security,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from src.database.db import get_db, get_redis_client
from src.entity.models import User
from src.schemas import UserModel, TokenModel, UserResponse
from src.services.auth import auth_service

from src.services.send_email import send_email
from src.repository import users as repositories_users


router = APIRouter()

security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserModel,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    The signup function creates a new user account.

    :param body: UserModel: Get the user data to be created. The user data (email, password, etc.)
    :param background_tasks: BackgroundTasks: Execute the send_email function asynchronously.
       Sends a confirmation email in the background.
    :param request: Request: Get the base url of the application for email verification
    :param db: AsyncSession: Access to the database
    :raise: HTTPException: 409_CONFLICT if "An account with this email already exists"
    :return: UserResponse: dict. The created user object with response details
    """

    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body, db)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )
    return new_user


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    The login function authenticates a user and returns access and refresh JWT tokens.

    :param body: OAuth2PasswordRequestForm: Validate the request body using the username (email) and password
    :param db: AsyncSession : Pass the database session to the function
    :raise: HTTPException: 401_UNAUTHORIZED if email is invalide
    :raise: HTTPException: 401_UNAUTHORIZED if email doesn't confirmed
    :raise: HTTPException: 401_UNAUTHORIZED if password is invalide
    :return: TokenModel: A JSON object
    """

    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    # Generate JWT
    access_token = await auth_service.create_access_token(
        data={"sub": user.email, "test": "коза-дереза"}
    )
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repositories_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(
        security
    ),  # HTTPAuthorizationCredentials = Depends(get_refresh_token)
    db: AsyncSession = Depends(get_db),
):
    """
    The refresh_token function is used to refresh the access token using the a valid refresh token.

    :param credentials: HTTPAuthorizationCredentials: Get the credentials from the request
    :param db: AsyncSession: Connect to the database. The database session to query the user data
    :raise: HTTPException: 401_UNAUTHORIZED if refresh token is invalid
    :return: TokenModel: A JSON object. A dictionary of the access token, refresh token and bearer
    """

    token = credentials.credentials
    email = await auth_service.get_email_from_refresh_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repositories_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    user.refresh_token = refresh_token
    await repositories_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/secret")
async def read_item(user: User = Depends(auth_service.get_current_user)):
    """
    The read_item function requires a valid authentication token and returns the
    authenticated user's email. Test of protected route for authenticated users.

    :param user: User: The current authenticated user, obtained from the auth service
    :return: dict: A message and the email of the authenticated user
    """

    return {"message": "secret router", "owner": user.email}


@router.post("/test_cache/set")
async def set_cache(
    key: str, value: str, redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    The set_cache function stores a key-value pair in Redis for later retrieval.
    
    :param key: str: The cache key
    :param value: str: The value associated with the key
    :param redis_client: Redis: The Redis client to interact with the cache
    :return: dict: Confirmation message
    """
    await redis_client.set(key, value)


@router.get("/test_cache/get/{key}")
async def get_cache(key: str, redis_client: redis.Redis = Depends(get_redis_client)):
    """
     The get_cache function retrieves the value associated with the provided key from Redis.

    :param key: str: The cache key to retrieve
    :param redis_client: Redis: The Redis client to interact with the cache
    :return: dict: The key-value pair from the cache
    """
    value = await redis_client.get(key)
    return {key: value}
