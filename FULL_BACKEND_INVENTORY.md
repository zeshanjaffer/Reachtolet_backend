# Reachtolet Backend — Full Inventory (A–Z)

Complete reference of **every model, table, column, HTTP API, Socket.IO event, Celery task, and management command** in this project. Use this when rebuilding a new backend.

**Stack today:** Django 5 + DRF + Daphne (ASGI) + Socket.IO + Celery + Redis + PostGIS  
**Base (app):** `http://16.16.160.64:8000`

---

# Part A — Database models & tables

**Live apps with models:** `users`, `billboards`, `chat`, `notifications`, `admin_panel`, `locations`  
**Total live models:** 25  
**Not live:** `adbuq` (orphaned migration only; not in `INSTALLED_APPS`)

Unless noted, every model has implicit PK `id` = `BigAutoField`.

---

## A1. App: `users`

### Table `users_user` — model `User`

Custom user (`AbstractUser`). Login field = `email`. `username` removed.

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `password` | CharField(128) | NO | — | |
| `last_login` | DateTimeField | YES | — | |
| `is_superuser` | BooleanField | NO | False | |
| `first_name` | CharField(150) | NO | '' | blank |
| `last_name` | CharField(150) | NO | '' | blank |
| `is_staff` | BooleanField | NO | False | |
| `is_active` | BooleanField | NO | True | |
| `date_joined` | DateTimeField | NO | now | |
| `email` | EmailField | NO | — | **UNIQUE**, login |
| `full_name` | CharField(150) | NO | — | |
| `country_code` | CharField(3) | YES | — | ISO alpha-2 |
| `phone` | CharField(20) | YES | — | E.164 style |
| `name` | CharField(150) | YES | — | legacy |
| `profile_image` | ImageField | YES | — | `profile_images/` |
| `user_type` | CharField(20) | NO | `advertiser` | `advertiser` \| `media_owner` |
| `profile_type` | CharField(20) | YES | — | `individual` \| `company` |
| `preferred_currency` | CharField(3) | YES | — | ISO 4217 |
| `preferred_language` | CharField(10) | YES | — | |
| `company_name` | CharField(200) | YES | — | |
| `company_size` | CharField(20) | YES | — | |
| `company_website` | CharField(255) | YES | — | |
| `company_address` | TextField | YES | — | |
| `profile_setup_completed` | BooleanField | NO | False | setup gate |
| `apple_sub` | CharField(255) | YES | — | **UNIQUE**, Apple Sign In |

M2M (auth): `groups`, `user_permissions`  
Indexes: `(user_type, is_active)`

---

### Table `users_passwordresetotp` — model `PasswordResetOTP`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `email` | EmailField | NO | — | indexed |
| `otp_hash` | CharField(128) | NO | — | |
| `attempts` | PositiveSmallInteger | NO | 0 | |
| `created_at` | DateTimeField | NO | auto_now_add | |
| `is_used` | BooleanField | NO | False | |
| `reset_token` | UUIDField | YES | None | **UNIQUE** |
| `reset_token_created_at` | DateTimeField | YES | — | |

Indexes: `(email, is_used)`

---

## A2. App: `billboards`

### Table `billboards_oohmediatype` — model `OohMediaType`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `name` | CharField(100) | NO | — | **UNIQUE** |
| `slug` | SlugField(120) | NO | — | **UNIQUE** |
| `category` | CharField(20) | NO | — | digital/static/place/transit/other |
| `parent_id` | FK → self | YES | — | SET_NULL, `children` |
| `is_selectable` | BooleanField | NO | True | false = group header |
| `is_digital` | BooleanField | NO | False | |
| `sort_order` | PositiveInteger | NO | 0 | |
| `is_active` | BooleanField | NO | True | indexed |

Ordering: `sort_order`, `name`

---

### Table `billboards_oohmediatypeattribute` — model `OohMediaTypeAttribute`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `media_type_id` | FK → OohMediaType | NO | — | CASCADE, `attributes` |
| `key` | SlugField(80) | NO | — | unique with media_type |
| `label` | CharField(120) | NO | — | |
| `field_type` | CharField(20) | NO | — | text/number/integer/boolean/select/multiselect |
| `required` | BooleanField | NO | False | |
| `options` | JSONField | YES | — | |
| `validation` | JSONField | YES | — | |
| `order` | PositiveInteger | NO | 0 | |
| `help_text` | CharField(255) | NO | '' | blank OK |
| `is_active` | BooleanField | NO | True | |

