# Chat Socket.IO Migration Guide (Flutter + Web)

Socket.IO is the primary chat transport. REST is **only** for multipart file attachments.

**Socket URL:** same host as the API, path `/socket.io/`  
**Auth:** `auth: { token: "<JWT access>" }` (or `?token=` query)

Personal channel: `user_{userId}` (joined automatically on connect)  
Room channel: `chat_room_{roomId}` (joined via `join_room`)

---

## Connect / disconnect

| Server → client | Payload |
|---|---|
| `connected` | `{ user_id, online_user_ids }` |
| `user_presence` | `{ user_id, is_online, user_name }` (to contacts' personal rooms) |

---

## Client → server (with ACK)

Return shape always includes `status_code`. Flutter uses `emitWithAck`.

| Event | Body | ACK |
|---|---|---|
| `chat_sync` | `{ page?, page_size? }` | `{ status_code: 200, unread, inbox, online_user_ids }` |
| `get_unread` | `{}` | unread summary + `status_code` |
| `get_inbox` | `{ page?, page_size? }` | paginated rooms + `status_code` |
| `get_room` | `{ room_id }` | `{ status_code, room }` |
| `get_or_create_room` | `{ billboard_id }` | `{ status_code: 200\|201, room }` (advertiser only) |
| `get_messages` | `{ room_id, page?, page_size? }` | paginated messages (page 1 = newest; `results` oldest→newest) |
| `get_presence` | `{}` | `{ status_code, online_user_ids }` |
| `send_message` | `{ room_id, body }` | `{ status_code: 201, message }` |

Errors: `{ status_code: 4xx\|5xx, message }`

---

## Client → server (no ACK required)

| Event | Body |
|---|---|
| `join_room` | `{ room_id }` → server emits `room_joined` `{ room_id, other_user_online }` |
| `leave_room` | `{ room_id }` → `room_left` |
| `typing_start` / `typing_stop` | `{ room_id }` → others get `user_typing` |
| `message_delivered` | `{ room_id, message_id }` |
| `messages_seen` | `{ room_id, message_id }` → room gets `messages_seen`; marker gets `unread_updated` |

---

## Server pushes

| Event | When |
|---|---|
| `message_sent` | To sender after successful `send_message` |
| `new_message` | To room channel (text + attachments) |
| `inbox_updated` | To recipient personal room |
| `unread_updated` | To recipient (new msg) or to reader (`messages_seen`) |
| `message_delivered` / `messages_seen` | Room channel receipts |
| `user_typing` | Room channel |
| `error` | `{ message, status_code }` |

---

## REST (attachments only)

```
POST /api/chat/rooms/{room_id}/messages/
Authorization: Bearer <token>
Content-Type: multipart/form-data

body? (optional text)
attachment_0, attachment_1, ...  (at least one file required)
```

Text-only without files → **400** (use socket `send_message`).  
On success the server still emits `new_message` (+ inbox/unread to the other user).

---

## Flutter mapping

Matches `ChatSocketService` / `ChatRepoImpl`:

- Inbox, unread, rooms, messages, presence → socket ACK events  
- Text send → `send_message`  
- Files → REST multipart only  
