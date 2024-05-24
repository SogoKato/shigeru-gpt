from logging import getLogger
from typing import Optional

import numpy as np
import pandas as pd
from config import config
from fastapi import FastAPI, Header, HTTPException, Request, status
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from openai import OpenAI

app = FastAPI()
logger = getLogger(__name__)

configuration = Configuration(
    access_token=config.line_channel_access_token.get_secret_value()
)
handler = WebhookHandler(config.line_channel_secret.get_secret_value())


@app.get("/readyz")
def read_root():
    return {"status": "ok"}


@app.post("/callback")
async def callback(
    req: Request, x_line_signature: Optional[str] = Header(default=None)
):
    x_line_signature = req.headers["X-Line-Signature"]
    body = await req.body()
    try:
        handler.handle(body.decode(), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    logger.info(event.json())
    ans = answer_with_embedding_based_search(event.message.text)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=ans)],
            )
        )


query_template = """{query}

Relevant info:
\"\"\"
{info}
\"\"\"
"""


def answer_with_embedding_based_search(query: str) -> str:
    client = OpenAI()
    df = read_data()
    search_result = embeddings_search(df=df, query=query)
    info = "\n\n".join(search_result)
    q = query_template.format(query=query, info=info)
    logger.info(q)
    res = client.chat.completions.create(
        messages=[
            {"role": "system", "content": config.system_prompt},
            {"role": "user", "content": q},
        ],
        model=config.openai_model,
        temperature=config.openai_temp,
    )
    logger.info(res)
    return res.choices[0].message.content


def read_data() -> pd.DataFrame:
    df = pd.read_csv(config.data_path, index_col=0)
    df["embedding"] = df.embedding.apply(eval).apply(np.array)
    logger.info(df)
    return df


def embeddings_search(df: pd.DataFrame, query: str, n: int = 3) -> list[str]:
    embedding = get_embedding(query)
    df["similarities"] = df.embedding.apply(lambda x: cosine_similarity(x, embedding))
    res = df.sort_values("similarities", ascending=False).head(n)
    return [i for i in res.text]


def get_embedding(text: str, model: str = "text-embedding-3-small"):
    text = text.replace("\n", " ")
    client = OpenAI()
    return client.embeddings.create(input=[text], model=model).data[0].embedding


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