`unique_together`: `(media_type, key)`

---

### Table `billboards_billboard` — model `Billboard`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `user_id` | FK → User | YES | — | CASCADE, owner |
| `city` | CharField(100) | NO | — | indexed |
| `description` | TextField | YES | — | |
| `number_of_boards` | CharField(10) | YES | — | |
| `average_daily_views` | CharField(20) | YES | — | |
| `traffic_direction` | CharField(100) | YES | — | |
| `road_position` | CharField(100) | YES | — | |
| `road_name` | CharField(100) | YES | — | |
| `exposure_time` | CharField(100) | YES | — | |
| `price_range` | CharField(100) | YES | — | |
| `currency` | CharField(3) | YES | — | from owner preferred_currency |
| `display_height` | CharField(20) | YES | — | |
| `display_width` | CharField(20) | YES | — | |
| `advertiser_phone` | CharField(20) | YES | — | |
| `advertiser_whatsapp` | CharField(100) | YES | — | |
| `company_name` | CharField(100) | YES | — | indexed |
| `company_website` | CharField(200) | YES | — | |
| `ooh_media_type` | CharField(100) | NO | — | denormalized name |
| `media_type_id` | FK → OohMediaType | YES | — | PROTECT |
| `ooh_media_id` | CharField(100) | YES | — | |
| `type` | CharField(50) | NO | — | indexed |
| `images` | JSONField | NO | `[]` | URL list |
| `specifications` | JSONField | NO | `{}` | attribute key→value |
| `unavailable_dates` | JSONField | NO | `[]` | booked dates |
| `latitude` | FloatField | YES | — | indexed |
| `longitude` | FloatField | YES | — | indexed |
| `location` | PointField (PostGIS) | YES | — | geography SRID 4326 |
| `views` | IntegerField | NO | 0 | |
| `leads` | IntegerField | NO | 0 | indexed |
| `is_active` | BooleanField | NO | True | indexed |
| `address` | TextField | YES | — | |
| `generator_backup` | CharField(3) | YES | — | Yes/No |
| `approval_status` | CharField(20) | NO | `pending` | pending/approved/rejected |
| `approved_at` | DateTimeField | YES | — | |
| `rejected_at` | DateTimeField | YES | — | |
| `rejection_reason` | TextField | YES | — | |
| `approved_by_id` | FK → User | YES | — | SET_NULL |
| `rejected_by_id` | FK → User | YES | — | SET_NULL |
| `created_at` | DateTimeField | NO | auto_now_add | indexed |

Multiple composite indexes on active/approval/geo/user (see models Meta).

---

### Table `billboards_wishlist` — model `Wishlist`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `user_id` | FK → User | NO | — | CASCADE |
| `billboard_id` | FK → Billboard | NO | — | CASCADE |
| `created_at` | DateTimeField | NO | auto_now_add | |

`unique_together`: `(user, billboard)`

---

### Table `billboards_lead` — model `Lead`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `billboard_id` | FK → Billboard | NO | — | CASCADE |
| `user_id` | FK → User | YES | — | SET_NULL |
| `user_ip` | GenericIPAddress | YES | — | |
| `user_agent` | TextField | YES | — | |
| `created_at` | DateTimeField | NO | auto_now_add | |

---

### Table `billboards_view` — model `View`

Same columns as `Lead` (billboard, user, user_ip, user_agent, created_at).

---

## A3. App: `chat`

### Table `chat_chatroom` — model `ChatRoom`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `billboard_id` | FK → Billboard | NO | — | CASCADE |
| `advertiser_id` | FK → User | NO | — | CASCADE |
| `media_owner_id` | FK → User | NO | — | CASCADE |
| `created_at` | DateTimeField | NO | auto_now_add | |
| `updated_at` | DateTimeField | NO | auto_now | |

Unique: `(billboard, advertiser)`

---

### Table `chat_chatroomparticipant` — model `ChatRoomParticipant`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `room_id` | FK → ChatRoom | NO | — | CASCADE |
| `user_id` | FK → User | NO | — | CASCADE |
| `last_read_message_id` | FK → ChatMessage | YES | — | SET_NULL |
| `last_read_at` | DateTimeField | YES | — | |

Unique: `(room, user)`

---

