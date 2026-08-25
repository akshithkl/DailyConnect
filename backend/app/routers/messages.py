from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import decode_access_token
from app.deps import current_user
from app.models import Conversation, ConversationMember, Message, User
from app.schemas import ConversationCreate, MessageCreate, MessageOut
from app.services.storage import public_url

router = APIRouter(prefix="/api/conversations", tags=["messages"])


class ConnectionManager:
    def __init__(self): self.connections: dict[int, set[WebSocket]] = defaultdict(set)
    async def connect(self, conversation_id: int, websocket: WebSocket): await websocket.accept(); self.connections[conversation_id].add(websocket)
    def disconnect(self, conversation_id: int, websocket: WebSocket): self.connections[conversation_id].discard(websocket)
    async def broadcast(self, conversation_id: int, event: dict[str, Any]):
        for socket in list(self.connections[conversation_id]): await socket.send_json(event)

manager = ConnectionManager()


def is_member(db: Session, conversation_id: int, user_id: int) -> bool:
    return db.scalar(select(ConversationMember.id).where(and_(ConversationMember.conversation_id == conversation_id, ConversationMember.user_id == user_id))) is not None


def message_out(message: Message) -> MessageOut:
    return MessageOut(id=message.id, sender_id=message.sender_id, text=message.text, image_url=public_url(message.image_key), created_at=message.created_at)


@router.get("", response_model=list[dict])
def conversations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Conversation).join(ConversationMember).where(ConversationMember.user_id == user.id).order_by(Conversation.created_at.desc())).all()
    return [{"id": row.id, "members": [{"id": member.user.id, "username": member.user.username, "profile_photo": public_url(member.user.profile.profile_photo if member.user.profile else None)} for member in row.members]} for row in rows]


@router.post("", response_model=dict, status_code=201)
def create_conversation(payload: ConversationCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if payload.user_id == user.id or not db.get(User, payload.user_id): raise HTTPException(status_code=400, detail="Choose another valid user")
    existing = db.scalar(select(Conversation).join(ConversationMember).where(ConversationMember.user_id == user.id).having(Conversation.id.in_(select(ConversationMember.conversation_id).where(ConversationMember.user_id == payload.user_id))))
    if existing: return {"id": existing.id}
    conversation = Conversation(members=[ConversationMember(user_id=user.id), ConversationMember(user_id=payload.user_id)])
    db.add(conversation); db.commit(); db.refresh(conversation); return {"id": conversation.id}


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(conversation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not is_member(db, conversation_id, user.id): raise HTTPException(status_code=403, detail="Conversation access denied")
    return [message_out(item) for item in db.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)).all()]


@router.websocket("/ws/chat/{conversation_id}")
async def chat(websocket: WebSocket, conversation_id: int):
    token = websocket.query_params.get("token")
    subject = decode_access_token(token or "")
    db = SessionLocal()
    try:
        user_id = int(subject) if subject and subject.isdigit() else 0
        if not is_member(db, conversation_id, user_id): await websocket.close(code=1008); return
        await manager.connect(conversation_id, websocket)
        while True:
            payload = MessageCreate.model_validate(await websocket.receive_json())
            if not payload.text.strip(): continue
            message = Message(conversation_id=conversation_id, sender_id=user_id, text=payload.text.strip())
            db.add(message); db.commit(); db.refresh(message)
            await manager.broadcast(conversation_id, message_out(message).model_dump(mode="json"))
    except WebSocketDisconnect: manager.disconnect(conversation_id, websocket)
    finally: db.close()
