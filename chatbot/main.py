import hashlib
import os
from logging import INFO, StreamHandler, getLogger
from typing import Optional, TypedDict

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
    ShowLoadingAnimationRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from openai import OpenAI

app = FastAPI()
logger = getLogger(__name__)
std_handler = StreamHandler()
std_handler.setLevel(INFO)
logger.addHandler(std_handler)
logger.setLevel(INFO)

configuration = Configuration(
    access_token=config.line_channel_access_token.get_secret_value()
)
handler = WebhookHandler(config.line_channel_secret.get_secret_value())


@app.get("/readyz")
def read_root():
    data_sha256 = ""
    if os.path.exists(config.data_path):
        with open(config.data_path, "rb") as f:
            d = hashlib.file_digest(f, "sha256")
        data_sha256 = d.hexdigest()
    if not data_sha256:
        logger.warning(f"{config.data_path} does not exist!")
    return {"data": f"sha256:{data_sha256}"}


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
    logger.info(event.json(ensure_ascii=False))
    if event.source.type == "user":
        conversation_id = event.source.user_id
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.show_loading_animation_with_http_info(
                ShowLoadingAnimationRequest(
                    chatId=conversation_id,
                    loadingSeconds=60,
                )
            )
    else:
        conversation_id = event.source.group_id
        if event.message.text.strip()[-1] not in ["?", "？", "❓", "❔"]:
            logger.info("Ignoring message as it is not a question.")
            return
    ans = answer_with_embedding_based_search(event.message.text, conversation_id)
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


def answer_with_embedding_based_search(query: str, conversation_id: str) -> str:
    client = OpenAI()
    df = read_data()
    search_result = embeddings_search(df=df, query=query)
    info = "\n\n".join(search_result)
    q = query_template.format(query=query, info=info)
    logger.info(q)
    messages = init_messages(conversation_id=conversation_id)
    messages.append({"role": "user", "content": q})
    logger.info(messages)
    res = client.chat.completions.create(
        messages=messages,
        model=config.openai_model,
        temperature=config.openai_temp,
    )
    logger.info(res)
    save_message(
        conversation_id=conversation_id, message={"role": "user", "content": query}
    )
    ret = res.choices[0].message.content
    save_message(
        conversation_id=conversation_id, message={"role": "assistant", "content": ret}
    )
    return res.choices[0].message.content


class Message(TypedDict):
    role: str
    content: str


history: dict[str, list[Message]] = {}


def init_messages(conversation_id: str) -> list[Message]:
    ret: list[Message] = [
        {"role": "system", "content": config.system_prompt},
    ]
    if conversation_id not in history.keys():
        return ret
    ret.extend(history[conversation_id])
    return ret


def save_message(conversation_id: str, message: Message):
    hist = history.get(conversation_id, [])
    if len(hist) >= config.max_history_per_conversation:
        start = len(hist) - config.max_history_per_conversation + 1
        history[conversation_id] = history[conversation_id][start:]
    if len(hist) == 0:
        history[conversation_id] = []
    history[conversation_id].append(message)


def read_data() -> pd.DataFrame:
    df = pd.read_csv(config.data_path, index_col=0)
    df["embedding"] = df.embedding.apply(eval).apply(np.array)
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