### Table `chat_chatmessage` — model `ChatMessage`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `room_id` | FK → ChatRoom | NO | — | CASCADE |
| `sender_id` | FK → User | NO | — | CASCADE |
| `body` | TextField | NO | '' | blank OK |
| `message_type` | CharField(20) | NO | `text` | text/attachment/mixed |
| `status` | CharField(20) | NO | `sent` | sent/delivered/seen |
| `created_at` | DateTimeField | NO | auto_now_add | |

---

### Table `chat_chatattachment` — model `ChatAttachment`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `message_id` | FK → ChatMessage | NO | — | CASCADE |
| `file` | FileField | NO | — | `chat_attachments/%Y/%m/` |
| `original_name` | CharField(255) | NO | — | |
| `content_type` | CharField(100) | NO | '' | |
| `file_size` | PositiveInteger | NO | 0 | |
| `created_at` | DateTimeField | NO | auto_now_add | |

---

## A4. App: `notifications`

### Enum `NotificationType`

`new_lead`, `new_view`, `wishlist_added`, `billboard_activated`, `billboard_deactivated`, `billboard_approved`, `billboard_rejected`, `price_update`, `system_message`, `welcome`, `new_chat_message`

---

### Table `notifications_usernotification` — model `UserNotification`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | UUIDField | NO | uuid4 | **PK** |
| `recipient_id` | FK → User | NO | — | CASCADE |
| `notification_type` | CharField(50) | NO | — | NotificationType |
| `title` | CharField(255) | NO | — | |
| `body` | TextField | NO | — | |
| `data` | JSONField | NO | `{}` | e.g. room_id, message_id |
| `related_object_type` | CharField(50) | NO | '' | |
| `related_object_id` | PositiveInteger | YES | — | |
| `is_read` | BooleanField | NO | False | |
| `read_at` | DateTimeField | YES | — | |
| `created_at` | DateTimeField | NO | auto_now_add | |

---

### Table `notifications_pushnotification` — model `PushNotification`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | UUIDField | NO | uuid4 | PK |
| `recipient_id` | FK → User | NO | — | |
| `notification_type` | CharField(50) | NO | — | |
| `title` | CharField(255) | NO | — | |
| `body` | TextField | NO | — | |
| `fcm_token` | CharField(255) | NO | — | |
| `device_type` | CharField(10) | NO | `android` | ios/android/web |
| `content_type_id` | FK → ContentType | YES | — | GFK |
| `object_id` | PositiveInteger | YES | — | GFK |
| `data` | JSONField | NO | `{}` | |
| `message_id` | CharField(255) | YES | — | FCM id |
| `sent_at` | DateTimeField | NO | auto_now_add | |
| `delivered` | BooleanField | NO | False | |
| `delivered_at` | DateTimeField | YES | — | |
| `opened` | BooleanField | NO | False | |
| `opened_at` | DateTimeField | YES | — | |
| `error_message` | TextField | YES | — | |
| `retry_count` | IntegerField | NO | 0 | |
| `max_retries` | IntegerField | NO | 3 | |

---

### Table `notifications_device_token` — model `DeviceToken`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `user_id` | FK → User | NO | — | |
| `fcm_token` | CharField(255) | NO | — | **UNIQUE** |
| `device_type` | CharField(10) | NO | `android` | ios/android/web |
| `device_id` | CharField(255) | YES | — | |
| `app_version` | CharField(20) | YES | — | |
| `os_version` | CharField(20) | YES | — | |
| `is_active` | BooleanField | NO | True | |
| `created_at` | DateTimeField | NO | auto_now_add | |
| `last_used` | DateTimeField | NO | auto_now | |

---

### Table `notifications_notification_preference` — model `NotificationPreference`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `user_id` | OneToOne → User | NO | — | |
| `new_leads_enabled` | BooleanField | NO | True | |
| `new_views_enabled` | BooleanField | NO | True | |
| `wishlist_updates_enabled` | BooleanField | NO | True | |
| `system_messages_enabled` | BooleanField | NO | True | |
| `chat_messages_enabled` | BooleanField | NO | True | |
| `push_enabled` | BooleanField | NO | True | |
| `sound_enabled` | BooleanField | NO | True | |
| `vibration_enabled` | BooleanField | NO | True | |
| `quiet_hours_enabled` | BooleanField | NO | False | |
| `quiet_hours_start` | TimeField | YES | — | |
| `quiet_hours_end` | TimeField | YES | — | |
| `created_at` | DateTimeField | NO | auto_now_add | |
| `updated_at` | DateTimeField | NO | auto_now | |

---

