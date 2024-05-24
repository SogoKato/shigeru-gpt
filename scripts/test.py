import os
import sys
from argparse import ArgumentParser

import numpy as np
import pandas as pd
from openai import OpenAI


def main():
    parser = ArgumentParser()
    parser.add_argument("query", default="しげるって誰？")
    args = parser.parse_args()
    df = pd.read_csv("../data/embed/data.csv", index_col=0)
    df["embedding"] = df.embedding.apply(eval).apply(np.array)
    res = search(df, args.query, n=3)
    print([i for i in res.text])
    chat_res = chat(args.query, [i for i in res.text])


def chat(query: str, embed: list[str]):
    q = f"""{query}

Relevant info:
\"\"\"
{"\n\n".join(embed)}
\"\"\"
"""
    print(q)
    client = OpenAI()
    res = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": q},
        ],
        model="gpt-3.5-turbo",
        temperature=0,
    )
    print(res)
    return res.choices[0].message.content


def search(df, query, n=3):
    cache_path = "cache.csv"
    if not os.path.exists(cache_path):
        data = "index,text,embedding\n"
        with open(cache_path, "w") as f:
            f.write(data)
    cache_df = pd.read_csv(cache_path, index_col=0)
    cache_df["embedding"] = cache_df.embedding.apply(eval).apply(np.array)
    try:
        embedding = cache_df[cache_df["text"] == query].embedding.values[0]
        if len(embedding) != 1536:
            print("!! Wrong cached embedding length", len(embedding))
            raise ValueError()
        print("Using cache\nlen =", len(embedding))
        print(embedding)
    except Exception:
        embedding = get_embedding(query)
        save_cache(query, embedding)
    df["similarities"] = df.embedding.apply(lambda x: cosine_similarity(x, embedding))
    res = df.sort_values("similarities", ascending=False).head(n)
    return res


def save_cache(text: str, embedding: list[float]):
    cache_path = "cache.csv"
    cache_df = pd.read_csv(cache_path, index_col=0)
    cache_df.loc[len(cache_df)] = [text, embedding]
    cache_df.to_csv(cache_path)


def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    client = OpenAI()
    return client.embeddings.create(input=[text], model=model).data[0].embedding


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


if __name__ == "__main__":
    main()
