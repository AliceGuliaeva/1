from bottle import (
    route, run, template, request, redirect
)

from scraputils import get_news
from db import News, session, make_table_news
from bayes import NaiveBayesClassifier
import string

@route("/")
@route("/news")
def news_list():
    s = session
    rows = s.query(News).filter(News.label == None).all()
    return template('news_template', rows=rows)


@route("/add_label/")
def add_label():

    id = request.query["id"]
    label = request.query["label"]
    item = session.query(News).get(id)
    item.label = label
    session.commit()
    redirect("/news")


@route("/update")
def update_news():

    news = get_news(url="https://news.ycombinator.com/newest")
    make_news = []
    for i in news:
        title, author = i["title"], i["author"]
        if not list(session.query(News).filter(News.title == title, News.author == author)):
            make_news.append(i)
        make_table_news(session, make_news)
    redirect("/news")

colors = {"good": "#00ff6a", "never": "#d10000", "maybe": "#ffb700"}
def clean(s: str) -> str:
    translator = str.maketrans("", "", string.punctuation)
    return s.translate(translator)

@route("/classify")
def classify_news():

    model = NaiveBayesClassifier()
    train_set = session.query(News).filter(News.label != None).all()
    model.fit(
        [clean(news.title).lower() for news in train_set],
        [news.label for news in train_set],
    )
    test = session.query(News).filter(News.label == None).all()
    cell = list(map(lambda x: model.predict(x.title), test))
    return template(
        "color_template",
        rows=list(map(lambda x: (x[1], colors[cell[x[0]]]), enumerate(test))),
    )

if __name__ == "__main__":
    run(host="localhost", port=8080)

