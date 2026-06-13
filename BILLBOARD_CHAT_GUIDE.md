# Billboard Chat API & Socket.IO Guide

OLX-style chat between **advertiser** and **media owner** per billboard.  
Advertiser taps **Message** on billboard detail → chat room is created (or reopened).  
Real-time updates via **Socket.IO** (typing, delivered, seen).

**Base URL:** `http://16.16.160.64:8000`  
**Socket.IO URL:** `http://16.16.160.64:8000` (same host, path `/socket.io/`)

**Server:** Daphne ASGI (`reachtolet-daphne.service`) — required for WebSockets.

---

## Task summary

| Feature | Implementation |
|---|---|
| Chat room per billboard + advertiser | `ChatRoom` unique on `(billboard, advertiser)` |
| Advertiser starts chat | `GET /api/chat/rooms/by-billboard/{id}/` |
| Text messages | REST POST + Socket `new_message` broadcast |
| Document/image attachments | REST multipart (`attachment_0`, …) max 15 MB |
| Typing indicator | Socket `typing_start` / `typing_stop` → `user_typing` |
| Sent | Message `status: "sent"` on create |
| Delivered | Socket `message_delivered` or REST mark delivered |
| Seen / read | Socket `messages_seen` or REST `POST .../read/` |
| Auth | JWT Bearer (REST) + JWT in Socket `auth.token` |

---

## Database tables

| Table | Purpose |
|---|---|
| `chat_chatroom` | One thread per `(billboard, advertiser)`; stores media owner |
| `chat_chatmessage` | Messages: body, type, status (`sent`/`delivered`/`seen`) |
| `chat_chatattachment` | Files linked to a message |
| `chat_chatroomparticipant` | Per-user read cursor (`last_read_message`) |

**Relations:**
```
Billboard ──< ChatRoom >── User (advertiser)
                └── User (media_owner)
                └──< ChatMessage ──< ChatAttachment
```

---

## User flow (Flutter)

```
Billboard detail → [Message] button (advertiser only)
    → GET /api/chat/rooms/by-billboard/{billboard_id}/
    → Open chat screen, connect Socket.IO, emit join_room
    → Load history: GET /api/chat/rooms/{room_id}/messages/
    → Send text/files: POST /api/chat/rooms/{room_id}/messages/
    → On receive new_message: emit message_delivered
    → On screen visible: POST /api/chat/rooms/{room_id}/read/
```

Media owner sees the room in `GET /api/chat/rooms/` after advertiser sends first message (room exists from first tap).

---

## REST API reference

All endpoints require:

```
Authorization: Bearer {access_token}
```

---

### 1. Start / get room from billboard (Message button)

**Advertiser only** — get-or-create room.

```bash
curl --location "$BASE_URL/api/chat/rooms/by-billboard/40/" \
  --header "Authorization: Bearer $ADVERTISER_TOKEN"
```

**201 — room created:**

```json
{
  "status_code": 201,
  "message": "Chat room created",
  "room": {
    "id": 1,
    "billboard_id": 40,
    "billboard": {
      "id": 40,
      "city": "Lahore",
      "road_name": "Jail Road",
      "ooh_media_type": "Digital Billboard",
      "image": "http://16.16.160.64:8000/media/billboards/photo.jpg"
    },
    "advertiser_id": 17,
    "media_owner_id": 21,
    "other_user": {
      "id": 21,
      "email": "mediaowner@gmail.com",
      "full_name": "media owner",
      "user_type": "media_owner"
    },
    "last_message": null,
    "unread_count": 0,
    "created_at": "2026-06-13T11:28:39.578231+00:00",
    "updated_at": "2026-06-13T11:28:39.578256+00:00"
  }
}
```

**200 — room already exists:** same shape, `"message": "Chat room retrieved"`.

---

### 2. List my chat rooms

```bash
curl --location "$BASE_URL/api/chat/rooms/?page_size=20" \
  --header "Authorization: Bearer $TOKEN"
```

**200:**

```json
{
  "links": { "next": null, "previous": null },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 1,
      "billboard_id": 40,
      "billboard": { "id": 40, "city": "TestCity", "ooh_media_type": "Digital Billboard", "image": null },
      "other_user": { "id": 17, "email": "admin@gmail.com", "full_name": "admin", "user_type": "advertiser" },
      "last_message": {
        "id": 1,
        "body": "Hello, is this billboard available next week?",
        "status": "sent",
        "message_type": "text",
        "attachments": [],
        "created_at": "2026-06-13T11:28:46.957507+00:00"
      },
      "unread_count": 1,
      "updated_at": "2026-06-13T11:28:46.957507+00:00"
    }
  ]
}
```

