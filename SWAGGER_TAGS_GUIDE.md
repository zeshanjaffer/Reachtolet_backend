# 🏷️ Swagger API Grouping Guide

## ✅ API Grouping Complete!

Your Swagger documentation is now organized into logical groups using tags. All endpoints are categorized for easy navigation.

---

## 📋 Available API Groups

### 1. **Billboards** 🏢
All billboard-related endpoints:
- List/Create billboards
- Get billboard details
- Update/Delete billboard
- Get my billboards
- Upload billboard images

### 2. **Wishlist** ❤️
Wishlist management:
- Get my wishlist
- Add to wishlist
- Remove from wishlist
- Toggle wishlist status

### 3. **Analytics & Tracking** 📊
View and lead tracking:
- Track billboard view
- Track billboard lead

### 4. **Users & Authentication** 👤
User management and authentication:
- Register new user
- Login (JWT)
- Get/Update profile
- Validate token
- Google login
- Get country codes

### 5. **Notifications** 🔔
Push notification management:
- Register device token
- Get my notifications
- Mark notification as opened
- Mark all as opened
- Notification preferences

### 6. **Admin - Billboard Approval** ✅
Admin-only billboard approval:
- Get pending billboards
- Approve billboard
- Reject billboard

### 7. **Admin - Notifications** 📢
Admin notification management:
- Send custom notification
- Notification statistics
- Campaign management

---

## 🎯 How Tags Work in Swagger

### In Swagger UI

1. **Grouped by Tags**: Endpoints are automatically grouped by their tags
2. **Collapsible Sections**: Each tag group can be expanded/collapsed
3. **Easy Navigation**: Find endpoints quickly by category
4. **Filter by Tag**: Click on a tag to filter endpoints

### Tag Structure

```python
@swagger_auto_schema(
    operation_summary="Short description",
    tags=['Tag Name'],  # This groups the endpoint
    # ... other parameters
)
```

---

## 📝 Example: Viewing Grouped APIs

### In Swagger UI (`http://localhost:8000/swagger/`)

You'll see:

```
📁 Billboards
  ├─ GET /api/billboards/ - List all billboards
  ├─ POST /api/billboards/ - Create billboard
  ├─ GET /api/billboards/{id}/ - Get billboard details
  └─ ...

📁 Wishlist
  ├─ GET /api/billboards/wishlist/ - Get my wishlist
  ├─ POST /api/billboards/wishlist/ - Add to wishlist
  └─ ...

📁 Analytics & Tracking
  ├─ POST /api/billboards/{id}/track-view/ - Track view
  └─ POST /api/billboards/{id}/track-lead/ - Track lead

📁 Users & Authentication
  ├─ POST /api/users/register/ - Register user
  ├─ POST /api/users/login/ - Login
  └─ ...

📁 Notifications
  ├─ POST /api/notifications/device-token/register/ - Register token
  ├─ GET /api/notifications/notifications/ - Get notifications
  └─ ...

📁 Admin - Billboard Approval
  ├─ GET /api/billboards/pending/ - Get pending
  ├─ POST /api/billboards/{id}/approve/ - Approve
  └─ POST /api/billboards/{id}/reject/ - Reject
```

---

## 🔧 Adding Tags to New Endpoints

### For Function-Based Views

```python
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='post',
    operation_summary="My endpoint",
    tags=['My Tag'],  # Add your tag here
    responses={200: 'Success'}
)
@api_view(['POST'])
def my_endpoint(request):
    # Your code
    pass
```

### For Class-Based Views

```python
from drf_yasg.utils import swagger_auto_schema

class MyView(generics.ListAPIView):
    @swagger_auto_schema(
        operation_summary="List items",
        tags=['My Tag'],  # Add your tag here
        responses={200: MySerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
```

---

## 🎨 Customizing Tags

### Change Tag Names

Edit the `tags` parameter in `@swagger_auto_schema`:

```python
tags=['Billboards']  # Current
tags=['Advertising Spaces']  # New name
```

### Add Multiple Tags

```python
tags=['Billboards', 'Public']  # Endpoint appears in both groups
```

### Tag Order

Tags are automatically sorted alphabetically in Swagger UI. To control order, use consistent naming:
- Use prefixes: `Admin - ...`, `User - ...`
- Use numbers: `1. Billboards`, `2. Users`

---

## 📊 Tag Statistics

Current tag distribution:
- **Billboards**: ~8 endpoints
- **Wishlist**: ~3 endpoints
- **Analytics & Tracking**: ~2 endpoints
- **Users & Authentication**: ~6 endpoints
- **Notifications**: ~5 endpoints
- **Admin - Billboard Approval**: ~3 endpoints
- **Admin - Notifications**: ~2 endpoints

---

## ✅ Benefits of Tagging

1. **Better Organization**: Endpoints grouped logically
2. **Easier Navigation**: Find endpoints quickly
3. **Clearer Documentation**: Related endpoints together
4. **Better UX**: Users can focus on specific areas
5. **Scalability**: Easy to add new endpoints to existing groups

---

## 🚀 Next Steps

1. **Start Server**: `python manage.py runserver 0.0.0.0:8000`
2. **Open Swagger**: `http://localhost:8000/swagger/`
3. **Explore Groups**: Click on different tag groups
4. **Test Endpoints**: Use the interactive testing feature

Your API documentation is now beautifully organized! 🎉

