import json
import os
import time
from argparse import ArgumentParser
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, Tag
from jinja2 import Environment, FileSystemLoader

URL_LIST_PATH = "./url_list.json"


def main():
    parser = ArgumentParser()
    parser.add_argument("--save-dir", default="../data/raw/")
    parser.add_argument("--update-list", action="store_true")
    args = parser.parse_args()
    if args.update_list:
        url_list = update_url_list()
        print(f"{URL_LIST_PATH} is updated.")
    else:
        url_list = load_url_list()
        print(f"{URL_LIST_PATH} is loaded.")
    for url in url_list:
        if not args.save_dir.endswith("/"):
            args.save_dir += "/"
        if not url.endswith("/"):
            url += "/"
        slug = url.split("/")[-2]
        path = f"{args.save_dir}{slug}.txt"
        if exists_saved_article(path):
            print(f"{path} is found, skipping...")
            continue
        try:
            article = get_article(url)
            save_article(article=article, path=path)
            print(f"{path} has been saved.")
        except (requests.exceptions.TooManyRedirects, NotFoundError, HttpError) as e:
            print(f"ERROR while saving {url} to {path}, skipping...\n{e}")
            time.sleep(1)
            continue
        time.sleep(1)
    return


class NotFoundError(Exception):
    pass


class HttpError(Exception):
    pass


def load_url_list() -> list[str]:
    with open(URL_LIST_PATH, "r") as f:
        ret = json.load(f)
    return ret


def update_url_list() -> list[str]:
    list_page_url = "https://ariosoweb.com/articles/"
    pagination_index = 1
    ret: list[str] = []
    while True:
        if pagination_index == 1:
            found = find_links_from(url=list_page_url)
        else:
            try:
                found = find_links_from(url=f"{list_page_url}page/{pagination_index}/")
            except NotFoundError:
                break
        ret.extend(found)
        with open("./.url_list_tmp.json", "w") as f:
            json.dump(ret, f)
        pagination_index += 1
        time.sleep(1)
    with open(URL_LIST_PATH, "w") as f:
        json.dump(ret, f)
    os.remove("./.url_list_tmp.json")
    return ret


def find_links_from(url: str) -> list[str]:
    res = requests.get(url)
    if res.status_code == 404:
        raise NotFoundError()
    if not res.ok:
        raise HttpError()
    print(f"Got {url}")
    soup = BeautifulSoup(res.text, features="html.parser")
    # soup = BeautifulSoup(open("./sample.html"), features="html.parser")
    elems = soup.select("h2.entry-title a")
    ret: list[str] = []
    for elem in elems:
        ret.append(elem.attrs["href"])
    return ret


@dataclass
class Article:
    title: str
    author: str
    published_at: str
    content: str


@dataclass
class Page:
    title: str
    author: str
    published_at: str
    content: str


def exists_saved_article(path: str) -> bool:
    return os.path.exists(path)


def save_article(article: Article, path: str):
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("template.txt.j2")
    out = template.render(
        title=article.title,
        published_at=article.published_at,
        author=article.author,
        content=article.content,
    )
    with open(path, "w") as f:
        f.write(out)


def get_article(url: str) -> Article:
    content = ""
    pagination_index = 1
    while True:
        if pagination_index == 1:
            page = get_page(url=url)
        else:
            try:
                page = get_page(url=f"{url}{pagination_index}/")
            except NotFoundError:
                break
        content += page.content
        pagination_index += 1
        time.sleep(1)
    return Article(
        title=page.title,
        content=content,
        published_at=page.published_at,
        author=page.author,
    )


def get_page(url: str) -> Page:
    res = requests.get(url)
    if res.status_code == 404:
        raise NotFoundError()
    if not res.ok:
        raise HttpError()
    print(f"Got {url}")
    soup = BeautifulSoup(res.text, features="html.parser")
    title = soup.find_all("h1")[0].string
    published_at = soup.select('meta[property="article:published_time"]')[0].attrs[
        "content"
    ]
    author = soup.select("div.about-author a")[0].get_text()
    entry = soup.find_all("div", class_="entry-content")
    content = ""
    for child in entry[0]:
        if isinstance(child, Tag):
            if "class" in child.attrs.keys():
                class_ = child.attrs["class"]
                if "sns-share" in class_:
                    continue
                if "wpulike" in class_:
                    break
        content += child.get_text()
    return Page(title=title, content=content, published_at=published_at, author=author)


if __name__ == "__main__":
    main()
