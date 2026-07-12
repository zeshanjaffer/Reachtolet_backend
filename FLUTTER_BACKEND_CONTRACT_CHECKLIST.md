# Reachtolet Backend — Flutter Contract Checklist

Use this document on the Flutter side to confirm every backend feature is present and field shapes match the app.

**Base URL (current app):** `http://16.16.160.64:8000`  
**Socket path:** `/socket.io/`  
**Socket auth:** `{ "token": "<access_jwt>" }`

---

## 1. Auth / Users

### Endpoints

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/api/users/register/` | No | Slim body only |
| POST | `/api/users/login/` | No | Email + password |
| POST | `/api/users/token/refresh/` | No | Refresh JWT |
| POST | `/api/users/google-login/` | No | `id_token`, optional `user_type` |
| POST | `/api/users/apple-login/` | No | `identity_token`, optional `user_type`, `full_name`, `email` |
| POST | `/api/users/forgot-password/` | No | Sends OTP email |
| POST | `/api/users/verify-reset-otp/` | No | Returns `reset_token` |
| POST | `/api/users/reset-password/` | No | Body includes `email` + `reset_token` + passwords |
| POST | `/api/users/change-password/` | Yes | Current + new password |
| GET | `/api/users/profile/` | Yes | Full profile (Flutter token/session check) |
| PUT/PATCH | `/api/users/profile/` | Yes | Update profile + optional multipart `profile_image` |
| PUT | `/api/users/profile/setup/` | Yes | One-time setup + optional multipart `profile_image` |
| GET | `/api/users/country-codes/` | No | Present; Flutter picker is local (unused) |
| POST | `/api/users/logout/` | Yes | Logout |
| GET | `/api/users/validate-token/` | Yes | Present; Flutter uses GET `/profile/` instead |
| GET | `/api/users/health/` | No | Health |

**Removed (do not use):** `POST /api/users/upload-profile-image/` — profile photos go only via multipart on `profile/setup/` or `profile/`.

### Register body (slim)

```json
{
  "email": "user@example.com",
  "password": "••••••••",
  "full_name": "Ali Khan",
  "user_type": "advertiser"
}
```

`user_type`: `"advertiser"` | `"media_owner"` only.  
**Not required at register:** phone, country_code, currency, company fields.

### Auth success envelope (login / register / Google / Apple)

```json
{
  "status_code": 200,
  "message": "...",
  "access": "<jwt>",
  "refresh": "<jwt>",
  "user": {
    "id": 12,
    "email": "user@example.com",
    "full_name": "Ali Khan",
    "phone": "+923001234567",
    "country_code": "PK",
    "user_type": "media_owner",
    "preferred_currency": "PKR",
    "profile_setup_completed": true
  }
}
```

New register user typically has:
- `preferred_currency`: `null`
- `profile_setup_completed`: `false`
- `phone` / `country_code`: `null`

### Profile setup — `PUT /api/users/profile/setup/`

Required-style fields Flutter sends:
- `profile_type`
- `preferred_language`
- `preferred_currency` (3-letter ISO, e.g. `PKR`)
- `phone`
- `country_code`
- Company fields when applicable
- Optional `profile_image` (multipart)

Sets `profile_setup_completed = true`.

### Profile GET — must include

- `preferred_currency`
- `profile_setup_completed`
- Plus: `id`, `email`, `full_name`, `phone`, `country_code`, `user_type`, company fields, `profile_image`, etc.

### Password reset flow

1. `forgot-password` → `{ "email": "..." }`
2. `verify-reset-otp` → `{ "email", "otp" }` → `{ "reset_token": "..." }`
3. `reset-password` → `{ "email", "reset_token", "new_password", "confirm_password" }`

Backend **requires** `email` (Flutter sends it).

### Profile image (multipart only)

Flutter uploads via multipart field `profile_image` on:

- `PUT /api/users/profile/setup/` (first-time)
- `PUT` / `PATCH /api/users/profile/` (later edits; supports `remove_profile_image`)

There is **no** separate `/upload-profile-image/` endpoint.

### Apple login body

```json
{
  "identity_token": "<apple_jwt>",
  "user_type": "advertiser",
  "full_name": "Optional",
  "email": "optional@example.com"
}
```

---

## 2. Chat — Socket.IO (primary) + REST attachments only

### Connect

- URL: `{baseUrl}/socket.io/`
- Auth: `{ "token": "<access>" }`
- On success server emits: `connected` → `{ "user_id", "online_user_ids": [...] }`

### Client → server ACK events

| Event | Payload in | ACK shape |
|-------|------------|-----------|
| `chat_sync` | `{ page, page_size }` | **Nested:** `{ status_code, unread: {...}, inbox: {...}, online_user_ids }` |
| `get_unread` | `{}` | **Flat:** `{ status_code, total_unread, rooms_with_unread, rooms: [{ room_id, unread_count }] }` |
| `get_inbox` | `{ page, page_size }` | **Flat:** `{ status_code, count, total_pages, current_page, page_size, results: [room...] }` |
| `get_room` | `{ room_id }` | `{ status_code, room: {...} }` |
| `get_or_create_room` | `{ billboard_id }` | `{ status_code, room: {...} }` |
| `get_messages` | `{ room_id, page, page_size }` | **Flat:** `{ status_code, results, total_pages, current_page, ... }` |
| `send_message` | `{ room_id, body }` | `{ status_code: 201, message: {...} }` |
| `get_presence` | `{}` | `{ status_code, online_user_ids: [...] }` |

### Client → server fire-and-forget (no ACK)

| Event | Payload |
|-------|---------|
| `join_room` | `{ room_id }` |
| `leave_room` | `{ room_id }` |
| `typing_start` | `{ room_id }` |
| `typing_stop` | `{ room_id }` |
| `message_delivered` | `{ room_id, message_id }` |
| `messages_seen` | `{ room_id, message_id }` |

### Server → client pushes Flutter listens to

| Event | Shape |
|-------|--------|
| `connected` | `{ user_id, online_user_ids }` |
| `new_message` | message object (or `{ message }` — Flutter unwraps both) |
| `message_sent` | `{ status_code, message }` or message — Flutter unwraps |
| `user_typing` | `{ room_id, user_id, is_typing: true\|false }` (+ optional `user_name`) |
| `message_delivered` | `{ room_id, message_id, user_id, status }` |
| `messages_seen` | `{ room_id, message_id, user_id, status }` |
| `inbox_updated` | `{ room_id, room, last_message, updated_at, unread_count }` |
| `unread_updated` | must include `{ total_unread }` (may include more keys) |
| `user_presence` | `{ user_id, is_online: true\|false }` (+ optional `user_name`) |
| `error` | `{ message, status_code }` |

Unused by Flutter (harmless): `room_joined`, `room_left`.

### Message object

```json
{
  "id": 44,
  "room_id": 7,
  "sender_id": 9,
  "sender_email": "adv@example.com",
  "sender_name": "Sara Adv",
  "body": "Hi",
  "message_type": "text",
  "status": "sent",
  "attachments": [
    {
      "id": 1,
      "original_name": "brief.pdf",
      "content_type": "application/pdf",
      "file_size": 12345,
      "url": "https://..."
    }
  ],
  "created_at": "2026-07-11T12:00:00+00:00"
}
```

Flutter ignores `sender_email`.

### Room object

```json
{
  "id": 7,
  "billboard_id": 101,
  "billboard": {
    "id": 101,
    "city": "Lahore",
    "road_name": "MM Alam",
    "ooh_media_type": "Digital Billboard",
    "image": "https://..."
  },
  "advertiser_id": 9,
  "media_owner_id": 12,
  "other_user": {
    "id": 9,
    "email": "adv@example.com",
    "full_name": "Sara Adv",
    "user_type": "advertiser"
  },
  "last_message": { /* message */ },
  "unread_count": 2,
  "created_at": "...",
  "updated_at": "..."
}
```

### REST chat (attachments only)

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/chat/rooms/{roomId}/messages/` | Yes |

