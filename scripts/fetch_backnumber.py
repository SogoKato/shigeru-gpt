import requests
from bs4 import BeautifulSoup, Tag

template = """アリオーゾ冊子のバックナンバー・過去号一覧: {back_numbers}"""


def main():
    url = "https://ariosoweb.com/backnumbers/"
    res = requests.get(url)
    if not res.ok:
        raise ValueError(res.status_code)
    print(f"Got {url}")
    soup = BeautifulSoup(res.text, features="html.parser")
    path = "../data/raw/backnumbers.txt"
    entry = soup.find_all("div", class_="entry-content")
    tmp = "\n".join([e.get_text() for e in entry])
    back_numbers = ""
    for l in tmp.split("\n"):
        if not l.strip() or "coming soon" in l:
            continue
        back_numbers += l + " "
    out = template.format(back_numbers=back_numbers)
    with open(path, "w") as f:
        f.write(out)


if __name__ == "__main__":
    main()
