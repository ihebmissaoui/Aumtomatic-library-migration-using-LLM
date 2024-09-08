from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.params import Depends
from starlette.responses import RedirectResponse
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND

from user_repository import UserRepository, create_user_repository, UserFilter,User

app = FastAPI(swagger_ui_default_parameters={"tryItOutEnabled": True})


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.post("/create/", status_code=HTTP_201_CREATED)
def create(email: str, password: str,  name: str, country: str,status: bool, user_repository: UserRepository = Depends(create_user_repository)):
    with user_repository as repo:
        repo.save(User(email=email, password=password, name=name, country=country, status=status,))


@app.get("/user/{email}", response_model=Optional[User])
def get(email: str, user_repository: UserRepository = Depends(create_user_repository)):
    with user_repository as repo:
        user = repo.get_by_email(email)
        if (not user):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
        return user
@app.get("/find",response_model=List[User])
def find (user_filter:UserFilter=Depends(),user_repository:UserRepository = Depends(create_user_repository)):
    with user_repository as repo:
        return repo.get(user_filter)