Multipart: `attachment_0`, `attachment_1`, …  
Response includes message under `message_data` (or top-level message map).  
**No** REST inbox / text send — those are sockets only.

---

## 3. Guest mode (billboards)

### AllowAny (no JWT when guest — Flutter sends no `Authorization`)

| Method | Path |
|--------|------|
| GET | `/api/billboards/` |
| GET | `/api/billboards/{id}/` |
| GET | `/api/billboards/{id}/preview/` |
| GET | `/api/billboards/{id}/availability/` |
| GET | `/api/billboards/media-types/` |
| POST | `/api/billboards/{id}/track-view/` |

Anonymous detail/list: only **approved + active** public inventory.  
Owners (authenticated) can still see own pending/rejected via auth flows / my-billboards.

Backend also has `GET .../media-types/{id}/schema/` — Flutter does **not** call it (uses list `attributes`).

### Still require auth

| Method | Path |
|--------|------|
| POST | `/api/billboards/` (create) |
| PUT/PATCH/DELETE | `/api/billboards/{id}/` |
| POST | `/api/billboards/my-billboards/` |
| PATCH | `/api/billboards/{id}/toggle-active/` |
| POST | `/api/billboards/{id}/track-lead/` |
| GET/POST | `/api/billboards/wishlist/` |
| DELETE | `/api/billboards/wishlist/{id}/remove/` |
| POST | `/api/billboards/wishlist/{id}/toggle/` |

