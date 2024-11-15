from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.conf.config import settings
from src.database.db import get_db
from src.repository import users as repository_users



class Auth:
    # CryptContext is used to handle password hashing and verification (bcrypt in this case)
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = settings.ALGORITHM
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
    # r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)
    
    def verify_password(self, plain_password, hashed_password):
        """
        The verify_password function verifies that the plain text password matches the hashed password.

        :param self: Represent the instance of the class
        :param: plain_password (str): The plain text password entered by the user
        :param: hashed_password (str): The stored hashed password to compare against

        :return: bool: True if the passwords match, otherwise False
        """

        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        The get_password_hash function hashes a plain text password.

        :param self: Represent the instance of the class
        :param password: str: plain text password 
        :return: str: A bcrypt hashed version of the password
        """
        return self.pwd_context.hash(password)


    async def create_access_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        The create_access_token function creates an access token based on the provided data and expiration time.

        :param self: Refer to the instance of the class
        :param data: dict: Store the data that is to be encoded into the access token
        :param expires_delta: Optional[float]: Set the expiration time of the token
        :return: An encoded access token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now() + timedelta(minutes=15)
        # to_encode.update({"exp": expire})
        to_encode.update(
            {"iat": datetime.now(), "exp": expire, "scope": "access_token"}
        )
        encoded_access_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        # encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_access_token

    async def create_refresh_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        The create_refresh_token function creates a refresh token.

        :param self: Represent the instance of the class
        :param data: dict: Pass the data that will be encoded in the token
        :param expires_delta: Optional[float]: Set the expiration time of the token
        :return: An encoded refresh token
        """

        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now() + timedelta(days=7)
        to_encode.update(
            {"iat": datetime.now(), "exp": expire, "scope": "refresh_token"}
        )  # datetime.utcnow() ?
        encoded_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        """
        The get_current_user function is a dependency that will be used to retrieve the current user.
        It uses the OAuth2PasswordBearer scheme to validate and decode JWT tokens.
        If credentials are invalid or if no user with such email exists, it raises an HTTPException.

        :param self: Refer to the class itself
        :param token: str: Get the token from the request header
        :param db: Session: Get the database session
        :return: The current user based on the provided token
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        return user

    def create_email_token(self, data: dict):
        """
        The create_email_token function creates a JWT token using the provided data dictionary.
        The function takes in a self parameter, which is an instance of the class, and a data parameter,
        which is a dictionary containing the data to encode. The function then copies this data into another
        dictionary called to_encode and adds two additional keys: iat (issued at) and exp (expiration).
        The iat key contains the current time in UTC format while exp contains 7 days from now in UTC format.
        Finally, we use jwt's encode method to create our token with our secret key.

        :param self: Refer to the instance of the class
        :param data: dict: Pass in a dictionary containing the data to encode
        :return: A jwt token encoded with the provided data and secret key
        """
        to_encode = data.copy()
        expire = datetime.now() + timedelta(days=7)  # datetime.datetime.now
        to_encode.update({"iat": datetime.now(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        """
        Decodes a JWT token to extract the email address from its payload.
        The get_email_from_token function takes a token string as input and attempts to decode it using the SECRET_KEY and ALGORITHM.
        If successful, it extracts the email from the decoded payload and returns it.
        If an exception of type JWTError is caught, it prints the error and raises an HTTPException with status code 422
        and detail &quot;Invalid token for email verification&quot;.

        :param self: Refers to the instance of the class
        :param token: str: The JWT token string to be decoded
        :raise: exeption HTTP_422_UNPROCESSABLE_ENTITY: indicating an invalid token for email verification
        :return: The email string extracted from the decoded JWT token
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )
        

    async def get_email_from_refresh_token(self, refresh_token: str):
        """
        The get_email_from_refresh_token function decodes a refresh token to extract the email address and validate its scope.

        :param self: Refers to the instance of the class
        :param refresh_token: str: The refresh token string
        :exeption HTTP_401_UNAUTHORIZED: If the token has an invalid scope or cannot be validated
        :return: str: The email address extracted from the decoded refresh token
        """
         
        try:
            payload = jwt.decode(refresh_token,  self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

auth_service = Auth()