---

### 3. Room detail

```bash
curl --location "$BASE_URL/api/chat/rooms/1/" \
  --header "Authorization: Bearer $TOKEN"
```

**200:** Single `room` object (same shape as inside create response).

---

### 4. Create room (alternative POST)

```bash
curl --location "$BASE_URL/api/chat/rooms/" \
  --header "Authorization: Bearer $ADVERTISER_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"billboard_id": 40}'
```

Same response as by-billboard endpoint.

---

### 5. List messages (paginated)

```bash
curl --location "$BASE_URL/api/chat/rooms/1/messages/?page_size=50" \
  --header "Authorization: Bearer $TOKEN"
```

**200:**

```json
{
  "links": { "next": null, "previous": null },
  "count": 1,
  "total_pages": 1,
  "current_page": 1,
  "results": [
    {
      "id": 1,
      "room_id": 1,
      "sender_id": 17,
      "sender_email": "admin@gmail.com",
      "sender_name": "admin",
      "body": "Hello, is this billboard available next week?",
      "message_type": "text",
      "status": "sent",
      "attachments": [],
      "created_at": "2026-06-13T11:28:46.957507+00:00"
    }
  ]
}
```

---

### 6. Send message (text + attachments)

**Content-Type:** `multipart/form-data`

```bash
curl --location "$BASE_URL/api/chat/rooms/1/messages/" \
  --header "Authorization: Bearer $TOKEN" \
  --form 'body=Please find the brief attached.' \
  --form 'attachment_0=@"/path/to/brief.pdf"'
```

**201:**

```json
{
  "status_code": 201,
  "message": "Message sent",
  "message_data": {
    "id": 2,
    "room_id": 1,
    "sender_id": 17,
    "sender_email": "admin@gmail.com",
    "sender_name": "admin",
    "body": "Please find the brief attached.",
    "message_type": "mixed",
    "status": "sent",
    "attachments": [
      {
        "id": 1,
        "original_name": "brief.pdf",
        "content_type": "application/pdf",
        "file_size": 245760,
        "url": "http://16.16.160.64:8000/media/chat_attachments/2026/06/abc.pdf"
      }
    ],
    "created_at": "2026-06-13T11:35:00.000000+00:00"
  }
}
```

**Allowed attachment types:** PDF, DOC/DOCX, XLS/XLSX, JPEG, PNG, GIF, WEBP, TXT  
**Max size:** 15 MB per file

Also broadcasts Socket event `new_message` to room subscribers.

---

### 7. Mark messages as read (seen)

```bash
curl --location "$BASE_URL/api/chat/rooms/1/read/" \
  --header "Authorization: Bearer $TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"message_id": 2}'
```

**200:**

```json
{
  "status_code": 200,
  "message": "Messages marked as read",
  "message_id": 2,
  "status": "seen"
}
```

Also emits Socket `messages_seen` to the room.

---

### 8. Mark single message delivered (REST fallback)

```bash
curl --location -X POST "$BASE_URL/api/chat/rooms/1/messages/2/delivered/" \
  --header "Authorization: Bearer $TOKEN"
```

**200:**

```json
{
  "status_code": 200,
  "message_id": 2,
  "status": "delivered"
}
```

---

## Socket.IO reference

### Connect (Flutter / JS)

```javascript
import { io } from 'socket.io-client';

const socket = io('http://16.16.160.64:8000', {
  transports: ['websocket', 'polling'],
  auth: {
    token: accessToken,  // JWT access token (with or without "Bearer " prefix)
  },
});
```

Alternative: query string `?token=YOUR_JWT`

---

### Client → Server events (emit)

| Event | Payload | Description |
|---|---|---|
| `join_room` | `{ "room_id": 1 }` | Subscribe to room channel (call when opening chat) |
| `leave_room` | `{ "room_id": 1 }` | Unsubscribe |
| `typing_start` | `{ "room_id": 1 }` | User started typing |
| `typing_stop` | `{ "room_id": 1 }` | User stopped typing |
| `send_message` | `{ "room_id": 1, "body": "Hi" }` | Text-only send (prefer REST for attachments) |
| `message_delivered` | `{ "room_id": 1, "message_id": 2 }` | Recipient received message |
| `messages_seen` | `{ "room_id": 1, "message_id": 2 }` | Recipient read up to this message |

---

### Server → Client events (listen)

