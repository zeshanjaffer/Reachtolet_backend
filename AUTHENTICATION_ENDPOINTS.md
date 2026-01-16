# 🔐 Authentication API Endpoints

**Base URL:** `http://44.200.108.209:8000`

---

## 1. Signup (Register)

**Endpoint:** `POST /api/users/register/`

**User Types:**
- `"advertiser"` - For users who want to advertise on billboards
- `"media_owner"` - For users who own billboards/media spaces

**Required Fields:**
- `email` (required) - Must be unique
- `password` (required)
- `full_name` (required) - User's full name
- `phone` (required) - Must be in international format with country code included (e.g., +12345678901 for US)
- `country_code` (required) - ISO 3166-1 alpha-2 code (e.g., US, GB)
- `user_type` (required) - Must be "advertiser" or "media_owner"

**Phone Number Format:**
- **US/Canada:** `+1` followed by 10 digits (e.g., `+12345678901`)
- **UK:** `+44` followed by 10-11 digits (e.g., `+441234567890`)
- **India:** `+91` followed by 10 digits (e.g., `+911234567890`)
- The phone number must include the country's dial code prefix

**cURL (Advertiser - US):**
```bash
curl --location 'http://44.200.108.209:8000/api/users/register/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "advertiser@example.com",
    "password": "TestPassword123!",
    "full_name": "John Doe",
    "user_type": "advertiser",
    "phone": "+12345678901",
    "country_code": "US"
}'
```

**cURL (Media Owner - UK):**
```bash
curl --location 'http://44.200.108.209:8000/api/users/register/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "owner@example.com",
    "password": "TestPassword123!",
    "full_name": "Jane Smith",
    "user_type": "media_owner",
    "phone": "+441234567890",
    "country_code": "GB"
}'
```

**Success Response (201):**
```json
{
    "user": {
        "id": 1,
        "email": "advertiser@example.com",
        "full_name": "John Doe",
        "phone": "+12345678901",
        "country_code": "US",
        "user_type": "advertiser"
    },
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "message": "User registered successfully"
}
```

**Error Response (400) - Missing Fields:**
```json
{
    "email": ["This field is required."],
    "password": ["This field is required."],
    "full_name": ["This field is required."],
    "phone": ["This field is required."],
    "country_code": ["This field is required."],
    "user_type": ["This field is required."]
}
```

**Error Response (400) - Invalid User Type:**
```json
{
    "user_type": ["user_type must be one of: advertiser, media_owner"]
}
```

---

## 2. Login

**Endpoint:** `POST /api/users/login/`

**cURL:**
```bash
curl --location 'http://44.200.108.209:8000/api/users/login/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "user@example.com",
    "password": "TestPassword123!"
}'
```

**Success Response (200):**
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "user_type": "advertiser"
    }
}
```

**Error Response (401):**
```json
{
    "detail": "No active account found with the given credentials"
}
```

---

## 3. Refresh Token

**Endpoint:** `POST /api/users/token/refresh/`

**cURL:**
```bash
curl --location 'http://44.200.108.209:8000/api/users/token/refresh/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}'
```

**Success Response (200):**
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Response (401):**
```json
{
    "detail": "Token is invalid or expired",
    "code": "token_not_valid"
}
```

---

## 4. Validate Token

**Endpoint:** `GET /api/users/validate-token/`

**cURL:**
```bash
curl --location 'http://44.200.108.209:8000/api/users/validate-token/' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

**Success Response (200):**
```json
{
    "valid": true,
    "user": {
        "id": 1,
        "email": "user@example.com",
        "user_type": "advertiser"
    }
}
```

**Error Response (401):**
```json
{
    "valid": false,
    "detail": "Token is invalid or expired"
}
```

---

## 5. Get User Profile

**Endpoint:** `GET /api/users/profile/`

