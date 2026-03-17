from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional,Literal


class Token(BaseModel):
    """Schema for the token response."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for the token data."""
    user_id: Optional[str] = None


class SignupForm(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    # username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    gender: Optional[Literal["male", "female"]] = None
    age: Optional[int] = None

    @field_validator("gender")
    def validate_gender(cls, v):
        return v.lower() if v else v
