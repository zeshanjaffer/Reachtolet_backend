# Guest Mode Flutter Guide

Anonymous users can browse approved, active billboards without a JWT.

## Public (no auth)

| Method | Path | Notes |
|---|---|---|
| GET | `/api/billboards/` | Map/list — approved + active only |
| GET | `/api/billboards/{id}/` | Detail — approved + active only |
| GET | `/api/billboards/{id}/preview/` | Pin preview |
| GET | `/api/billboards/{id}/availability/` | Calendar booked dates |
| GET | `/api/billboards/media-types/` | Picker + nested `attributes` |
| GET | `/api/billboards/media-types/{id}/schema/` | Type + attribute schema |
| POST | `/api/billboards/{id}/track-view/` | Guest OK (IP dedup) |

## Still requires auth

| Method | Path |
|---|---|
| POST | `/api/billboards/` (media_owner) |
| PUT/PATCH/DELETE | `/api/billboards/{id}/` |
| POST | `/api/billboards/my-billboards/` |
| POST | `/api/billboards/{id}/track-lead/` |
| Wishlist | `/api/billboards/wishlist/...` |
| PUT | `/api/billboards/{id}/availability/` |
| POST | `/api/billboards/{id}/toggle-active/` |

## Owner exception on detail/preview

Authenticated **media owners** can still GET their own pending/rejected/inactive boards.

## Flutter tips

- Call public GETs without `Authorization`.
- After login, re-fetch detail if owner needs pending boards.
- `track-lead` and wishlist still need a token — prompt sign-in on those CTAs.
- `is_in_wishlist` is always `false` for guests.
