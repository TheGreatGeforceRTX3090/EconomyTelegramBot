from data.db_session import SqlAlchemyBase
from sqlalchemy import Integer, String, Column


class User(SqlAlchemyBase):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String)
    user_id = Column(Integer)
    balance = Column(Integer, default=0)