**cURL:**
```bash
curl --location 'http://44.200.108.209:8000/api/users/profile/' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

**Success Response (200):**
```json
{
    "id": 1,
    "email": "user@example.com",
    "phone": "+1234567890",
    "country_code": "US",
    "formatted_phone": "US +1234567890",
    "full_name": "John Doe",
    "profile_image": "http://44.200.108.209:8000/media/profile_images/user.jpg",
    "user_type": "advertiser"
}
```

---

## 6. Update User Profile

**Endpoint:** `PATCH /api/users/profile/` or `PUT /api/users/profile/`

**cURL (PATCH):**
```bash
curl --location --request PATCH 'http://44.200.108.209:8000/api/users/profile/' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
--header 'Content-Type: application/json' \
--data-raw '{
    "full_name": "Jane Smith",
    "phone": "+9876543210",
    "country_code": "GB"
}'
```

**Success Response (200):**
```json
{
    "id": 1,
    "email": "user@example.com",
    "phone": "+9876543210",
    "country_code": "GB",
    "formatted_phone": "GB +9876543210",
    "full_name": "Jane Smith",
    "user_type": "advertiser"
}
```

---

## 7. Google Login

**Endpoint:** `POST /api/users/google-login/`

**cURL:**
```bash
curl --location 'http://44.200.108.209:8000/api/users/google-login/' \
--header 'Content-Type: application/json' \
--data-raw '{
    "access_token": "google_access_token_here"
}'
```

**Success Response (200):**
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": 1,
        "email": "user@gmail.com",
        "user_type": "advertiser"
    }
}
```

---

## 8. Upload Profile Image

**Endpoint:** `POST /api/users/upload-profile-image/`

**cURL:**
```bash
curl --location 'http://44.200.108.209:8000/api/users/upload-profile-image/' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
--form 'profile_image=@"/path/to/image.jpg"'
```

**Success Response (200):**
```json
{
    "profile_image": "http://44.200.108.209:8000/media/profile_images/user.jpg",
    "message": "Profile image uploaded successfully"
}
```

---

## 9. Get Country Codes

**Endpoint:** `GET /api/users/country-codes/`

**cURL:**
```bash
curl --location 'http://44.200.108.209:8000/api/users/country-codes/'
```

**Success Response (200):**
```json
[
    {
        "code": "US",
        "name": "United States",
        "dial_code": "+1"
    },
    {
        "code": "GB",
        "name": "United Kingdom",
        "dial_code": "+44"
    },
    {
        "code": "IN",
        "name": "India",
        "dial_code": "+91"
    }
]
```

---

## 📝 Notes

- **Base URL:** `http://44.200.108.209:8000`
- **Email Only:** All endpoints use email (no username field)
- **User Type (REQUIRED):** Must be provided in signup - choose one:
  - `"advertiser"` - For users who want to advertise on billboards
  - `"media_owner"` - For users who own billboards/media spaces
- **Authentication:** Protected endpoints require `Authorization: Bearer <access_token>` header
- **Token Expiry:** Access tokens expire; use refresh token endpoint to get new access token
- **Required Fields in Signup:** 
  - `email` (required)
  - `password` (required)
  - `full_name` (required)
  - `phone` (required) - Must be in international format with country dial code included
    - US/Canada: `+1` + 10 digits (e.g., `+12345678901`)
    - UK: `+44` + 10-11 digits (e.g., `+441234567890`)
    - India: `+91` + 10 digits (e.g., `+911234567890`)
  - `country_code` (required) - ISO 3166-1 alpha-2 code (e.g., US, GB)
  - `user_type` (required) - Must be "advertiser" or "media_owner"

---

## 🔑 User Type Values

- `"advertiser"` - For users who want to advertise
- `"media_owner"` - For users who own billboards/media spaces

---

## ⚠️ Common Error Responses

**401 Unauthorized:**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

**400 Bad Request:**
```json
{
    "email": ["This field is required."],
    "password": ["This field is required."]
}
```

**500 Internal Server Error:**
```json
{
    "detail": "A server error occurred."
}
```