| Event | Payload | When |
|---|---|---|
| `connected` | `{ "user_id": 17 }` | Successful connection |
| `room_joined` | `{ "room_id": 1 }` | After `join_room` |
| `room_left` | `{ "room_id": 1 }` | After `leave_room` |
| `new_message` | `{ message object }` | New message in room (same shape as REST) |
| `user_typing` | `{ "room_id": 1, "user_id": 21, "user_name": "...", "is_typing": true }` | Typing indicator |
| `message_delivered` | `{ "room_id": 1, "message_id": 2, "user_id": 21, "status": "delivered" }` | Delivery receipt |
| `messages_seen` | `{ "room_id": 1, "message_id": 2, "user_id": 21, "status": "seen" }` | Read receipt |
| `error` | `{ "message": "...", "status_code": 403 }` | Auth / validation error |

---

### Message status flow

```
sent  →  delivered  →  seen
 ↑         ↑              ↑
create   recipient      recipient
         got message    opened chat /
         (socket/REST)  POST read
```

---

### Flutter Socket example

```dart
socket.onConnect((_) {
  socket.emit('join_room', {'room_id': roomId});
});

socket.on('new_message', (data) {
  addMessageToUi(data);
  socket.emit('message_delivered', {
    'room_id': roomId,
    'message_id': data['id'],
  });
});

socket.on('user_typing', (data) {
  showTypingIndicator(data['user_id'], data['is_typing'] == true);
});

socket.on('messages_seen', (data) {
  updateMessageStatus(data['message_id'], 'seen');
});

// Typing
textController.addListener(() {
  socket.emit('typing_start', {'room_id': roomId});
  debouncer.run(() => socket.emit('typing_stop', {'room_id': roomId}));
});
```

---

## HTTP status codes

| Code | Endpoint | Cause |
|---|---|---|
| **200** | GET list/detail, POST read, existing room | Success |
| **201** | POST room, POST message, new room | Created |
| **400** | POST message | Empty body and no attachments |
| **400** | POST message | Invalid attachment type / too large |
| **401** | All | Missing or invalid JWT |
| **403** | POST room | Advertiser-only (media owner cannot start from billboard button) |
| **403** | Any room action | Not a participant in the room |
| **403** | POST room | Media owner trying to chat on own billboard |
| **404** | Room / message | Not found |
| **415** | POST message with JSON only | Use multipart for attachments |

Socket connection rejected (`connect` returns false) → invalid/expired JWT.

---

## Before vs after

| Before | After |
|---|---|
| No chat | Full REST + Socket.IO chat per billboard |
| No real-time | Typing, delivered, seen over sockets |
| — | Attachments (PDF, images, docs) |
| Gunicorn (HTTP only) | Daphne ASGI (HTTP + WebSocket) |

---

## Deployment

```bash
cd /home/ubuntu/Reachtolet_backend
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
sudo systemctl restart reachtolet-daphne
```

**Service commands:**

```bash
sudo systemctl start reachtolet-daphne
sudo systemctl stop reachtolet-daphne
sudo systemctl restart reachtolet-daphne
sudo journalctl -u reachtolet-daphne -f   # logs
```

Verify:

```bash
curl http://16.16.160.64:8000/api/users/health/
```

---

## Postman collection tips

| Request | Method | URL | Body |
|---|---|---|---|
| Start chat | GET | `/api/chat/rooms/by-billboard/40/` | — |
| List rooms | GET | `/api/chat/rooms/` | — |
| Messages | GET | `/api/chat/rooms/1/messages/` | — |
| Send text | POST | `/api/chat/rooms/1/messages/` | form: `body` |
| Send file | POST | `/api/chat/rooms/1/messages/` | form: `body` + `attachment_0` file |
| Mark read | POST | `/api/chat/rooms/1/read/` | JSON: `{ "message_id": 2 }` |

---

## Files added

| File | Purpose |
|---|---|
| `chat/models.py` | Room, Message, Attachment, Participant |
| `chat/services.py` | Business logic |
| `chat/views.py` | REST endpoints |
| `chat/socket_handlers.py` | Socket.IO events |
| `chat/auth.py` | JWT for sockets |
| `core/asgi.py` | Daphne + Socket.IO mount |
| `deploy/reachtolet-daphne.service` | systemd unit |

---

## Related guides

- `BILLBOARD_SPECIFICATIONS_GUIDE.md` — type-specific billboard data
- `BILLBOARD_PREVIEW_API_GUIDE.md` — map pin preview before detail/chat
