# 🔧 Admin Panel API Endpoints

## ✅ **Renamed Admin APIs with Clear Prefixes**

All admin panel APIs now use the `/api/admin/` prefix to clearly distinguish them from regular user APIs.

### **🔐 Authentication Endpoints**

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/api/users/admin/auth/login/` | POST | Admin login | ✅ Working |
| `/api/users/admin/auth/me/` | GET | Get current admin user | ✅ Working |
| `/api/users/admin/auth/logout/` | POST | Admin logout | ✅ Working |

### **📊 Admin Panel Management Endpoints**

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/api/admin-panel/admin/campaigns/` | GET | List campaigns | ✅ Working |
| `/api/admin-panel/admin/campaigns/create/` | POST | Create campaign | ✅ Working |
| `/api/admin-panel/admin/campaigns/{id}/` | GET/PUT/DELETE | Campaign details | ✅ Working |
| `/api/admin-panel/admin/templates/` | GET | List templates | ✅ Working |
| `/api/admin-panel/admin/templates/{id}/` | GET/PUT/DELETE | Template details | ✅ Working |
| `/api/admin-panel/admin/users/` | GET | List users | ✅ Working |
| `/api/admin-panel/admin/send/` | POST | Send notification | ✅ Working |
| `/api/admin-panel/admin/bulk-action/` | POST | Bulk operations | ✅ Working |
| `/api/admin-panel/admin/stats/` | GET | Get statistics | ✅ Working |
| `/api/admin-panel/admin/campaigns/{id}/analytics/` | GET | Campaign analytics | ✅ Working |

## 🧪 **Test Results**

### **Authentication Test:**
```bash
POST /api/users/admin/auth/login/
{
  "email": "admin@gmail.com",
  "password": "zeshanopn1613m"
}
```
**Response:** ✅ 200 OK with JWT tokens

### **Stats Test:**
```bash
GET /api/admin-panel/admin/stats/
Authorization: Bearer <token>
```
**Response:** ✅ 200 OK with statistics

## 🔄 **API Structure Comparison**

### **Before (Confusing):**
- `/api/users/auth/login/` - Admin login
- `/api/users/auth/me/` - Admin user info
- `/api/admin-panel/stats/` - Admin stats
- `/api/admin-panel/campaigns/` - Admin campaigns

### **After (Clear):**
- `/api/users/admin/auth/login/` - **Admin login**
- `/api/users/admin/auth/me/` - **Admin user info**
- `/api/admin-panel/admin/stats/` - **Admin stats**
- `/api/admin-panel/admin/campaigns/` - **Admin campaigns**

## 🚀 **Benefits of New Structure**

1. **Clear Separation**: Admin APIs are clearly distinguished from user APIs
2. **Easy Identification**: All admin endpoints have `/admin/` prefix
3. **Better Organization**: Logical grouping of admin functionality
4. **No Conflicts**: No confusion between user and admin endpoints
5. **Scalable**: Easy to add more admin features

## 📝 **Frontend Update Required**

Your Next.js frontend needs to be updated to use the new endpoints:

### **Old Endpoints (Update Required):**
```typescript
// ❌ Old endpoints
const API_ENDPOINTS = {
  LOGIN: '/users/auth/login/',
  ME: '/users/auth/me/',
  STATS: '/admin-panel/stats/',
  CAMPAIGNS: '/admin-panel/campaigns/',
};
```

### **New Endpoints (Use These):**
```typescript
// ✅ New endpoints
const API_ENDPOINTS = {
  LOGIN: '/users/admin/auth/login/',
  ME: '/users/admin/auth/me/',
  STATS: '/admin-panel/admin/stats/',
  CAMPAIGNS: '/admin-panel/admin/campaigns/',
};
```

## 🎯 **Quick Test Commands**

```bash
# Test admin login
curl -X POST http://localhost:8000/api/users/admin/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@gmail.com", "password": "zeshanopn1613m"}'

# Test admin stats
curl -X GET http://localhost:8000/api/admin-panel/admin/stats/ \
  -H "Authorization: Bearer <your_token>"
```

All admin panel APIs are now properly organized and working! 🎉
