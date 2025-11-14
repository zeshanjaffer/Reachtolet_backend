# Admin Panel Push Notification Implementation Guide

## 🎯 **Overview**

This guide shows you how to implement push notification sending functionality in your admin panel frontend.

---

## 🔌 **API Endpoint**

### **Primary Endpoint (Recommended):**

```
POST http://44.200.108.209:8000/api/notifications/send/
```

**Permission:** Admin Only (`IsAdminUser`)

**Base URL:** `http://44.200.108.209:8000`

---

## 📋 **Request Format**

### **Headers:**
```
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

### **Request Body:**

#### **Option 1: Send to All Users**
```json
{
  "notification_type": "system_message",
  "title": "Your notification title",
  "body": "Your notification message",
  "all_users": true,
  "data": {
    "custom": "data",
    "action": "navigate_to_screen"
  }
}
```

#### **Option 2: Send to Specific Users**
```json
{
  "notification_type": "system_message",
  "title": "Your notification title",
  "body": "Your notification message",
  "user_ids": [1, 2, 3, 4, 5],
  "data": {
    "custom": "data"
  }
}
```

---

## 📝 **Available Notification Types**

```typescript
type NotificationType = 
  | "new_lead"              // New Lead
  | "new_view"              // New View
  | "wishlist_added"        // Added to Wishlist
  | "billboard_activated"    // Billboard Activated
  | "billboard_deactivated" // Billboard Deactivated
  | "billboard_approved"    // Billboard Approved
  | "billboard_rejected"    // Billboard Rejected
  | "price_update"          // Price Update
  | "system_message"        // System Message (Recommended for admin)
  | "welcome"              // Welcome Message
```

**Recommended:** Use `"system_message"` for admin-sent notifications.

---

## ✅ **Response Format**

### **Success Response (201 Created):**
```json
{
  "message": "Successfully sent 15 notifications",
  "notifications_sent": 15
}
```

### **Error Responses:**

#### **400 Bad Request:**
```json
{
  "error": "Either user_ids or all_users must be specified"
}
```

#### **401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### **403 Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### **500 Internal Server Error:**
```json
{
  "error": "Failed to send notifications"
}
```

---

## 💻 **Frontend Implementation**

### **1. TypeScript/React Implementation**

#### **Create API Service:**

```typescript
// services/notificationService.ts
import axios from 'axios';

const API_BASE_URL = 'http://44.200.108.209:8000';

export interface SendNotificationRequest {
  notification_type: string;
  title: string;
  body: string;
  all_users?: boolean;
  user_ids?: number[];
  data?: Record<string, any>;
}

export interface SendNotificationResponse {
  message: string;
  notifications_sent: number;
}

export const sendNotification = async (
  token: string,
  request: SendNotificationRequest
): Promise<SendNotificationResponse> => {
  const response = await axios.post<SendNotificationResponse>(
    `${API_BASE_URL}/api/notifications/send/`,
    request,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );
  return response.data;
};
```

#### **Create React Component:**

```typescript
// components/SendNotificationForm.tsx
import React, { useState } from 'react';
import { Button, Form, Input, Select, Switch, message, Card, Space } from 'antd';
import { sendNotification } from '../services/notificationService';
import { useAuth } from '../contexts/AuthContext';

const { TextArea } = Input;
const { Option } = Select;

const NOTIFICATION_TYPES = [
  { value: 'system_message', label: 'System Message' },
  { value: 'welcome', label: 'Welcome Message' },
  { value: 'price_update', label: 'Price Update' },
];

