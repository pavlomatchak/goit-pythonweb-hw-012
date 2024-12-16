from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from schemas import UserCreate, Token, User, RequestEmail, PasswordResetRequest, PasswordReset
from services.auth import create_access_token, Hash, get_email_from_token, create_password_reset_token, verify_password_reset_token
from services.users import UserService
from database.db import get_db
from services.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
  user_data: UserCreate,
  background_tasks: BackgroundTasks,
  request: Request,
  db: Session = Depends(get_db),
):
  """
  Registers a new user.

  Args:
    user_data: User data for registration.
    background_tasks: Background task queue.
    request: HTTP request.
    db: Database session.

  Returns:
    The newly created user.

  Raises:
    HTTPException: If a user with the same email or username already exists.
  """
  user_service = UserService(db)

  email_user = await user_service.get_user_by_email(user_data.email)
  if email_user:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="Користувач з таким email вже існує",
    )

  username_user = await user_service.get_user_by_username(user_data.username)
  if username_user:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="Користувач з таким іменем вже існує",
    )
  user_data.password = Hash().get_password_hash(user_data.password)
  new_user = await user_service.create_user(user_data)
  background_tasks.add_task(
    send_email, new_user.email, new_user.username, request.base_url
  )
  return new_user

@router.post("/login", response_model=Token)
async def login_user(
  form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
  """
  Authenticates user, verifies password, and returns access token.

  Args:
    form_data: Form data containing username and password.
    db: Database session.

  Returns:
    Access token.

  Raises:
    HTTPException: On authentication failure.
  """
  user_service = UserService(db)
  user = await user_service.get_user_by_username(form_data.username)
  if not user or not Hash().verify_password(form_data.password, user.hashed_password):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Неправильний логін або пароль",
      headers={"WWW-Authenticate": "Bearer"},
    )
  if not user.confirmed:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Електронна адреса не підтверджена",
    )
  access_token = await create_access_token(data={"sub": user.username})
  return {"access_token": access_token, "token_type": "bearer"}

@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
  """
  Confirms a user's email address.

  Args:
    token: The email confirmation token.
    db: The database session.

  Returns:
    A message indicating the confirmation status.

  Raises:
    HTTPException: If the token is invalid or the user is not found.
  """
  email = await get_email_from_token(token)
  user_service = UserService(db)
  user = await user_service.get_user_by_email(email)
  if user is None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
    )
  if user.confirmed:
    return {"message": "Ваша електронна пошта вже підтверджена"}
  await user_service.confirmed_email(email)
  return {"message": "Електронну пошту підтверджено"}

@router.post("/request_email")
async def request_email(
  body: RequestEmail,
  background_tasks: BackgroundTasks,
  request: Request,
  db: Session = Depends(get_db),
):
  """
  Requests email confirmation for a user.

  Args:
    body: RequestEmail object containing the user's email.
    background_tasks: Background task queue for sending the email.
    request: HTTP request object.
    db: Database session for user operations.

  Returns:
    A dictionary containing a message about the request status.
  """
  user_service = UserService(db)
  user = await user_service.get_user_by_email(body.email)

  if user.confirmed:
      return {"message": "Ваша електронна пошта вже підтверджена"}
  if user:
      background_tasks.add_task(
          send_email, user.email, user.username, request.base_url
      )
  return {"message": "Перевірте свою електронну пошту для підтвердження"}

@router.post("/password-reset-request")
async def request_password_reset(
  request: PasswordResetRequest,
  background_tasks: BackgroundTasks,
  db: Session = Depends(get_db),
):
  """
  Initiates a password reset.

  Args:
    request: The FastAPI request object containing details about the incoming request.
    background_tasks: A FastAPI background tasks object for sending the email asynchronously.
    db: A database session dependency injected via Depends(get_db).

  Raises:

    HTTPException: If the user is not found in the database.

  Returns:
    Message
  """
  user_service = UserService(db)
  user = await user_service.get_user_by_email(request.email)
  
  if not user:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувач не знайдений.")

  token = create_password_reset_token({"sub": user.email})

  reset_link = f"{request.base_url}password-reset/{token}"
  background_tasks.add_task(send_email, user.email, "Оновити пароль", reset_link)
  
  return {"message": "Лист для оновлення паролю був відправлений."}

@router.post("/password-reset/{token}")
async def reset_password(
  token: str,
  body: PasswordReset,
  db: Session = Depends(get_db),
):
  """
  Resets a user's password based on a valid reset token.

  Args:
    token: The password reset token string received from the request URL.
    body: A PasswordReset schema object containing the new password.
    db: A database session dependency injected via Depends(get_db).

  Raises:
    HTTPException: If the token is invalid or the user is not found in the database.

  Returns:
    Message
  """
  payload = verify_password_reset_token(token)
  
  email = payload["sub"]
  
  user_service = UserService(db)
  user = await user_service.get_user_by_email(email)
  
  if not user:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувач не знайдений.")

  hashed_password = Hash().get_password_hash(body.new_password)

  user.password = hashed_password
  await user_service.update_user(user)
  
  return {"message": "Пароль успішно оновлено."}
