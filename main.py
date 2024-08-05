#uvicorn main:app --host 127.0.0.1 --port 8000 --reload
import sys 
import os
from dotenv import load_dotenv
from fastapi import FastAPI


from src.routes.contact_router import router as contact_router
from src.routes.email_router import router as email_router
from src.routes.auth_router import router as auth_router
#from src.conf import config    
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

app = FastAPI()

app.include_router(contact_router, prefix="/contacts", tags=["contacts"])
app.include_router(email_router, prefix="/email", tags=["email"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/api/healthchecker")
def root():
    return {"message": "Welcome to FastAPI!"}


# if __name__ == '__main__':
#     result=main()
#     import uvicorn
#     uvicorn.run(app, host=config.HOST, port=config