### Flutter guest notes

- Guest UI skips wishlist, chat, inbox, profile, create.
- `is_in_wishlist` defaults to `false` if missing.
- Flutter does **not** call `track-view` / `track-lead` / preferences / schema today (backend keeps them).

---

## 4. Media types + dynamic specifications

### Endpoints

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/billboards/media-types/` | Guest OK |
| GET | `/api/billboards/media-types/{id}/schema/` | Guest OK |

### Attribute object (on picker types + schema + `media_type_detail`)

```json
{
  "key": "screen_size",
  "label": "Screen Size",
  "field_type": "text",
  "required": true,
  "order": 1,
  "validation": { "max_length": 64 },
  "options": null,
  "help_text": ""
}
```

`field_type`: `text` | `number` | `integer` | `boolean` | `select` | `multiselect`  
Flutter: `options`/`validation` null → treat as `[]` / `{}`; `help_text` optional/ignored.

### Billboard embed — `media_type_detail` (MUST include attributes)

```json
"media_type_detail": {
  "id": 3,
  "name": "Digital Billboard",
  "slug": "digital-billboard",
  "category": "digital",
  "is_digital": true,
  "attributes": [ /* attribute objects above */ ]
}
```

Advertiser detail specs UI reads `media_type_detail.attributes`. Empty = blank specs section.

### Create billboard specs rules

- Specs keys must match media-type `attributes`.
- Unknown keys rejected.
- **`currency` must NOT be inside `specifications`** — Flutter strips it; backend also rejects it in specs.
- Billboard `currency` is set from owner `preferred_currency` on create.
- Validation errors under `specifications` field.

---

## 5. Billboards (other)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/billboards/` | Map/list (guest OK) |
| POST | `/api/billboards/` | Create (media_owner) |
| GET | `/api/billboards/{id}/` | Full detail |
| PUT/PATCH/DELETE | `/api/billboards/{id}/` | Owner |
| GET | `/api/billboards/{id}/preview/` | Map pin preview |
| GET | `/api/billboards/{id}/availability/` | Booked dates |
| PATCH | `/api/billboards/{id}/toggle-active/` | Owner |
| POST | `/api/billboards/my-billboards/` | Owner tabs (pending/approved/rejected) |
| Wishlist endpoints | as above | Auth |

---

## 6. In-app notifications inbox

**Not FCM.** Separate inbox under `/api/notifications/inbox/`.

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/notifications/inbox/unread-count/` | Yes |
| GET | `/api/notifications/inbox/` | Yes — `?page=&page_size=&is_read=&notification_type=` |
| GET | `/api/notifications/inbox/{uuid}/` | Yes — `?mark_read=true` (default true) |
| POST | `/api/notifications/inbox/{uuid}/read/` | Yes |
| POST | `/api/notifications/inbox/mark-all-read/` | Yes |

### Unread count

```json
{
  "status_code": 200,
  "message": "...",
  "unread_count": 3
}
```

### List

```json
{
  "status_code": 200,
  "message": "...",
  "links": { "next": null, "previous": null },
  "count": 10,
  "total_pages": 1,
  "current_page": 1,
  "results": [ /* notification items */ ],
  "unread_count": 3
}
```

### Notification item

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "notification_type": "new_chat_message",
  "notification_type_display": "New Chat Message",
  "title": "New message from Sara Adv",
  "body": "Hi, is this board free?",
  "data": {
    "room_id": 7,
    "message_id": 44,
    "billboard_id": 101,
    "sender_id": 9
  },
  "related_object_type": "chatmessage",
  "related_object_id": 44,
  "is_read": false,
  "read_at": null,
  "created_at": "2026-07-11T12:00:00+00:00"
}
```