### Table `notifications_notification_template` — model `NotificationTemplate`

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | BigAutoField | NO | auto | PK |
| `name` | CharField(100) | NO | — | **UNIQUE** |
| `notification_type` | CharField(50) | NO | — | |
| `title_template` | CharField(255) | NO | — | |
| `body_template` | TextField | NO | — | |
| `data_template` | JSONField | NO | `{}` | |
| `is_active` | BooleanField | NO | True | |
| `created_at` | DateTimeField | NO | auto_now_add | |
| `updated_at` | DateTimeField | NO | auto_now | |

---

## A5. App: `admin_panel`

### `admin_panel_notification_campaign` — `AdminNotificationCampaign`

UUID PK. Fields: `title`, `message`, `recipient_type` (all_users/billboard_owners/advertisers/specific_users), `template_name`, `custom_data`, `status` (draft/scheduled/sending/sent/failed), `scheduled_at`, `sent_at`, counters (`total_recipients`, `sent_count`, `delivered_count`, `opened_count`, `failed_count`), `created_by_id` → User, `created_at`, `updated_at`.

### `admin_panel_notification_recipient` — `AdminNotificationRecipient`

FK `campaign`, FK `user`, `status` (pending/sent/delivered/opened/failed), `fcm_token`, `device_type`, `message_id`, timestamps, `error_message`, `retry_count`. Unique `(campaign, user)`.

### `admin_panel_notification_template` — `AdminNotificationTemplate`

`name` UNIQUE, `title`, `message`, `description`, `recipient_type`, `variables` JSON, `is_active`, `usage_count`, timestamps.

### `admin_panel_notification_analytics` — `AdminNotificationAnalytics`

OneToOne → campaign. Counters + rates (`delivery_rate`, `open_rate`, `failure_rate`), platform counts, `avg_delivery_time`, `peak_delivery_time`, `last_updated`.

---

## A6. App: `locations`

### `locations_state` — `State`

`legacy_id` UNIQUE, `name`, `abbr`, `capital`, `coordinates`, `latitude`, `longitude` (Decimal), `enabled`, `deleted_at`, `country_id`, `image`, `region`.

### `locations_city` — `City`

`legacy_id` UNIQUE, `state_abbr`, `name`, `coordinates`, `enabled`, `deleted_at`, `country_id`, `image`, `county_name`, `state_name`, `zip_codes`, `place_type`, `latitude`/`longitude` (Char), `area_code`, `population`, `households`, `median_income`, `land_area`, `water_area`, `time_zone`.

### `locations_cityboundary` — `CityBoundary`

`legacy_id` UNIQUE, `city`, `state`, `boundary` JSON, `deleted_at`. Unique `(city, state)`.

### `locations_stateboundary` — `StateBoundary`

`legacy_id` UNIQUE, `state` UNIQUE, `boundary` JSON, `deleted_at`.

---

## A7. Django built-in tables (also present)

Typical Django/auth tables also exist: `auth_group`, `auth_permission`, `django_content_type`, `django_migrations`, `django_session`, `django_admin_log`, JWT blacklist tables if enabled, etc.

---

# Part B — HTTP APIs (full list)

## B1. Users — `/api/users/`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/users/register/` | Public | Slim signup |
| POST | `/api/users/login/` | Public | Email/password → JWT + user |
| POST | `/api/users/token/refresh/` | Public | Refresh JWT |
| GET | `/api/users/validate-token/` | Auth | Validate token (Flutter uses profile instead) |
| GET | `/api/users/country-codes/` | Public | Country dial list (Flutter unused) |
| GET | `/api/users/profile/` | Auth | Get profile |
| PUT/PATCH | `/api/users/profile/` | Auth | Update profile (+ multipart `profile_image`) |
| PUT | `/api/users/profile/setup/` | Auth | One-time setup (+ multipart image) |
| POST | `/api/users/google-login/` | Public | Google `id_token` |
| POST | `/api/users/apple-login/` | Public | Apple `identity_token` |
| POST | `/api/users/forgot-password/` | Public | Send OTP |
| POST | `/api/users/verify-reset-otp/` | Public | OTP → `reset_token` |
| POST | `/api/users/reset-password/` | Public | `{email, reset_token, new_password, confirm_password}` |
| POST | `/api/users/change-password/` | Auth | Change password |
| POST | `/api/users/logout/` | Bearer and/or refresh | Logout / blacklist |
| GET | `/api/users/health/` | Public | Health |

