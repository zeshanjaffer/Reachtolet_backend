# 📧 Flutter Migration Guide: Email-Only Authentication

## 🎯 Overview

The backend has been updated to **remove username completely** and use **email only** for authentication. This guide will help you update your Flutter app to align with the new API.

---

## ✅ Backend Changes Made

1. ✅ **User Model**: Email is now the `USERNAME_FIELD` (replaces username)
2. ✅ **Login API**: Now accepts `email` field only (no username)
3. ✅ **Signup API**: Removed `username` field requirement
4. ✅ **All Serializers**: Removed username from all responses
5. ✅ **Migrations**: Created migration to update database

---

## 🔄 Flutter App Changes Required

### 1. **Update Signup API Call**

**Before:**
```dart
// OLD - Don't use this anymore
{
  "username": "user@example.com",
  "email": "user@example.com",
  "password": "password123",
  "user_type": "advertiser"
}
```

**After:**
```dart
// NEW - Only email, no username
{
  "email": "user@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "advertiser"
}
```

**Update your `RegisterRequested` event:**
```dart
// In your auth_bloc.dart or wherever you handle signup
class RegisterRequested extends AuthEvent {
  final String email;
  final String password;
  final String? firstName;
  final String? lastName;
  final String? phone;
  final String? countryCode;
  final String userType;

  RegisterRequested({
    required this.email,
    required this.password,
    this.firstName,
    this.lastName,
    this.phone,
    this.countryCode,
    required this.userType,
  });
}
```

**Update your signup API call:**
```dart
// Remove username from the request body
final response = await dio.post(
  '/api/users/register/',
  data: {
    'email': email,
    'password': password,
    'first_name': firstName,
    'last_name': lastName,
    'phone': phone,
    'country_code': countryCode,
    'user_type': userType,
  },
);
```

---

### 2. **Update Login API Call**

**Before:**
```dart
// OLD - Don't use this anymore
{
  "username": "user@example.com",  // ❌ Remove this
  "password": "password123"
}
```

**After:**
```dart
// NEW - Only email
{
  "email": "user@example.com",  // ✅ Use email only
  "password": "password123"
}
```

**Update your `LoginRequested` event:**
```dart
// In your auth_bloc.dart
class LoginRequested extends AuthEvent {
  final String email;  // Changed from username
  final String password;

  LoginRequested({
    required this.email,  // Changed from username
    required this.password,
  });
}
```

**Update your login API call:**
```dart
// In your auth repository or API service
final response = await dio.post(
  '/api/users/login/',
  data: {
    'email': email,  // Changed from username
    'password': password,
  },
);
```

**Update your LoginScreen:**
```dart
// In LoginScreen.dart - Update the login handler
void _handleLogin() {
  if (_formKey.currentState!.validate()) {
    context.read<AuthBloc>().add(
      LoginRequested(
        email: _emailController.text.trim(),  // Changed from username
        password: _passwordController.text,
      ),
    );
  }
}
```

---

### 3. **Update User Model/Response Handling**

**Before:**
```dart
// OLD - Don't use this anymore
class User {
  final int id;
  final String username;  // ❌ Remove this
  final String email;
  final String userType;
  // ...
}
```

**After:**
```dart
// NEW - No username field
class User {
  final int id;
  final String email;  // ✅ Only email
  final String userType;
  // ...
}
```

**Update your User model:**
```dart
// In your user model file
class User {
  final int id;
  final String email;
  final String? firstName;
  final String? lastName;
  final String? phone;
  final String? countryCode;
  final String userType;
  final String? profileImage;

  User({
    required this.id,
    required this.email,
    this.firstName,
    this.lastName,
    this.phone,
    this.countryCode,
    required this.userType,
    this.profileImage,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      firstName: json['first_name'],
      lastName: json['last_name'],
      phone: json['phone'],
      countryCode: json['country_code'],
      userType: json['user_type'],
      profileImage: json['profile_image'],
    );
  }
}
```

---

### 4. **Update API Response Parsing**

**Signup Response:**
```dart
// OLD Response (with username)
{
  "user": {
    "id": 1,
    "username": "user@example.com",  // ❌ Remove this
    "email": "user@example.com",
    "user_type": "advertiser"
  },
  "access": "...",
  "refresh": "..."
}

// NEW Response (no username)
{
  "user": {
    "id": 1,
    "email": "user@example.com",  // ✅ Only email
    "user_type": "advertiser"
  },
  "access": "...",
  "refresh": "..."
}
```

