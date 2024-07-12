from ctypes.wintypes import FLOAT
from sqlalchemy import Column, Integer, String, Date, ARRAY, FLOAT
from database import Base

class Tweets(Base):
    __tablename__ = 'tweets'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key= True, index = True)
    created_at = Column(Date, index = True)
    lang = Column(String, index = True)
    text = Column(String, index = True)
    full_text = Column(String, index = True)
    sentiment = Column(String, index = True)
    sentiment_val = Column(FLOAT, index = True)
    embedding_vector = Column(String, index = True)
