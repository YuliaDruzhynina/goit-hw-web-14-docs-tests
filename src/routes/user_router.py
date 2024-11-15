from fastapi import APIRouter, Depends, UploadFile, File
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary
import cloudinary.uploader

from src.database.db import get_db
from src.entity.models import User
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.conf.config import settings
from src.schemas import UserResponse

# Initialize a FastAPI APIRouter instance for the current module or endpoint group
router = APIRouter()
# Configure Cloudinary settings with the credentials provided in the app's settings
cloudinary.config(
    cloud_name=settings.CLOUDINARY_NAME, # Cloudinary cloud name from app settings
    api_key=settings.CLOUDINARY_API_KEY, # Cloudinary API key from app settings
    api_secret=settings.CLOUDINARY_API_SECRET, # Cloudinary API secret from app settings
    secure=True, # Enable secure URLs for media
    )

@router.get("/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    """
    The read_users_me function returns the details of the currently authenticated user
    
    :param current_user: The currently authenticated user, automatically injected 
                          by FastAPI's `Depends` function and the authentication service
    :return: UserResponse: model containing the user's details (e.g., username, email, etc.)
    """
    return current_user


@router.patch(
    "/avatar",
    response_model=UserResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))],
)
async def update_avatar_url(
    file: UploadFile = File(),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    The update_avatar_url function udates the avatar URL for the currently authenticated user.
    
    :param file: The image file to be uploaded as the user's avatar by user
    :param current_user: get current_user object with UserResponse model from Depends User object
    :param Depends(RateLimiter): Rate-limited to 1 request per 20 seconds.
    :param db: AsyncSession: get the database session for the request
    :return: The updated user object with the new avatar URL
    """
    
    public_id = f"cloud_store/{current_user.email}"
    #print(f"Generated public_id: {public_id}")
    resource = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
    #print(resource)
    res_url = cloudinary.CloudinaryImage(f'cloud_store/{current_user.email}')\
                        .build_url(width=250, height=250, crop='fill', version=resource.get('version'))
    user = await repository_users.update_avatar_url(current_user.email, res_url, db)
    return user
