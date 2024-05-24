import glob
from argparse import ArgumentParser

import pandas as pd
from openai import OpenAI


def main():
    parser = ArgumentParser()
    parser.add_argument("--glob", default="../data/chunked/*.txt")
    parser.add_argument("--save-dir", default="../data/embed/")
    args = parser.parse_args()
    if not args.save_dir.endswith("/"):
        args.save_dir += "/"
    data_path = txt_to_csv(args.glob, args.save_dir)
    df = pd.read_csv(data_path, index_col=0)
    df["embedding"] = df.text.apply(lambda x: get_embedding(x))
    df.to_csv(data_path)


def txt_to_csv(path: str, save_dir: str) -> str:
    files = glob.glob(path)
    data = "index,text\n"
    i = 0
    for file in files:
        with open(file, "r") as f:
            lines = f.readlines()
        for line in lines:
            data += f"{i},{line}"
            i += 1
    save_path = f"{save_dir}data.csv"
    with open(save_path, "w") as f:
        f.write(data)
    return save_path


def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    client = OpenAI()
    return client.embeddings.create(input=[text], model=model).data[0].embedding


if __name__ == "__main__":
    main()