export const SendNotificationForm: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [sendToAll, setSendToAll] = useState(true);
  const { token } = useAuth();

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      const request = {
        notification_type: values.notification_type,
        title: values.title,
        body: values.body,
        all_users: sendToAll,
        user_ids: sendToAll ? undefined : values.user_ids,
        data: values.data ? JSON.parse(values.data) : {},
      };

      const response = await sendNotification(token!, request);
      
      message.success(
        `Successfully sent ${response.notifications_sent} notifications!`
      );
      form.resetFields();
    } catch (error: any) {
      message.error(
        error.response?.data?.error || 
        error.response?.data?.detail || 
        'Failed to send notifications'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Send Push Notification" style={{ maxWidth: 800, margin: '0 auto' }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          notification_type: 'system_message',
        }}
      >
        <Form.Item
          name="notification_type"
          label="Notification Type"
          rules={[{ required: true, message: 'Please select notification type' }]}
        >
          <Select placeholder="Select notification type">
            {NOTIFICATION_TYPES.map((type) => (
              <Option key={type.value} value={type.value}>
                {type.label}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="title"
          label="Title"
          rules={[{ required: true, message: 'Please enter notification title' }]}
        >
          <Input 
            placeholder="Enter notification title" 
            maxLength={255}
          />
        </Form.Item>

        <Form.Item
          name="body"
          label="Message"
          rules={[{ required: true, message: 'Please enter notification message' }]}
        >
          <TextArea
            rows={4}
            placeholder="Enter notification message"
            showCount
            maxLength={500}
          />
        </Form.Item>

        <Form.Item label="Send To">
          <Space>
            <Switch
              checked={sendToAll}
              onChange={setSendToAll}
              checkedChildren="All Users"
              unCheckedChildren="Specific Users"
            />
            {sendToAll ? (
              <span style={{ color: '#52c41a' }}>
                Will send to all active users with registered device tokens
              </span>
            ) : (
              <span style={{ color: '#1890ff' }}>
                Select specific users below
              </span>
            )}
          </Space>
        </Form.Item>

        {!sendToAll && (
          <Form.Item
            name="user_ids"
            label="User IDs"
            rules={[{ required: true, message: 'Please select at least one user' }]}
          >
            <Select
              mode="multiple"
              placeholder="Select users"
              style={{ width: '100%' }}
            >
              {/* Populate with users from API */}
            </Select>
          </Form.Item>
        )}

        <Form.Item
          name="data"
          label="Additional Data (JSON, optional)"
          help="Optional JSON data to send with notification"
        >
          <TextArea
            rows={3}
            placeholder='{"key": "value"}'
          />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            Send Notification
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};
```

---

### **2. JavaScript/Vanilla Implementation**

```javascript
// notificationService.js
const API_BASE_URL = 'http://44.200.108.209:8000';

async function sendNotification(adminToken, notificationData) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/notifications/send/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${adminToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(notificationData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || error.detail || 'Failed to send notification');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error sending notification:', error);
    throw error;
  }
}

// Usage
const notificationData = {
  notification_type: 'system_message',
  title: 'Test Notification',
  body: 'This is a test notification from admin panel',
  all_users: true,
  data: {
    action: 'test',
  },
};

sendNotification(adminToken, notificationData)
  .then((response) => {
    console.log('Success:', response.message);
    console.log('Notifications sent:', response.notifications_sent);
  })
  .catch((error) => {
    console.error('Error:', error.message);
  });
```

---

### **3. Next.js Implementation**

```typescript
// app/api/notifications/send/route.ts (Next.js App Router)
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const adminToken = request.headers.get('Authorization')?.replace('Bearer ', '');

    if (!adminToken) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const response = await fetch('http://44.200.108.209:8000/api/notifications/send/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${adminToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

---

## 🎨 **UI Examples**

### **Simple Form (Ant Design):**

```tsx
import { Form, Input, Button, Switch, message } from 'antd';

const SendNotification = () => {
  const [form] = Form.useForm();
  const [sendToAll, setSendToAll] = useState(true);

  const onFinish = async (values: any) => {
    try {
      const response = await fetch('http://44.200.108.209:8000/api/notifications/send/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          notification_type: 'system_message',
          title: values.title,
          body: values.body,
          all_users: sendToAll,
        }),
      });

      const data = await response.json();
      
      if (response.ok) {
        message.success(`Sent ${data.notifications_sent} notifications!`);
        form.resetFields();
      } else {
        message.error(data.error || 'Failed to send');
      }
    } catch (error) {
      message.error('Network error');
    }
  };

  return (
    <Form form={form} onFinish={onFinish} layout="vertical">
      <Form.Item name="title" label="Title" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="body" label="Message" rules={[{ required: true }]}>
        <Input.TextArea rows={4} />
      </Form.Item>
      <Form.Item>
        <Switch
          checked={sendToAll}
          onChange={setSendToAll}
          checkedChildren="All Users"
        />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit">
          Send Notification
        </Button>
      </Form.Item>
    </Form>
  );
};
```

---

## 🧪 **Testing**

### **Test with cURL:**

```bash
curl -X POST http://44.200.108.209:8000/api/notifications/send/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "system_message",
    "title": "Test Notification",
    "body": "This is a test from admin panel",
    "all_users": true
  }'
```

### **Test with Postman:**

1. **Method:** POST
2. **URL:** `http://44.200.108.209:8000/api/notifications/send/`
3. **Headers:**
   - `Authorization: Bearer YOUR_ADMIN_TOKEN`
   - `Content-Type: application/json`
4. **Body (JSON):**
```json
{
  "notification_type": "system_message",
  "title": "Test Notification",
  "body": "This is a test notification",
  "all_users": true
}
```

---

## 📊 **Get User List (For User Selection)**

If you want to send to specific users, you'll need to fetch the user list:

### **Endpoint:**
```
GET http://44.200.108.209:8000/api/admin-panel/admin/users/
Authorization: Bearer <admin_token>
```

### **Response:**
```json
{
  "results": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "is_active": true
    },
    ...
  ]
}
```

---

## ⚠️ **Important Notes**

1. **Admin Only:** This endpoint requires admin privileges
2. **Device Tokens:** Only users with registered device tokens will receive notifications
3. **Active Users:** Only active users receive notifications
4. **User Preferences:** Users who disabled push notifications won't receive them
5. **Quiet Hours:** Notifications respect user's quiet hours settings

---

## 🔍 **Troubleshooting**

### **Issue: 403 Forbidden**
- **Solution:** Make sure you're logged in as an admin user

### **Issue: 0 notifications sent**
- **Solution:** 
  - Check if users have registered device tokens
  - Verify users are active
  - Check user notification preferences

### **Issue: Some users not receiving**
- **Solution:**
  - Check if user has device token registered
  - Verify user hasn't disabled notifications
  - Check if quiet hours are active

---

## 📝 **Complete Example (React + TypeScript)**

```typescript
// Complete working example
import React, { useState } from 'react';
import { Button, Form, Input, Switch, message } from 'antd';

interface NotificationFormData {
  title: string;
  body: string;
  all_users: boolean;
}

const AdminNotificationPanel: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const adminToken = localStorage.getItem('admin_token'); // Get from your auth system

  const handleSend = async (values: NotificationFormData) => {
    setLoading(true);
    try {
      const response = await fetch(
        'http://44.200.108.209:8000/api/notifications/send/',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${adminToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            notification_type: 'system_message',
            title: values.title,
            body: values.body,
            all_users: values.all_users,
          }),
        }
      );

      const data = await response.json();

      if (response.ok) {
        message.success(
          `✅ Successfully sent ${data.notifications_sent} notifications!`
        );
      } else {
        message.error(data.error || 'Failed to send notifications');
      }
    } catch (error) {
      message.error('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '600px' }}>
      <h2>Send Push Notification</h2>
      <Form onFinish={handleSend} layout="vertical">
        <Form.Item
          name="title"
          label="Title"
          rules={[{ required: true }]}
        >
          <Input placeholder="Notification title" />
        </Form.Item>
        <Form.Item
          name="body"
          label="Message"
          rules={[{ required: true }]}
        >
          <Input.TextArea rows={4} placeholder="Notification message" />
        </Form.Item>
        <Form.Item name="all_users" valuePropName="checked" initialValue={true}>
          <Switch checkedChildren="All Users" unCheckedChildren="Specific Users" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            Send Notification
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default AdminNotificationPanel;
```

---

## 🎯 **Quick Start Checklist**

- [ ] Get admin authentication token
- [ ] Create API service function
- [ ] Create notification form component
- [ ] Add form validation
- [ ] Handle success/error responses
- [ ] Test with real device tokens
- [ ] Add user selection (optional)
- [ ] Add notification preview (optional)

---

**Your admin panel is ready to send push notifications!** 🚀

