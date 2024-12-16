from fastapi import APIRouter, Depends, Request, File, UploadFile, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from schemas import User
from services.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import User as DBUser
from database.db import get_db
import cloudinary.uploader

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)

@router.get(
  "/me", response_model=User, description="No more than 10 requests per minute"
)
@limiter.limit("10/minute")
async def me(request: Request, user: DBUser = Depends(get_current_user)):
  return user

@router.put("/avatar", description="Update user avatar")
async def update_avatar(
  file: UploadFile = File(...),
  current_user: User = Depends(get_current_user),
  db: AsyncSession = Depends(get_db)
):
  if file.content_type not in ["image/jpeg", "image/png"]:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Invalid file type. Only JPEG or PNG images are allowed."
    )

  if current_user.role == "admin":
    try:
      upload_result = cloudinary.uploader.upload(file.file, folder="avatars")

      stmt = select(User).where(User.id == current_user.id)
      result = await db.execute(stmt)
      user = result.scalar_one_or_none()

      if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

      user.avatar = upload_result["secure_url"]
      await db.commit()
      await db.refresh(user)

      return {"avatar_url": user.avatar}

    except Exception as e:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"An error occurred while uploading the avatar: {str(e)}"
      )

  else:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Only administrators can change the default avatar."
    )
