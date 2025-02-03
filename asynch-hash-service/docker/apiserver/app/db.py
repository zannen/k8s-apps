"""
Database functions
"""

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import String


class NotFound(Exception):
    """
    A NotFound class, so folks elsewhere don't have to import sqlalchemy.exc.
    """


class OpError(Exception):
    """
    A sqlalchemy OperationalError class, so folks elsewhere don't have to
    import sqlalchemy.exc.
    """


class Base(DeclarativeBase):
    """
    The declarative base, but named shorter.
    """


class Data(Base):
    """
    The one and only table, for storing and retrieving data.
    """

    __tablename__ = "data"

    id: Mapped[int] = mapped_column(primary_key=True)
    info: Mapped[str] = mapped_column(String(30))

    def __repr__(self) -> str:
        return f"Data(id={self.id!r}, info='{self.info!r}')"


def get_db(url: str):
    try:
        engine = sa.create_engine(url, echo=True)
        if url.startswith("mysql+mysqldb:"):
            with engine.connect() as conn:
                conn.execute(sa.text("CREATE DATABASE IF NOT EXISTS atestdb"))
                conn.commit()
            url += "/atestdb"
            engine = sa.create_engine(url, echo=True)

        with engine.connect() as conn:
            Base.metadata.create_all(conn)
            conn.commit()
    except sa.exc.OperationalError as exc:
        raise OpError() from exc
    return engine
