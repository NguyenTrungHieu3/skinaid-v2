# Chatbot module anatomy

Tai lieu nay mo ta kien truc chatbot sau khi refactor.

Muc tieu cua module: tao session chat, phan loai session, goi LLM dung context, va luu lich su hoi dap.

## 1. Cac file chinh

```text
backend/app/modules/chatbot/
  routes/chat_router.py              API endpoints
  services/chat_service.py           Service dieu phoi chinh
  services/chat_prompt_builder.py    Tao prompt cho LLM
  services/redis_session_store.py    Luu App Guide session/messages trong Redis
  services/wound_context_loader.py   Load Analysis + wound context
  services/rag_retriever.py          Goi RAG/Qdrant
  repository/chat_repository.py      DB access cho chat_sessions/chat_messages
```

## 2. Hai mode cua chatbot

### Wound Advisor

Dung khi user chat ve mot ket qua phan tich vet thuong.

Dieu kien:

- Tao session co `analysis_id`.
- Analysis ton tai.
- Analysis thuoc user hien tai.
- Analysis co `status = "completed"`.

Noi luu:

- Session: DB `chat_sessions`.
- Messages: DB `chat_messages`.

Co dung:

- `Analysis`.
- Detection co confidence cao nhat.
- `firstaid_snapshot`.
- RAG chunks tu Qdrant.
- LLM config key: `chatbot_advisor`.

### App Guide

Dung khi user hoi cach su dung app SkinAid.

Dieu kien:

- Tao session khong co `analysis_id`.

Noi luu:

- Session metadata: Redis.
- Messages: Redis.

Khong dung:

- Analysis.
- RAG.
- First-aid snapshot.

Co dung:

- LLM config key: `chatbot_guide`.

## 3. API flow

### Tao session

```text
POST /chatbot/sessions
    -> chat_router.create_session()
    -> ChatService.create_session()
```

Neu co `analysis_id`:

```text
ChatService
    -> WoundContextLoader.load_analysis()
    -> ChatRepository.create_session()
    -> return session_type = wound_advisor
```

Neu khong co `analysis_id`:

```text
ChatService
    -> ChatRedisSessionStore.create_session()
    -> return session_type = app_guide
```

### Gui tin nhan

```text
POST /chatbot/sessions/{session_id}/messages
    -> chat_router.send_message()
    -> ChatService.send_message()
```

`ChatService.send_message()` tim session theo thu tu:

```text
1. Tim DB session
   -> neu co: _reply_wound_advisor()

2. Tim Redis session
   -> neu co: _reply_app_guide()

3. Khong tim thay
   -> raise ChatSessionNotFoundError
```

## 4. Wound Advisor pipeline

Ham xu ly: `ChatService._reply_wound_advisor()`

```text
Kiem tra message_count
    -> ChatRepository.get_messages()
    -> WoundContextLoader.load_wound_context()
    -> ChatRagRetriever.query()
    -> ChatPromptBuilder.build_wound_advisor_prompt()
    -> ChatPromptBuilder.build_messages()
    -> resolve_llm_config("chatbot_advisor")
    -> LLMService.call()
    -> ChatRepository.save_message(user)
    -> ChatRepository.save_message(assistant)
    -> ChatRepository.increment_message_count()
    -> ChatMessageResponse
```

Y nghia tung buoc:

- `get_messages`: lay history de LLM hieu hoi dap truoc do.
- `load_wound_context`: lay `wound_type`, `severity`, `sub_type`, `firstaid_snapshot`.
- `rag.query`: lay them kien thuc bo sung lien quan.
- `build_wound_advisor_prompt`: tao system prompt gioi han scope chi ve vet thuong da phan tich.
- `resolve_llm_config`: lay model/temperature/max_tokens tu DB config.
- `LLMService.call`: goi LLM text mode.
- `save_message`: luu ca user message va assistant reply.
- `increment_message_count`: moi user message thanh cong tang 1.

## 5. App Guide pipeline

Ham xu ly: `ChatService._reply_app_guide()`

```text
Kiem tra message_count trong Redis metadata
    -> ChatRedisSessionStore.get_messages()
    -> ChatPromptBuilder.build_app_guide_prompt()
    -> ChatPromptBuilder.build_messages()
    -> resolve_llm_config("chatbot_guide")
    -> LLMService.call()
    -> ChatRedisSessionStore.save_message(user)
    -> ChatRedisSessionStore.save_message(assistant)
    -> ChatRedisSessionStore.increment_count()
    -> ChatMessageResponse
```

Mode nay chi tra loi ve cach su dung SkinAid, khong tu van y te cu the.

## 6. Trach nhiem tung component

| Component | Trach nhiem |
| --- | --- |
| `ChatService` | Dieu phoi flow, chon mode, goi cac component khac |
| `ChatRepository` | DB CRUD cho session/message |
| `ChatRedisSessionStore` | Redis CRUD cho App Guide |
| `WoundContextLoader` | Validate analysis va load wound context |
| `ChatRagRetriever` | Goi Qdrant hybrid search, fallback rong neu loi |
| `ChatPromptBuilder` | Tao prompt cho Wound Advisor/App Guide |
| `LLMService` | Goi OpenAI va record usage |

## 7. Diem can nho

- `create_session()` chi tao phong chat, chua goi LLM.
- `send_message()` moi la noi xu ly cau hoi.
- Router chi giu 2 endpoint can thiet: tao session va gui message.
- Wound Advisor dung DB + Analysis + RAG.
- App Guide dung Redis, khong dung RAG.
- Chatbot goi LLM o text mode, khong ep JSON.
- RAG loi thi Wound Advisor van tiep tuc voi context san co.
