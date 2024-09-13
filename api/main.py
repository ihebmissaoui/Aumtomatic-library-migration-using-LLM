from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.params import Depends
from starlette.responses import RedirectResponse
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND

from user_repository import UserRepository, create_user_repository, UserFilter, User

app = FastAPI(swagger_ui_default_parameters={"tryItOutEnabled": True})


@app.get("/")
async def root():
    """
    Redirects to the Swagger UI documentation page.

    :return: A redirect response to "/docs".
    """
    return RedirectResponse(url="/docs")


@app.post("/create/", status_code=HTTP_201_CREATED)
async def create(user_data: User,
                 user_repository: UserRepository = Depends(create_user_repository)):
    """
    Create a new user with the provided information.

    Args:
        user_data (User): Pydantic model containing user details
        user_repository (UserRepository): Dependency injection of the user repository

    Returns:
        dict: Success message indicating that the user was created.

    """
    user = User(
        email=user_data.email,
        password=user_data.password,
        name=user_data.name,
        country=user_data.country,
        status=user_data.status
    )

    async with user_repository as repo:
        await repo.save(user)

    return {"message": "User created successfully!"}


@app.get("/user/{email}", response_model=Optional[User])
async def get(email: str, user_repository: UserRepository = Depends(create_user_repository)):
    """
    Retrieves a user by email.

    :param email: Email of the user.
    :param user_repository: Dependency injection for the user repository.
    :return: The user object or raises an HTTP 404 if not found.
    """
    async with user_repository as repo:
        user = await repo.get_by_email(email)
        if not user:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
        return user


@app.get("/find", response_model=List[User])
async def find(user_filter: UserFilter = Depends(),
               user_repository: UserRepository = Depends(create_user_repository)):
    """
    Retrieves a list of users based on the filter criteria.

    :param user_filter: Filter criteria for finding users.
    :param user_repository: Dependency injection for the user repository.
    :return: A list of users matching the filter criteria.
    """
    async with user_repository as repo:
        return await repo.get(user_filter)
