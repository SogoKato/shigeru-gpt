import glob
import json
from argparse import ArgumentParser

URL_LIST_PATH = "./url_list.json"


def main():
    parser = ArgumentParser()
    parser.add_argument("--glob", default="../data/raw/*.txt")
    args = parser.parse_args()
    url_list = load_url_list()
    files = glob.glob(args.glob)
    for file in files:
        filename = file.split("/")[-1].replace(".txt", "")
        for url in url_list:
            slug = url.split("/")[-2]
            if filename == slug:
                with open(file, "r") as f:
                    lines = f.readlines()
                    for i, l in enumerate(lines):
                        if l.startswith("投稿者:"):
                            lines.insert(i + 1, f"URL: {url}")
                            break
                with open(file, "w") as f:
                    f.writelines(lines)


def load_url_list() -> list[str]:
    with open(URL_LIST_PATH, "r") as f:
        ret = json.load(f)
    return ret


if __name__ == "__main__":
    main()
