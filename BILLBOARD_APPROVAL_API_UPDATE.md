# Billboard Approval API Update - App Side Implementation

## 🔄 **Breaking Change: Unified Approval/Rejection API**

The separate `/approve/` and `/reject/` endpoints have been **merged into a single unified endpoint**.

---

## 📍 **New Unified Endpoint**

**Endpoint:** `POST /api/billboards/{billboard_id}/approval-status/`

**Old Endpoints (DEPRECATED - Remove these):**
- ❌ `POST /api/billboards/{id}/approve/`
- ❌ `POST /api/billboards/{id}/reject/`

---

## 📝 **Request Format**

### **To Approve a Billboard:**
```javascript
POST /api/billboards/{billboard_id}/approval-status/
Headers: {
  "Authorization": "Bearer <admin_token>",
  "Content-Type": "application/json"
}
Body: {
  "action": "approve"
}
```

### **To Reject a Billboard:**
```javascript
POST /api/billboards/{billboard_id}/approval-status/
Headers: {
  "Authorization": "Bearer <admin_token>",
  "Content-Type": "application/json"
}
Body: {
  "action": "reject",
  "rejection_reason": "Optional reason for rejection"
}
```

---

## ✅ **Response Format**

**Success Response (200 OK):**
```json
{
  "message": "Billboard approved successfully",  // or "Billboard rejected successfully"
  "billboard": {
    "id": 1,
    "approval_status": "approved",  // or "rejected"
    "approved_at": "2025-01-26T15:00:00Z",
    "rejected_at": null,
    "rejection_reason": null
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid action or billboard already processed
- `404 Not Found`: Billboard not found
- `403 Forbidden`: Admin access required

---

## 💻 **Implementation Examples**

### **React/JavaScript:**
```javascript
// Unified function for approve/reject
const updateBillboardStatus = async (billboardId, action, rejectionReason = '') => {
  const response = await fetch(
    `/api/billboards/${billboardId}/approval-status/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        action: action, // "approve" or "reject"
        rejection_reason: rejectionReason
      })
    }
  );
  
  return await response.json();
};

// Usage:
// Approve
await updateBillboardStatus(123, 'approve');

// Reject
await updateBillboardStatus(123, 'reject', 'Poor image quality');
```

### **React Native/Expo:**
```javascript
import axios from 'axios';

const updateBillboardStatus = async (billboardId, action, rejectionReason = '') => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/billboards/${billboardId}/approval-status/`,
      {
        action: action,
        rejection_reason: rejectionReason
      },
      {
        headers: {
          'Authorization': `Bearer ${await getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  } catch (error) {
    throw error.response?.data || error;
  }
};
```

### **TypeScript Interface:**
```typescript
interface ApprovalRequest {
  action: 'approve' | 'reject';
  rejection_reason?: string;
}

interface ApprovalResponse {
  message: string;
  billboard: {
    id: number;
    approval_status: 'approved' | 'rejected' | 'pending';
    approved_at?: string;
    rejected_at?: string;
    rejection_reason?: string;
  };
}
```

---

## 🔧 **Migration Steps**

1. **Replace API calls:**
   - Find all instances of `/approve/` and `/reject/` endpoints
   - Replace with single `/approval-status/` endpoint
   - Add `action` parameter to request body

2. **Update service functions:**
   ```javascript
   // OLD (Remove)
   approveBillboard(id) {
     POST `/api/billboards/${id}/approve/`
   }
   rejectBillboard(id, reason) {
     POST `/api/billboards/${id}/reject/` with { rejection_reason: reason }
   }
   
   // NEW (Use this)
   updateBillboardStatus(id, action, reason = '') {
     POST `/api/billboards/${id}/approval-status/` 
     with { action: action, rejection_reason: reason }
   }
   ```

3. **Update UI handlers:**
   ```javascript
   // OLD
   handleApprove(id) {
     await approveBillboard(id);
   }
   handleReject(id, reason) {
     await rejectBillboard(id, reason);
   }
   
   // NEW
   handleApprove(id) {
     await updateBillboardStatus(id, 'approve');
   }
   handleReject(id, reason) {
     await updateBillboardStatus(id, 'reject', reason);
   }
   ```

---

## ⚠️ **Important Notes**

- **Action values are case-insensitive** but use lowercase: `"approve"` or `"reject"`
- **Only pending billboards** can be approved/rejected
- **Rejection reason is optional** but recommended for better UX
- **Admin authentication required** - same as before

---

## 🧪 **Testing**

```bash
# Test Approve
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "approve"}' \
  http://localhost:8000/api/billboards/1/approval-status/

# Test Reject
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "reject", "rejection_reason": "Test rejection"}' \
  http://localhost:8000/api/billboards/1/approval-status/
```

---

**Last Updated:** After unified approval/rejection API implementation