**Login Response:**
```dart
// OLD Response (with username)
{
  "access": "...",
  "refresh": "...",
  "user": {
    "id": 1,
    "username": "user@example.com",  // ❌ Remove this
    "email": "user@example.com",
    "user_type": "advertiser"
  }
}

// NEW Response (no username)
{
  "access": "...",
  "refresh": "...",
  "user": {
    "id": 1,
    "email": "user@example.com",  // ✅ Only email
    "user_type": "advertiser"
  }
}
```

---

### 5. **Update Storage/SharedPreferences**

**Before:**
```dart
// OLD - Don't use this anymore
await storage.write(key: 'username', value: user.username);
final username = await storage.read(key: 'username');
```

**After:**
```dart
// NEW - Use email instead
await storage.write(key: 'email', value: user.email);
final email = await storage.read(key: 'email');
```

**Update your storage keys:**
```dart
// Remove any username-related storage
// Use email for all user identification
class StorageService {
  static const String emailKey = 'user_email';
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  
  static Future<void> saveUserEmail(String email) async {
    await storage.write(key: emailKey, value: email);
  }
  
  static Future<String?> getUserEmail() async {
    return await storage.read(key: emailKey);
  }
}
```

---

### 6. **Update UI Components**

**Remove any username display:**
```dart
// OLD - Don't use this anymore
Text('Welcome, ${user.username}!')

// NEW - Use email or name
Text('Welcome, ${user.firstName ?? user.email}!')
```

**Update profile screens:**
```dart
// Remove username field from profile display
// Show email instead
ListTile(
  leading: Icon(Icons.email),
  title: Text('Email'),
  subtitle: Text(user.email),
)
```

---

## 📋 Checklist

- [ ] Remove `username` field from signup request
- [ ] Change login request from `username` to `email`
- [ ] Update `LoginRequested` event to use `email`
- [ ] Update `RegisterRequested` event to remove `username`
- [ ] Remove `username` from User model class
- [ ] Update User `fromJson` to not parse `username`
- [ ] Update storage keys from `username` to `email`
- [ ] Remove username display from UI
- [ ] Update any username references in code
- [ ] Test signup flow
- [ ] Test login flow
- [ ] Test profile display

---

## 🧪 Testing

### Test Signup:
```bash
curl -X POST "http://44.200.108.209:8000/api/users/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User",
    "user_type": "advertiser"
  }'
```

### Test Login:
```bash
curl -X POST "http://44.200.108.209:8000/api/users/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

---

## ⚠️ Important Notes

1. **Backward Compatibility**: Existing users in the database will still have a username field (it's nullable now), but new signups won't require it.

2. **Migration**: The backend migration has been created. Make sure to run it:
   ```bash
   python manage.py migrate
   ```

3. **Email Uniqueness**: Email is now unique and required. Make sure your Flutter app validates email format.

4. **Error Messages**: If you see "username" in error messages, it's from old code. Update to use email.

---

## 🚀 Quick Migration Steps

1. **Search and Replace** in your Flutter codebase:
   - `username` → `email` (in API calls and models)
   - `LoginRequested(username:` → `LoginRequested(email:`
   - Remove `username` from User model
   - Remove `username` from signup requests

2. **Update API Service**:
   - Change login endpoint to send `email` instead of `username`
   - Remove `username` from signup endpoint

3. **Update Models**:
   - Remove `username` field from User class
   - Update `fromJson` methods

4. **Test**:
   - Test signup with email only
   - Test login with email only
   - Verify no username references remain

---

## ✅ Summary

**What Changed:**
- ❌ Removed: `username` field requirement
- ✅ Added: Email-only authentication
- ✅ Updated: All API endpoints to use email
- ✅ Updated: All serializers to remove username

**What You Need to Do:**
1. Remove `username` from all Flutter API calls
2. Change login to use `email` field
3. Update User model to remove `username`
4. Update storage to use `email` instead of `username`
5. Test thoroughly

That's it! Your Flutter app should now work with the email-only backend! 🎉

