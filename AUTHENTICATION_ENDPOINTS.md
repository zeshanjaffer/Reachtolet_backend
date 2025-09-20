# 🔐 Authentication Endpoints for React Native App

Your Django backend now has **ALL 3 essential endpoints** for persistent login! 🎯

## ✅ **Complete Endpoint List**

### 1. **Token Validation Endpoint**
```
GET /api/users/validate-token/
```
**Purpose**: Check if the stored access token is still valid  
**Headers**: `Authorization: Bearer <access_token>`  
**Response**: 
- `200 OK` = Token is valid
```json
{
  "valid": true,
  "user_id": 123,
  "email": "user@example.com"
}
```
- `401 Unauthorized` = Token is expired/invalid

### 2. **Token Refresh Endpoint**
```
POST /api/users/token/refresh/
```
**Purpose**: Get a new access token using the refresh token  
**Body**: 
```json
{
  "refresh": "your_refresh_token_here"
}
```
**Response**:
```json
{
  "access": "new_access_token_here"
}
```

### 3. **Login Endpoint**
```
POST /api/users/login/
```
**Purpose**: Initial login to get both tokens  
**Body**:
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```
**Response**:
```json
{
  "access": "access_token_here",
  "refresh": "refresh_token_here"
}
```

### 4. **Register Endpoint** (Bonus!)
```
POST /api/users/register/
```
**Purpose**: Create new user account and automatically log in  
**Body**:
```json
{
  "email": "newuser@example.com",
  "password": "secure_password",
  "name": "John Doe"
}
```
**Response**:
```json
{
  "user": {
    "id": 123,
    "email": "newuser@example.com",
    "name": "John Doe"
  },
  "access": "access_token_here",
  "refresh": "refresh_token_here",
  "message": "User registered successfully"
}
```

## 🚀 **React Native Implementation Flow**

### **App Startup Logic:**
1. **Check for stored tokens** in AsyncStorage
2. **Call `/api/users/validate-token/`** with stored access token
3. **If 200**: User is logged in, proceed to main app
4. **If 401**: Token expired, try refresh with `/api/users/token/refresh/`
5. **If refresh fails**: Redirect to login screen

### **Login Flow:**
1. **User enters credentials**
2. **Call `/api/users/login/`** 
3. **Store both tokens** in AsyncStorage
4. **Proceed to main app**

### **Automatic Token Refresh:**
1. **Before each API call**, check if token is about to expire
2. **If needed**, call `/api/users/token/refresh/`
3. **Update stored access token**
4. **Continue with original API call**

## 🔧 **JWT Token Settings**

Your tokens are configured with:
- **Access Token**: 1 day lifetime
- **Refresh Token**: 7 days lifetime

This means users will stay logged in for up to 7 days without re-entering credentials!

## ✅ **You're All Set!**

With these 4 endpoints, your React Native app will have:
- ✅ **Persistent login** across app restarts
- ✅ **Automatic token refresh** 
- ✅ **Secure authentication**
- ✅ **User registration**
- ✅ **No repeated login prompts**

**That's everything you need for a smooth user experience!** 🎉
