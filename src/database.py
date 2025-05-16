from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=4,
    max_overflow=4,
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

async def delete_tables():
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)

async def get_async_session():
    async with async_session_maker() as session:
        yield session


class BaseModel(DeclarativeBase):
    pass


class QuoteOrm(BaseModel):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str]
