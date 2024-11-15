
from fastapi import APIRouter, BackgroundTasks, Depends, Request, status, HTTPException, Response
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_mail.errors import ConnectionErrors

from src.conf.config import settings
from src.database.db import get_db
from src.schemas import EmailSchema, RequestEmail
from src.services.send_email import send_email
from src.repository import users as repositories_users
#from src.repository.users import get_user_by_email, confirmed_email
from src.services.auth import auth_service

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME="goithw13",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=settings.TEMPLATE_FOLDER,
)   

router = APIRouter()
fm = FastMail(conf)

@router.post("/send-email")
async def send_in_background(background_tasks: BackgroundTasks, body: EmailSchema):
    """
    The send_in_background function generates a verification token and sends a verification email asynchronously using background tasks.
    The email includes a link with the token that can be used for email verification.

    :param background_tasks: The FastAPI BackgroundTasks instance that allows the task 
                              to be processed asynchronously.
    :param body: The body of the request containing the user's email and optional fullname.

    :return: A dictionary with a success message if the email was successfully queued 
             for sending.
    
    :raise: HTTPException: 
        - If there is a connection error when attempting to send the email.
        - If any other unexpected error occurs during the process.
    """
    try:
        token_verification = auth_service.create_email_token({"sub": body.email})
        message = MessageSchema(
            subject="Fastapi mail module",
            recipients=[body.email],
            template_body={"fullname": "Bill Murray", "host": "http://127.0.0.1:8000", "token": token_verification},
            subtype=MessageType.html
        )
        background_tasks.add_task(fm.send_message, message, template_name="email_template.html")
        return {"message": "Email has been sent"}
    except ConnectionErrors as err:
        print(f"Connection error: {err}")
        return {"error": "Failed to connect to the email server"}
    except Exception as e:
        print(f"General error: {e}")
        return {"error": "An unexpected error occurred"}

@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    The confirmed_email function confirms the user's email address using the provided token.
    
    :param token: str: Retrieve the email from the token
    :param db: AsyncSession: Pass in the database session
    :raise: HTTPException: HTTP_400_BAD_REQUEST If user's email is already confirmed
    :return: A success message after the user's email confirmed
    """

    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repositories_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    The request_email function checks if the user's email is already confirmed
    
    :param body: The request body containing the user's email address
    :param background_tasks: The FastAPI BackgroundTasks instance that allows the 
                              email verification task to be processed asynchronously
    :param db: AsyncSession: Pass in the database session
    :return: dict.: A message indicating whether the email was already 
             confirmed or if the user should check their inbox for the verification email
    """
    
    user = await repositories_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation."}

