# Admin Panel Frontend Integration Guide

## Overview
This guide explains how to integrate the billboard approval workflow into the admin panel frontend. The backend APIs are already implemented and ready to use.

## 🎯 **Workflow Summary**
1. **User uploads billboard** → Status: `pending` (not visible on map)
2. **Admin reviews billboard** → Can approve or reject
3. **If approved** → Status: `approved` (visible on map for end users)
4. **If rejected** → Status: `rejected` (hidden from map, user can see rejection reason)

---

## 📋 **API Endpoints Available**

### **Get Pending Billboards (Admin Only)**
```javascript
GET /api/billboards/pending/
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "city": "Karachi",
      "description": "Premium location billboard",
      "approval_status": "pending",
      "approval_status_display": "Pending",
      "user_name": "John Doe",
      "created_at": "2025-10-26T14:30:00Z",
      "latitude": 24.8607,
      "longitude": 67.0011,
      "images": ["url1", "url2"],
      "company_name": "ABC Corp",
      "price_range": "$1000-2000",
      "ooh_media_type": "Digital Billboard"
    }
  ],
  "count": 1
}
```

### **Approve Billboard (Admin Only)**
```javascript
POST /api/billboards/{id}/approve/
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "Billboard approved successfully",
  "billboard": {
    "id": 1,
    "approval_status": "approved",
    "approved_at": "2025-10-26T15:00:00Z",
    "approved_by_username": "admin"
  }
}
```

### **Reject Billboard (Admin Only)**
```javascript
POST /api/billboards/{id}/reject/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "rejection_reason": "Poor image quality"
}
```

**Response:**
```json
{
  "message": "Billboard rejected successfully",
  "billboard": {
    "id": 1,
    "approval_status": "rejected",
    "rejected_at": "2025-10-26T15:00:00Z",
    "rejected_by_username": "admin",
    "rejection_reason": "Poor image quality"
  }
}
```

---

## 🎨 **Frontend Implementation**

### **1. Pending Requests Page Component**

