# In-App Notifications API Guide

Persistent inbox under `/api/notifications/inbox/` (auth required). Rows are created for leads, views milestones, wishlist, approve/reject, activate/deactivate, and chat messages. FCM push is attempted when preferences allow.

## Preference

`GET/PATCH /api/notifications/preferences/` includes `chat_messages_enabled` (default `true`). When false, chat inbox rows and chat push are skipped.

## Endpoints

### Unread count

`GET /api/notifications/inbox/unread-count/`

```json
{ "status_code": 200, "message": "...", "unread_count": 3 }
```

### List

`GET /api/notifications/inbox/?page=1&page_size=20&is_read=false&notification_type=new_chat_message`

Paginated `results` plus `unread_count`, `status_code`, `message`.

### Detail

`GET /api/notifications/inbox/{uuid}/?mark_read=true` (default marks read)

```json
{ "status_code": 200, "message": "...", "notification": { ... } }
```

### Mark one read

`POST /api/notifications/inbox/{uuid}/read/`

```json
{ "status_code": 200, "message": "...", "notification": { ... }, "unread_count": 2 }
```

### Mark all read

`POST /api/notifications/inbox/mark-all-read/`

```json
{ "status_code": 200, "message": "...", "marked_count": 5, "unread_count": 0 }
```

## Notification object

| Field | Notes |
|---|---|
| `id` | UUID string |
| `notification_type` | e.g. `new_lead`, `new_chat_message` |
| `title`, `body` | Display text |
| `data` | JSON extras (`billboard_id`, `room_id`, …) |
| `is_read`, `read_at`, `created_at` | |

## Chat `data` payload

```json
{
  "room_id": 12,
  "message_id":  subs,
  "billboard_id": 40,
  "sender_id": 7
}
```

## Types

`new_lead`, `new_view`, `wishlist_added`, `billboard_activated`, `billboard_deactivated`, `billboard_approved`, `billboard_rejected`, `new_chat_message`, `system_message`, …