**Removed:** `POST /api/users/upload-profile-image/` (use multipart on profile/setup or profile).

---

## B2. Billboards — `/api/billboards/`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/billboards/` | Public GET | List / map / cluster / search / filter |
| POST | `/api/billboards/` | Auth (media_owner) | Create (multipart images) |
| POST | `/api/billboards/my-billboards/` | Auth (media_owner) | Owner list by `approval_status` |
| GET | `/api/billboards/{id}/` | Public GET* | Detail (*anon = approved+active) |
| PUT/PATCH | `/api/billboards/{id}/` | Auth owner | Update |
| DELETE | `/api/billboards/{id}/` | Auth owner | Delete |
| GET | `/api/billboards/{id}/preview/` | Public | Map pin preview |
| GET | `/api/billboards/{id}/availability/` | Public | Booked dates (`from`/`to` optional) |
| PUT | `/api/billboards/{id}/availability/` | Auth owner | `{ booked_dates: [...] }` |
| PATCH | `/api/billboards/{id}/toggle-active/` | Auth owner | Toggle `is_active` |
| POST | `/api/billboards/{id}/track-view/` | Public | Queue view (Celery 202) |
| POST | `/api/billboards/{id}/increment-view/` | Public | Alias of track-view |
| POST | `/api/billboards/{id}/track-lead/` | Auth | Queue lead (Celery 202) |
| GET | `/api/billboards/media-types/` | Public | Groups + `attributes[]` |
| GET | `/api/billboards/media-types/{id}/schema/` | Public | Type + attributes schema |
| GET | `/api/billboards/wishlist/` | Auth | Wishlist list |
| POST | `/api/billboards/wishlist/` | Auth | Add (Flutter uses toggle) |
| DELETE | `/api/billboards/wishlist/{id}/remove/` | Auth | Remove (Flutter unused) |
| POST | `/api/billboards/wishlist/{id}/toggle/` | Auth | Toggle heart |
| GET | `/api/billboards/pending/` | Admin | Pending approvals |
| POST | `/api/billboards/{id}/approval-status/` | Admin | Approve/reject |

**List query params (examples):** `search`, `page`, `page_size`, `ooh_media_type`, `city`, `lat`/`lng`/`radius`, `cluster`, `ne_lat`/`ne_lng`/`sw_lat`/`sw_lng`, filters via django-filter.

---

## B3. Chat REST — `/api/chat/`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/chat/rooms/{room_id}/messages/` | Auth | Attachments only (`attachment_0`…); → `message_data` |

Text chat = Socket.IO only.

---

## B4. Notifications — `/api/notifications/`

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/notifications/device-token/register/` | Auth | FCM register |
| POST | `/api/notifications/device-token/unregister/` | Auth | FCM unregister |
| GET/PUT/PATCH | `/api/notifications/preferences/` | Auth | Prefs (Flutter unused UI) |
| GET | `/api/notifications/inbox/unread-count/` | Auth | Badge |
| GET | `/api/notifications/inbox/` | Auth | List (`page`, `is_read`, `notification_type`) |
| GET | `/api/notifications/inbox/{uuid}/` | Auth | Detail (`?mark_read=`) |
| POST | `/api/notifications/inbox/{uuid}/read/` | Auth | Mark one |
| POST | `/api/notifications/inbox/mark-all-read/` | Auth | Mark all |
| GET | `/api/notifications/notifications/` | Auth | Legacy push history |
| POST | `/api/notifications/notifications/{uuid}/mark-opened/` | Auth | Mark push opened |
| POST | `/api/notifications/notifications/mark-all-opened/` | Auth | Mark all opened |
| GET | `/api/notifications/stats/` | Auth | User push stats |
| POST | `/api/notifications/test/` | Auth | Test push |
| POST | `/api/notifications/send/` | Admin | Send push |

---

## B5. Admin panel — `/api/admin-panel/`

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/admin-panel/admin/auth/login/` | Staff login |
| GET | `/api/admin-panel/admin/auth/me/` | Current admin |
| POST | `/api/admin-panel/admin/auth/logout/` | Logout |
| GET/POST | `/api/admin-panel/admin/campaigns/` | Campaigns |
| GET/PUT/PATCH/DELETE | `/api/admin-panel/admin/campaigns/{uuid}/` | Campaign detail |
| POST | `/api/admin-panel/admin/campaigns/create/` | Create + recipients |
| GET | `/api/admin-panel/admin/campaigns/{id}/analytics/` | Analytics |
| GET/POST | `/api/admin-panel/admin/templates/` | Templates |
| GET/PUT/PATCH/DELETE | `/api/admin-panel/admin/templates/{id}/` | Template detail |
| GET | `/api/admin-panel/admin/users/` | Target users |
| POST | `/api/admin-panel/admin/send/` | Send |
| POST | `/api/admin-panel/admin/bulk-action/` | Bulk |
| GET | `/api/admin-panel/admin/stats/` | Stats |