Chat navigation uses `data.room_id` (and related fields).  
`related_object_type: "chatmessage"` is OK.

### Detail / mark-read

```json
{
  "status_code": 200,
  "message": "...",
  "notification": { /* item above */ },
  "unread_count": 2
}
```

(Detail may omit `unread_count`; mark-read includes it.)

### Mark all read

```json
{
  "status_code": 200,
  "message": "...",
  "marked_count": 3,
  "unread_count": 0
}
```

### Types backend can create (triggers)

| `notification_type` | Trigger |
|---------------------|---------|
| `new_chat_message` | Chat socket / attachment send |
| `billboard_approved` / `billboard_rejected` | Admin approval |
| `wishlist_added` | Wishlist add (owner notify) |
| `new_lead` | Track lead (Celery) |
| `new_view` | Views milestones (e.g. every 10) |
| `billboard_activated` / `billboard_deactivated` | Toggle active |

### Preferences (backend present; Flutter UI optional)

| Method | Path |
|--------|------|
| GET/PATCH | `/api/notifications/preferences/` |

Includes `chat_messages_enabled` (default `true`). When false, chat inbox rows skipped.

---

## 7. FCM device tokens

| Method | Path | Body |
|--------|------|------|
| POST | `/api/notifications/device-token/register/` | `{ "fcm_token", "device_type" }` |
| POST | `/api/notifications/device-token/unregister/` | `{ "fcm_token" }` |

`device_type`: `ios` | `android` | `web`  
`"unknown"` (desktop) → stored as `android`.

Also exists (legacy/admin):  
`GET /api/notifications/notifications/`, mark-opened, stats, test, send.

---

## 8. Models / migrations added (backend)

| App | Migration | What |
|-----|-----------|------|
| users | `0014_profile_setup_and_password_reset` | Profile setup fields, `preferred_currency`, `apple_sub`, `PasswordResetOTP` |
| billboards | `0016_billboard_currency` | Billboard `currency` |
| billboards | `0017_oohmediatypeattribute` | `OohMediaTypeAttribute` |
| notifications | `0004_usernotification_inbox` | `UserNotification`, `NEW_CHAT_MESSAGE`, `chat_messages_enabled` |

### New / expanded files (high level)

- `chat/presence.py`, expanded `chat/socket_handlers.py`, `chat/services.py`
- `notifications/inbox_service.py`, inbox views/urls
- `users/email_service.py`
- `billboards/management/commands/seed_media_type_attributes.py`
- Guides: `CHAT_SOCKET_MIGRATION_FLUTTER_WEB_GUIDE.md`, `GUEST_MODE_FLUTTER_GUIDE.md`, `IN_APP_NOTIFICATIONS_API_GUIDE.md`

---

## 9. Infra (server ops — not Flutter UI)

| Piece | Role |
|-------|------|
| Daphne ASGI | HTTP + Socket.IO (`core.asgi:application`) |
| Redis | Celery broker (`CELERY_BROKER_URL=redis://127.0.0.1:6379/0`) |
| Celery worker | Async `track-view` / `track-lead` (202 Accepted) |
| Chat presence | **In-memory** (per Daphne process) — not Redis |

Deploy units: `deploy/reachtolet-daphne.service`, `deploy/reachtolet-celery.service`.

After deploy:

```bash
python manage.py migrate
python manage.py seed_media_type_attributes
# restart redis, celery, daphne
```

---

## 10. Flutter `AppUrls` ↔ backend map

Every path Flutter defines is implemented:

