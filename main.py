from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, select, Session
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from uuid import UUID
import json
from database import engine, get_session
from models import Message
from tools import tools, serpapi_search
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

CHAT_HISTORY_NUMBER_LIMIT = os.getenv("CHAT_HISTORY_NUMBER_LIMIT")


# ----------- Request Schema ----------- #
class ChatRequest(BaseModel):
    session_id: UUID
    system_prompt: str
    user_prompt: str
    model_name: str = "gpt-4o"
    api_key: str


# ----------- DB init ----------- #
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    print("Database connected and tables created.")


# @app.get("/search")
# def search(req: ChatRequest, db: Session = Depends(get_session)):
#     result = serpapi_search("ترند روز در ایران")
#     return result


@app.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_session)):
    history: List[Message] = db.exec(
        select(Message)
        .where(Message.session_id == req.session_id)
        .order_by(Message.created_at.desc())
        .limit(CHAT_HISTORY_NUMBER_LIMIT)
    ).all()

    messages = []

    messages.append({"role": "system", "content": req.system_prompt})
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": req.user_prompt})

    client = OpenAI(api_key=req.api_key)
    response = client.chat.completions.create(
        model=req.model_name,
        tools=tools,
        tool_choice="auto",
        messages=messages,
    )

    user_msg = Message(session_id=req.session_id, role="user", content=req.user_prompt)
    db.add(user_msg)

    final_reply = None
    if response.choices[0].message.tool_calls:
        messages.append(
            {
                "role": "assistant",
                "content": response.choices[0].message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in response.choices[0].message.tool_calls
                ],
            }
        )

        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "serpapi_search":
                arguments = json.loads(tool_call.function.arguments)
                tool_result = serpapi_search(**arguments)

                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(tool_result),
                        "tool_call_id": tool_call.id,
                    }
                )

        final_response = client.chat.completions.create(
            model=req.model_name,
            tools=tools,
            tool_choice="auto",
            messages=messages,
        )
        final_reply = final_response.choices[0].message.content
    else:
        final_reply = response.choices[0].message.content

    if final_reply:
        ai_msg = Message(
            session_id=req.session_id, role="assistant", content=final_reply
        )
        db.add(ai_msg)

    db.commit()

    return {"reply": final_reply}