---

## B6. Docs / admin UI

| Path | Purpose |
|------|---------|
| `/admin/` | Django admin |
| `/swagger/`, `/redoc/` | API docs |
| `/swagger.json` | Schema |

---

# Part C — Socket.IO

**Path:** `/socket.io/`  
**Auth:** `{ "token": "<access_jwt>" }`

### Connect / disconnect
- `connect` → emit `connected` `{ user_id, online_user_ids }`, presence broadcast  
- `disconnect` → presence offline if last sid  

### Client → server ACK

| Event | In | Out |
|-------|-----|-----|
| `chat_sync` | page, page_size | nested `unread`, `inbox`, `online_user_ids` |
| `get_unread` | {} | flat `total_unread`, `rooms_with_unread`, `rooms` |
| `get_inbox` | page, page_size | flat rooms page |
| `get_room` | room_id | `{ room }` |
| `get_or_create_room` | billboard_id | `{ room }` |
| `get_messages` | room_id, page, page_size | flat messages page |
| `send_message` | room_id, body | `{ message }` |
| `get_presence` | {} | `online_user_ids` |

### Client → server fire-and-forget

`join_room`, `leave_room`, `typing_start`, `typing_stop`, `message_delivered`, `messages_seen`

### Server → client

`connected`, `new_message`, `message_sent`, `user_typing`, `message_delivered`, `messages_seen`, `inbox_updated`, `unread_updated`, `user_presence`, `error`, (+ unused by Flutter: `room_joined`, `room_left`)

---

# Part D — Celery / Redis / infra

| Piece | Detail |
|-------|--------|
| Broker | Redis `CELERY_BROKER_URL` default `redis://127.0.0.1:6379/0` |
| Task | `track_billboard_view_task` |
| Task | `track_billboard_lead_task` |
| ASGI | Daphne + Socket.IO (`core.asgi:application`) |
| Presence | In-memory per Daphne process (not Redis) |
| Cache | LocMem (not Redis) |

---

# Part E — Management commands

| Command | App | Purpose |
|---------|-----|---------|
| `seed_media_type_attributes` | billboards | Seed attribute schemas |
| `seed_locations` | locations | Seed states/cities/boundaries |
| `send_test_notification` | notifications | Test FCM blast |

---

# Part F — Entity relationship (short)

```
User ──┬── Billboard (owner)
       ├── Wishlist ── Billboard
       ├── ChatRoom (as advertiser OR media_owner) ── Billboard
       │      └── ChatMessage ── ChatAttachment
       │      └── ChatRoomParticipant
       ├── UserNotification (inbox)
       ├── PushNotification
       ├── DeviceToken
       └── NotificationPreference (1:1)

OohMediaType ── OohMediaTypeAttribute
OohMediaType ── Billboard.media_type

Billboard ── Lead / View (tracking rows)
```

---

# Part G — Counts summary

| Area | Count |
|------|-------|
| Live Django models | 25 |
| User HTTP endpoints | 16 |
| Billboard HTTP endpoints | ~18 |
| Chat REST | 1 |
| Notification HTTP | 14 |
| Admin-panel HTTP | 13 |
| Socket client events (excl connect) | 14 |
| Socket server emit names | 12 |
| Celery tasks | 2 |
| Management commands | 3 |

---

# Part H — Flutter vs full backend

**Flutter actually uses:** auth + profile setup + guest browse + wishlist toggle/GET + inbox + sockets + chat attachments + media-owner CRUD/availability/toggle/media-types/my-billboards + FCM register/unregister.

**Backend extras (keep if rebuilding admin/ops):** admin-panel APIs, preferences, legacy notifications list, track-view/lead, schema URL, country-codes, validate-token, pending approval APIs, locations seed data, push templates/campaigns.

---

**File purpose:** Rebuild checklist. For Flutter contract shapes (nested ACK payloads, auth user fields), also see `FLUTTER_BACKEND_CONTRACT_CHECKLIST.md`.
