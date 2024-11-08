import glob
import os
from argparse import ArgumentParser
from base64 import b64encode

import pandas as pd
from openai import OpenAI


def main():
    parser = ArgumentParser()
    parser.add_argument("--glob", default="../data/chunked/*.txt")
    parser.add_argument("--save-dir", default="../data/embed/")
    args = parser.parse_args()
    if not args.save_dir.endswith("/"):
        args.save_dir += "/"
    save_path = f"{args.save_dir}datav2.csv"
    if os.path.exists(save_path):
        df = extend_data(args.glob, save_path)
    else:
        yn = input("Do you want to create a new csv?")
        if yn != "yes":
            return
        df = init_data(args.glob, save_path)
    df.to_csv(save_path)


def extend_data(path: str, save_path: str) -> pd.DataFrame:
    files = glob.glob(path)
    df = pd.read_csv(save_path, index_col=0)
    i = len(df)
    for file in files:
        with open(file, "r") as f:
            lines = f.readlines()
        for line in lines:
            df.loc[i] = [line, get_embedding(line)]
            i += 1
    return df


def init_data(path: str, save_path: str) -> pd.DataFrame:
    files = glob.glob(path)
    data = "index,metadata,text\n"
    i = 0
    for file in files:
        with open(file, "r") as f:
            lines = f.readlines()
        metadata = ""
        for j, line in enumerate(lines):
            if j == 0:
                metadata = b64encode(line.strip().encode()).decode()
                continue
            data += f"{i},{metadata},{line}"
            i += 1
    with open(save_path, "w") as f:
        f.write(data)
    df = pd.read_csv(save_path, index_col=0)
    df["embedding"] = df.text.apply(lambda x: get_embedding(x))
    return df


def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    client = OpenAI()
    return client.embeddings.create(input=[text], model=model).data[0].embedding


if __name__ == "__main__":
    main()
