# 📚 Swagger API Documentation Guide

## ✅ Swagger/OpenAPI Documentation Setup Complete!

Your Django REST Framework API now has interactive API documentation using Swagger UI and ReDoc.

---

## 🔗 Access URLs

Once your server is running, access the documentation at:

### **Swagger UI** (Interactive)
- **Primary URL**: `http://localhost:8000/swagger/`
- **Alternative URL**: `http://localhost:8000/api/docs/`

### **ReDoc** (Alternative Documentation)
- **URL**: `http://localhost:8000/redoc/`

### **OpenAPI Schema** (JSON/YAML)
- **JSON**: `http://localhost:8000/swagger.json`
- **YAML**: `http://localhost:8000/swagger.yaml`

---

## 🚀 Features

### ✅ What's Included

1. **Interactive API Testing**
   - Test all endpoints directly from the browser
   - No need for Postman or curl
   - See request/response examples

2. **JWT Authentication Support**
   - Click "Authorize" button in Swagger UI
   - Enter: `Bearer YOUR_JWT_TOKEN`
   - All authenticated endpoints will use this token

3. **Complete API Documentation**
   - All endpoints automatically documented
   - Request/response schemas
   - Parameter descriptions
   - Authentication requirements

4. **Multiple Documentation Formats**
   - Swagger UI (interactive)
   - ReDoc (clean, readable)
   - OpenAPI JSON/YAML (for code generation)

---

## 🔐 Using Authentication in Swagger

1. **Get Your JWT Token**
   - Login via `/api/users/login/` endpoint
   - Copy the `access` token from response

2. **Authorize in Swagger**
   - Click the **"Authorize"** button (lock icon) at the top
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Click **"Authorize"**
   - Click **"Close"**

3. **Test Authenticated Endpoints**
   - All protected endpoints will now use your token
   - You can test them directly in Swagger UI

---

## 📝 Example: Testing an Endpoint

### 1. View All Billboards
- Go to `GET /api/billboards/`
- Click **"Try it out"**
- Add query parameters (optional):
  - `ne_lat`: 31.5497
  - `ne_lng`: 74.3436
  - `sw_lat`: 31.4500
  - `sw_lng`: 74.2500
  - `zoom`: 8
  - `cluster`: true
- Click **"Execute"**
- See the response below

### 2. Create a Billboard (Authenticated)
- First, authorize with your JWT token
- Go to `POST /api/billboards/`
- Click **"Try it out"**
- Fill in the request body
- Click **"Execute"**

---

## 🎨 Customization

### Update API Info

Edit `core/urls.py` to customize:

```python
schema_view = get_schema_view(
    openapi.Info(
        title="ReachToLet API",  # Change title
        default_version='v1',
        description="Your custom description",  # Update description
        contact=openapi.Contact(email="your@email.com"),  # Your email
        license=openapi.License(name="Your License"),  # Your license
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
```

### Update Swagger Settings

Edit `core/settings.py` to customize Swagger behavior:

```python
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        }
    },
    # ... other settings
}
```

---

## 📋 Available Endpoints

The documentation automatically includes:

### **Billboards**
- `GET /api/billboards/` - List all billboards
- `POST /api/billboards/` - Create billboard
- `GET /api/billboards/{id}/` - Get billboard details
- `POST /api/billboards/{id}/track-view/` - Track view
- `POST /api/billboards/{id}/track-lead/` - Track lead
- And more...

### **Users**
- `POST /api/users/register/` - Register user
- `POST /api/users/login/` - Login
- `GET /api/users/profile/` - Get profile
- And more...

### **Notifications**
- `POST /api/notifications/device-token/register/` - Register device token
- `GET /api/notifications/` - Get notifications
- And more...

### **Admin Panel**
- `GET /api/admin-panel/pending/` - Get pending billboards
- `POST /api/billboards/{id}/approve/` - Approve billboard
- `POST /api/billboards/{id}/reject/` - Reject billboard
- And more...

---

## 🛠️ Troubleshooting

### Issue: Swagger page not loading

**Solution:**
1. Make sure server is running: `python manage.py runserver 0.0.0.0:8000`
2. Check that `drf_yasg` is in `INSTALLED_APPS`
3. Verify URLs are correctly configured in `core/urls.py`

### Issue: Authentication not working

**Solution:**
1. Make sure you're using the correct format: `Bearer YOUR_TOKEN`
2. Token should be the `access` token from login response
3. Check that token hasn't expired

### Issue: Some endpoints not showing

**Solution:**
1. Check that views have proper serializer classes
2. Verify URL patterns are included in main `urls.py`
3. Some function-based views may need `@swagger_auto_schema` decorator

---

## 📖 Adding Custom Documentation

### For Function-Based Views

```python
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='post',
    operation_description="Track a view for a billboard",
    responses={
        200: openapi.Response('Success', schema=YourSerializer),
        404: 'Billboard not found'
    }
)
@api_view(['POST'])
def track_billboard_view(request, billboard_id):
    # Your view code
    pass
```

### For Class-Based Views

```python
from drf_yasg.utils import swagger_auto_schema

class MyView(generics.ListAPIView):
    @swagger_auto_schema(
        operation_description="List all items",
        responses={200: YourSerializer(many=True)}
    )
    def get(self, request):
        # Your code
        pass
```

---

## ✅ Summary

- ✅ Swagger UI: `http://localhost:8000/swagger/`
- ✅ ReDoc: `http://localhost:8000/redoc/`
- ✅ JWT Authentication: Click "Authorize" button
- ✅ Interactive Testing: Test endpoints directly
- ✅ Auto-Generated: All endpoints documented automatically

**Your API documentation is ready!** 🎉