```jsx
// components/PendingRequests.jsx
import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Modal, Form, Input, message } from 'antd';
import { CheckOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons';

const PendingRequests = () => {
  const [billboards, setBillboards] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedBillboard, setSelectedBillboard] = useState(null);
  const [rejectModalVisible, setRejectModalVisible] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  // Fetch pending billboards
  const fetchPendingBillboards = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/billboards/pending/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setBillboards(data.results);
      } else {
        message.error('Failed to fetch pending billboards');
      }
    } catch (error) {
      message.error('Error fetching pending billboards');
    } finally {
      setLoading(false);
    }
  };

  // Approve billboard
  const handleApprove = async (billboardId) => {
    try {
      const response = await fetch(`/api/billboards/${billboardId}/approve/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        message.success('Billboard approved successfully');
        fetchPendingBillboards(); // Refresh the list
      } else {
        const error = await response.json();
        message.error(error.error || 'Failed to approve billboard');
      }
    } catch (error) {
      message.error('Error approving billboard');
    }
  };

  // Reject billboard
  const handleReject = async (billboardId, reason) => {
    try {
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

      if (response.ok) {
        message.success('Billboard rejected successfully');
        setRejectModalVisible(false);
        setRejectReason('');
        fetchPendingBillboards(); // Refresh the list
      } else {
        const error = await response.json();
        message.error(error.error || 'Failed to reject billboard');
      }
    } catch (error) {
      message.error('Error rejecting billboard');
    }
  };

  // Open reject modal
  const openRejectModal = (billboard) => {
    setSelectedBillboard(billboard);
    setRejectModalVisible(true);
  };

  // Handle reject form submission
  const handleRejectSubmit = () => {
    if (selectedBillboard) {
      handleReject(selectedBillboard.id, rejectReason);
    }
  };

  useEffect(() => {
    fetchPendingBillboards();
  }, []);

  return (
    <div className="pending-requests">
      <h1>Pending Requests</h1>
      
      {/* Summary Cards */}
      <div className="summary-cards">
        <Card>
          <div className="summary-item">
            <ClockOutlined />
            <span>Pending: {billboards.filter(b => b.approval_status === 'pending').length}</span>
          </div>
        </Card>
        <Card>
          <div className="summary-item">
            <EyeOutlined />
            <span>Under Review: {billboards.filter(b => b.approval_status === 'under_review').length}</span>
          </div>
        </Card>
        <Card>
          <div className="summary-item">
            <CheckOutlined />
            <span>Approved: {billboards.filter(b => b.approval_status === 'approved').length}</span>
          </div>
        </Card>
        <Card>
          <div className="summary-item">
            <CloseOutlined />
            <span>Rejected: {billboards.filter(b => b.approval_status === 'rejected').length}</span>
          </div>
        </Card>
      </div>

      {/* Billboard List */}
      <div className="billboard-list">
        {billboards.map(billboard => (
          <Card key={billboard.id} className="billboard-card">
            <div className="billboard-content">
              <div className="billboard-image">
                {billboard.images && billboard.images.length > 0 ? (
                  <img src={billboard.images[0]} alt="Billboard" />
                ) : (
                  <div className="placeholder-image">
                    <span>📌</span>
                  </div>
                )}
              </div>
              
              <div className="billboard-details">
                <h3>{billboard.company_name || 'Unnamed Billboard'}</h3>
                <p>{billboard.description}</p>
                <p><strong>Location:</strong> {billboard.city}, {billboard.address}</p>
                <p><strong>Price:</strong> {billboard.price_range}</p>
                <p><strong>Company:</strong> {billboard.company_name}</p>
                <p><strong>Type:</strong> {billboard.ooh_media_type}, {billboard.display_width}x{billboard.display_height} ft</p>
                <p><strong>Submitted:</strong> {new Date(billboard.created_at).toLocaleString()}</p>
                <p><strong>User:</strong> {billboard.user_name}</p>
                
                <Badge 
                  status={billboard.approval_status === 'pending' ? 'warning' : 'processing'}
                  text={billboard.approval_status_display}
                />
              </div>
              
              <div className="billboard-actions">
                <Button 
                  icon={<EyeOutlined />} 
                  onClick={() => setSelectedBillboard(billboard)}
                >
                  View Details
                </Button>
                
                {billboard.approval_status === 'pending' && (
                  <>
                    <Button 
                      type="primary" 
                      icon={<CheckOutlined />}
                      onClick={() => handleApprove(billboard.id)}
                      style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
                    >
                      Approve
                    </Button>
                    <Button 
                      danger 
                      icon={<CloseOutlined />}
                      onClick={() => openRejectModal(billboard)}
                    >
                      Reject
                    </Button>
                  </>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Reject Modal */}
      <Modal
        title="Reject Billboard"
        open={rejectModalVisible}
        onOk={handleRejectSubmit}
        onCancel={() => {
          setRejectModalVisible(false);
          setRejectReason('');
        }}
        okText="Reject"
        cancelText="Cancel"
      >
        <Form>
          <Form.Item label="Rejection Reason">
            <Input.TextArea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Enter reason for rejection (optional)"
              rows={4}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PendingRequests;
```

### **2. Billboard Details Modal Component**

```jsx
// components/BillboardDetailsModal.jsx
import React from 'react';
import { Modal, Descriptions, Image, Tag } from 'antd';

const BillboardDetailsModal = ({ billboard, visible, onClose }) => {
  if (!billboard) return null;

  return (
    <Modal
      title="Billboard Details"
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
    >
      <Descriptions bordered column={2}>
        <Descriptions.Item label="ID">{billboard.id}</Descriptions.Item>
        <Descriptions.Item label="Status">
          <Tag color={billboard.approval_status === 'pending' ? 'orange' : 'blue'}>
            {billboard.approval_status_display}
          </Tag>
        </Descriptions.Item>
        
        <Descriptions.Item label="City">{billboard.city}</Descriptions.Item>
        <Descriptions.Item label="Company">{billboard.company_name}</Descriptions.Item>
        
        <Descriptions.Item label="Description" span={2}>
          {billboard.description}
        </Descriptions.Item>
        
        <Descriptions.Item label="Location" span={2}>
          {billboard.address}, {billboard.city}
        </Descriptions.Item>
        
        <Descriptions.Item label="Coordinates">
          {billboard.latitude}, {billboard.longitude}
        </Descriptions.Item>
        <Descriptions.Item label="Price Range">{billboard.price_range}</Descriptions.Item>
        
        <Descriptions.Item label="Media Type">{billboard.ooh_media_type}</Descriptions.Item>
        <Descriptions.Item label="Dimensions">
          {billboard.display_width} x {billboard.display_height} ft
        </Descriptions.Item>
        
        <Descriptions.Item label="Contact Phone">{billboard.advertiser_phone}</Descriptions.Item>
        <Descriptions.Item label="WhatsApp">{billboard.advertiser_whatsapp}</Descriptions.Item>
        
        <Descriptions.Item label="Views">{billboard.views}</Descriptions.Item>
        <Descriptions.Item label="Leads">{billboard.leads}</Descriptions.Item>
        
        <Descriptions.Item label="Created At" span={2}>
          {new Date(billboard.created_at).toLocaleString()}
        </Descriptions.Item>
        
        {billboard.approved_at && (
          <Descriptions.Item label="Approved At" span={2}>
            {new Date(billboard.approved_at).toLocaleString()} by {billboard.approved_by_username}
          </Descriptions.Item>
        )}
        
        {billboard.rejected_at && (
          <Descriptions.Item label="Rejected At" span={2}>
            {new Date(billboard.rejected_at).toLocaleString()} by {billboard.rejected_by_username}
            {billboard.rejection_reason && (
              <div>Reason: {billboard.rejection_reason}</div>
            )}
          </Descriptions.Item>
        )}
      </Descriptions>
      
      {billboard.images && billboard.images.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <h4>Images:</h4>
          <Image.PreviewGroup>
            {billboard.images.map((image, index) => (
              <Image
                key={index}
                src={image}
                width={100}
                height={100}
                style={{ margin: 8 }}
              />
            ))}
          </Image.PreviewGroup>
        </div>
      )}
    </Modal>
  );
};

export default BillboardDetailsModal;
```

### **3. Dashboard Stats Integration**

```jsx
// components/DashboardStats.jsx
import React, { useState, useEffect } from 'react';
import { Card, Statistic, Row, Col } from 'antd';
import { ClockOutlined, CheckOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons';

const DashboardStats = () => {
  const [stats, setStats] = useState({
    pending: 0,
    approved: 0,
    rejected: 0,
    total: 0
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      // Fetch pending billboards
      const pendingResponse = await fetch('/api/billboards/pending/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
        }
      });
      
      if (pendingResponse.ok) {
        const pendingData = await pendingResponse.json();
        setStats(prev => ({
          ...prev,
          pending: pendingData.count
        }));
      }
      
      // You can add more API calls here for approved/rejected counts
      // or create a dedicated stats endpoint
      
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  return (
    <Row gutter={16}>
      <Col span={6}>
        <Card>
          <Statistic
            title="Pending Requests"
            value={stats.pending}
            prefix={<ClockOutlined />}
            valueStyle={{ color: '#faad14' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="Under Review"
            value={stats.under_review || 0}
            prefix={<EyeOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="Approved"
            value={stats.approved}
            prefix={<CheckOutlined />}
            valueStyle={{ color: '#52c41a' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="Rejected"
            value={stats.rejected}
            prefix={<CloseOutlined />}
            valueStyle={{ color: '#f5222d' }}
          />
        </Card>
      </Col>
    </Row>
  );
};

export default DashboardStats;
```

---

## 🎨 **CSS Styles**

```css
/* styles/PendingRequests.css */
.pending-requests {
  padding: 24px;
}

.summary-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.summary-cards .ant-card {
  flex: 1;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
}

.billboard-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.billboard-card {
  margin-bottom: 16px;
}

.billboard-content {
  display: flex;
  gap: 16px;
}

.billboard-image {
  width: 120px;
  height: 120px;
  flex-shrink: 0;
}

.billboard-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

.placeholder-image {
  width: 100%;
  height: 100%;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 24px;
}

.billboard-details {
  flex: 1;
}

.billboard-details h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}

.billboard-details p {
  margin: 4px 0;
  color: #666;
}

.billboard-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 120px;
}

.billboard-actions .ant-btn {
  width: 100%;
}
```

---

## 🔧 **Integration Steps**

### **1. Add to Admin Panel Navigation**
```jsx
// Add to your admin panel navigation
{
  key: 'pending-requests',
  icon: <ClockOutlined />,
  label: 'Pending Requests',
  path: '/admin/pending-requests'
}
```

### **2. Add Route**
```jsx
// Add to your router
<Route path="/admin/pending-requests" element={<PendingRequests />} />
```

### **3. Update Dashboard**
```jsx
// Add stats to dashboard
import DashboardStats from './components/DashboardStats';

// In your dashboard component
<DashboardStats />
```

### **4. Add API Service**
```javascript
// services/billboardService.js
export const billboardService = {
  getPendingBillboards: async () => {
    const response = await fetch('/api/billboards/pending/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
      }
    });
    return response.json();
  },
  
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
};
```

---

## 🚀 **Testing the Integration**

### **1. Test Pending Billboards**
```bash
# Check if pending billboards are returned
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     http://localhost:8000/api/billboards/pending/
```

### **2. Test Approval**
```bash
# Approve a billboard
curl -X POST \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/billboards/1/approve/
```

### **3. Test Rejection**
```bash
# Reject a billboard
curl -X POST \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"rejection_reason": "Poor image quality"}' \
     http://localhost:8000/api/billboards/1/reject/
```

---

## 📱 **Mobile Responsive Design**

```css
@media (max-width: 768px) {
  .billboard-content {
    flex-direction: column;
  }
  
  .billboard-image {
    width: 100%;
    height: 200px;
  }
  
  .billboard-actions {
    flex-direction: row;
    min-width: auto;
  }
  
  .summary-cards {
    flex-direction: column;
  }
}
```

---

## 🎯 **Complete Workflow**

1. **User creates billboard** → Status: `pending`
2. **Admin sees in "Pending Requests"** → Can review details
3. **Admin approves** → Status: `approved` → Visible on public map
4. **Admin rejects** → Status: `rejected` → Hidden from map

The backend is ready! Just integrate these frontend components and you'll have a complete billboard approval workflow.
