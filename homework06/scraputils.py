import requests
from bs4 import BeautifulSoup


def extract_news(parser):
    """ Extract news from a given web page """
    news_list = []

    titles = parser.find_all("tr", class_="athing")
    subtext = parser.find_all("td", class_="subtext")

    for i in range(len(titles)):
        x = titles[i].find_all("td", class_="title")[1]
        title = x.a.text
        url = x.a["href"]
        c = subtext[i].find_all("a")[4]
        if c.text == "discuss":
            comments = 0
        else:
            comments = c.text
        author = subtext[i].find("a", class_="hnuser").get_text()
        point = subtext[i].find("span", class_="score").text
        points = point.split(' ')[0]

        news_list.append({"author": author, "comments": comments, "points": points, "title": title, "url": url})

    return news_list


def extract_next_page(parser):
    """ Extract next page URL """
    link = parser.find("a", class_="morelink")["href"]
    return str(link)


def get_news(url, n_pages=1):
    """ Collect news from a given web page """
    news = []
    while n_pages:
        print("Collecting data from page: {}".format(url))
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        news_list = extract_news(soup)
        next_page = extract_next_page(soup)
        url = "https://news.ycombinator.com/" + next_page
        news.extend(news_list)
        n_pages -= 1
    return news

if __name__ == "__main__":
    n = get_news(url="https://news.ycombinator.com/newest", n_pages=2)
    print(len(n))
    print(n[0])
    print(n[21])

