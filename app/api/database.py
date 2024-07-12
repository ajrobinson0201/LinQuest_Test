from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base 
from datetime import datetime

URL_DATABASE = 'postgresql://aaronrobinson:test@localhost:5432/tweets_db'

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

Base = declarative_base()

class Tweet(Base):
    __tablename__ = 'tweets'

    id = Column(Integer, primary_key=True, index = True)
    created_at = Column(DateTime)
    lang = Column(String)
    text = Column(String)
    full_text = Column(String)


