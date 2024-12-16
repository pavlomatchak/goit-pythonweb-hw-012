import contextlib

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
  AsyncEngine,
  async_sessionmaker,
  create_async_engine,
)

from conf.config import config

class DatabaseSessionManager:
  """
  Manages database sessions.
  """
  def __init__(self, url: str):
    self._engine: AsyncEngine | None = create_async_engine(url)
    self._session_maker: async_sessionmaker = async_sessionmaker(
      autoflush=False, autocommit=False, bind=self._engine
    )

  @contextlib.asynccontextmanager
  async def session(self):
    """
    Provides an asynchronous database session.

    Yields:
      An asynchronous database session.

    Raises:
      Exception: If the session maker is not initialized.
    """
    if self._session_maker is None:
      raise Exception("Database session is not initialized")
    session = self._session_maker()
    try:
      yield session
    except SQLAlchemyError as e:
      await session.rollback()
      raise  # Re-raise the original error
    finally:
      await session.close()

sessionmanager = DatabaseSessionManager(config.DB_URL)

async def get_db():
  """
  Provides an asynchronous database session.

  Yields:
    An asynchronous database session.
  """
  async with sessionmanager.session() as session:
    yield session
