# Admin Panel API Update - Quick Migration Guide

## 🔄 **API Endpoint Change**

**OLD Endpoints (Remove these):**
```javascript
POST /api/billboards/{id}/approve/
POST /api/billboards/{id}/reject/
```

**NEW Unified Endpoint:**
```javascript
POST /api/billboards/{id}/approval-status/
```

---

## 📝 **Update Instructions**

### **Step 1: Update Service Functions**

**Find this code:**
```javascript
// services/billboardService.js
approveBillboard: async (id) => {
  const response = await fetch(`/api/billboards/${id}/approve/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
},

rejectBillboard: async (id, reason) => {
  const response = await fetch(`/api/billboards/${id}/reject/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ rejection_reason: reason })
  });
  return response.json();
}
```

**Replace with:**
```javascript
// services/billboardService.js
updateBillboardStatus: async (id, action, reason = '') => {
  const response = await fetch(`/api/billboards/${id}/approval-status/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: action, // "approve" or "reject"
      rejection_reason: reason
    })
  });
  return response.json();
}
```

---

### **Step 2: Update Component Handlers**

**Find this code:**
```javascript
// components/PendingRequests.jsx

// Approve billboard
const handleApprove = async (billboardId) => {
  const response = await fetch(`/api/billboards/${billboardId}/approve/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
      'Content-Type': 'application/json'
    }
  });
  // ... rest of code
};

// Reject billboard
const handleReject = async (billboardId, reason) => {
  const response = await fetch(`/api/billboards/${billboardId}/reject/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      rejection_reason: reason
    })
  });
  // ... rest of code
};
```

**Replace with:**
```javascript
// components/PendingRequests.jsx

// Approve billboard
const handleApprove = async (billboardId) => {
  const response = await fetch(`/api/billboards/${billboardId}/approval-status/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: 'approve'
    })
  });
  // ... rest of code
};

// Reject billboard
const handleReject = async (billboardId, reason) => {
  const response = await fetch(`/api/billboards/${billboardId}/approval-status/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: 'reject',
      rejection_reason: reason
    })
  });
  // ... rest of code
};
```

---

### **Step 3: If Using Service Functions**

**Update function calls:**
```javascript
// OLD
await approveBillboard(billboardId);
await rejectBillboard(billboardId, reason);

// NEW
await updateBillboardStatus(billboardId, 'approve');
await updateBillboardStatus(billboardId, 'reject', reason);
```

---

## ✅ **Quick Checklist

- [ ] Replace `/approve/` endpoint with `/approval-status/`
- [ ] Replace `/reject/` endpoint with `/approval-status/`
- [ ] Add `action: 'approve'` to approve requests
- [ ] Add `action: 'reject'` to reject requests
- [ ] Keep `rejection_reason` in request body for reject
- [ ] Test approve functionality
- [ ] Test reject functionality

---

## 📋 **Request Body Format**

**Approve:**
```json
{
  "action": "approve"
}
```

**Reject:**
```json
{
  "action": "reject",
  "rejection_reason": "Your rejection reason here"
}
```

---

## 🎯 **Summary**

1. Change endpoint URL from `/approve/` or `/reject/` to `/approval-status/`
2. Add `action` field to request body: `"approve"` or `"reject"`
3. Keep `rejection_reason` for reject action
4. Everything else stays the same (headers, auth, response handling)

