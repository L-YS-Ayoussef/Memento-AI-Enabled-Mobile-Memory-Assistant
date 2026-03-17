from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from app.db.business_db import get_db
from app.schemas import schemas
from app.models import models
from app.utils.helpers import verify_password, hash_password
from app.core.security import create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from pydantic import ValidationError
from app.db.vector_store.vector_store import vector_store

router = APIRouter(
    tags=["Authentication"]
)

@router.post("/login", status_code=status.HTTP_200_OK, response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint.
    
    Args:
        user_credentials: must be sent as form data with 'username' (could be the email but field must be username) and 'password'.
        {
            "username": ""
            "password": ""
        }
    """
    user = db.query(models.User).filter(
        models.User.email == user_credentials.username      # using username field to accept email,
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid email or password"
        )
    
    if not verify_password(
        plain_password=user_credentials.password,
        hashed_password=user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid email or password"
        )
    
    # return the JWT token
    access_token = create_access_token(
        data={"user_id": user.id}
    )

    return {"access_token": access_token, "token_type": "bearer"}



@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=schemas.Token)
def signup(
    full_name: str = Form(...),
    # username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    gender: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        form_data = schemas.SignupForm(
            full_name=full_name,
            # username=username,
            email=email,
            password=password,
            gender=gender,
            age=age
        )
    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ve.errors()
        )

    # Check if user exists by email or username
    if db.query(models.User).filter(models.User.email == form_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # if db.query(models.User).filter(models.User.username == form_data.username).first():
    #     raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = hash_password(form_data.password)

    new_user = models.User(
        full_name=form_data.full_name,
        # username=form_data.username,
        email=form_data.email,
        password=hashed_password,
        gender=form_data.gender,
        age=form_data.age
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user")

    # Add user as a new tenant to vector store
    vector_store.add_user(tenant_id=new_user.id)

    access_token = create_access_token(data={"user_id": new_user.id})
    return {"access_token": access_token, "token_type": "bearer"}
