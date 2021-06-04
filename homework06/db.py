from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scraputils import get_news
import typing as tp

Base = declarative_base()
engine = create_engine("sqlite:///news.db")
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()


class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    url = Column(String)
    comments = Column(Integer)
    points = Column(Integer)
    label = Column(String)

def make_table_news(session, news: tp.List[tp.Dict[str, tp.Union[int, str]]]):
    for i in range(len(news)):
        values = News(
            title=news[i]["title"],
            author=news[i]["author"],
            url=news[i]["url"],
            points=news[i]["points"],
            comments=news[i]["comments"]
        )
        session.add(values)
    session.commit()

Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    make_table_news(
        session,
        get_news(url="https://news.ycombinator.com/newest", n_pages=25)
    )