| Flutter constant | Backend path |
|------------------|--------------|
| `signup` | `/api/users/register/` |
| `login` | `/api/users/login/` |
| `googleLogin` | `/api/users/google-login/` |
| `appleLogin` | `/api/users/apple-login/` |
| `forgotPassword` | `/api/users/forgot-password/` |
| `verifyResetOtp` | `/api/users/verify-reset-otp/` |
| `resetPassword` | `/api/users/reset-password/` |
| `changePassword` | `/api/users/change-password/` |
| `saveFcmToken` | `/api/notifications/device-token/register/` |
| `unregisterFcmToken` | `/api/notifications/device-token/unregister/` |
| `getBillboards` | `/api/billboards/` |
| `myBillboards` | `/api/billboards/my-billboards/` |
| `createBillboard` | `/api/billboards/` |
| `billboardMediaTypes` | `/api/billboards/media-types/` |
| `billboardDetail(id)` | `/api/billboards/{id}/` |
| `billboardPreview(id)` | `/api/billboards/{id}/preview/` |
| `billboardAvailability(id)` | `/api/billboards/{id}/availability/` |
| `billboardToggleActive(id)` | `/api/billboards/{id}/toggle-active/` |
| `logout` | `/api/users/logout/` |
| `refreshToken` | `/api/users/token/refresh/` |
| `getProfileInfo` / `updateProfile` | `/api/users/profile/` |
| `profileSetup` | `/api/users/profile/setup/` |
| `countryCodes` | `/api/users/country-codes/` (in AppUrls, unused — local picker) |
| wishlist add/fetch/remove/toggle | `/api/billboards/wishlist/...` |
| `fetchNotifications` | `/api/notifications/notifications/` (in AppUrls, unused — inbox replaced it) |
| `inboxUnreadCount` | `/api/notifications/inbox/unread-count/` |
| `inboxList` | `/api/notifications/inbox/` |
| `inboxDetail(id)` | `/api/notifications/inbox/{id}/` |
| `inboxMarkRead(id)` | `/api/notifications/inbox/{id}/read/` |
| `inboxMarkAllRead` | `/api/notifications/inbox/mark-all-read/` |
| `chatMessages(roomId)` | `/api/chat/rooms/{roomId}/messages/` |

---

## 11. Nesting shapes Flutter depends on (do not break)

1. **`get_unread` ACK** — flat (not wrapped in `unread`)
2. **`get_inbox` ACK** — flat (not wrapped in `inbox`)
3. **`chat_sync`** — nested `unread` + `inbox` (different from 1–2)
4. **`get_room` / `get_or_create_room`** — `{ room: {...} }`
5. **`send_message` ACK** — `{ message: {...} }`
6. **`user_typing`** — `{ room_id, user_id, is_typing }`
7. **`unread_updated`** — includes `total_unread`
8. **`user_presence`** — `{ user_id, is_online }`
9. **Auth `user`** — includes `preferred_currency` + `profile_setup_completed`
10. **`media_type_detail.attributes[]`** — same attribute shape as media-types list

---

## 12. Confirmation checklist (Flutter team)

Tick when verified against a live/deployed backend:

- [ ] Register slim body works; no phone required
- [ ] Login/Google/Apple `user` has `preferred_currency` + `profile_setup_completed`
- [ ] Profile GET syncs currency + setup flag (Flutter uses this instead of validate-token)
- [ ] Profile setup PUT completes gate; multipart `profile_image` works
- [ ] Profile PUT/PATCH multipart `profile_image` works (no upload-profile-image URL)
- [ ] Forgot → OTP → reset with `{ email, reset_token, new_password, confirm_password }`
- [ ] Change password works
- [ ] Guest can browse list/detail/preview/availability without JWT
- [ ] Guest blocked from wishlist/chat/inbox/create with sign-in prompts
- [ ] Media types list returns `attributes[]`
- [ ] Billboard detail `media_type_detail.attributes[]` non-empty for seeded types
- [ ] Create billboard specs from attributes; currency not in specs; board gets owner currency
- [ ] Socket connects with `auth: { token }`
- [ ] `chat_sync` / flat `get_unread` / flat `get_inbox` parse
- [ ] `get_or_create_room` + `send_message` + `new_message` work
- [ ] Typing / presence / unread_updated update UI
- [ ] Attachment POST returns `message_data`
- [ ] Inbox unread-count / list / detail / mark-read / mark-all-read
- [ ] Chat message creates inbox row with `data.room_id`
- [ ] FCM register accepts ios/android/web; unknown OK

---

**Bottom line for Flutter:** Backend implements the full contract (auth, profile multipart image, guest browse, dynamic specs, socket chat, inbox, FCM). Confirm against a **deployed** host after migrate + seed + Daphne/Celery/Redis restart — local code alone does not update `16.16.160.64` until deployed.
