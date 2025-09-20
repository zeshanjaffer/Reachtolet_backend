# 📱 Phone Number & Country Code Implementation

Your Django backend now supports **international phone numbers with country codes**! 🎉

## ✅ **What's Been Added**

### 1. **User Model Updates**
- ✅ **`country_code`** field (e.g., 'US', 'GB', 'IN')
- ✅ **Enhanced `phone`** field with validation
- ✅ **Formatted phone display** method
- ✅ **Database migration** applied

### 2. **Registration Endpoint Updates**
- ✅ **Accepts `country_code`** in registration payload
- ✅ **Validates country code** format and existence
- ✅ **Stores full international** phone number
- ✅ **Enhanced error messages** for invalid data

### 3. **Phone Number Validation**
- ✅ **International format** validation (e.g., '+1234567890')
- ✅ **Country-specific** phone number patterns
- ✅ **100+ country codes** supported
- ✅ **Real-time validation** with helpful error messages

### 4. **API Response Updates**
- ✅ **Includes `country_code`** in user profile responses
- ✅ **Returns `formatted_phone`** field
- ✅ **Enhanced user serializers** with validation

## 🚀 **New API Endpoints**

### **Get Country Codes**
```
GET /api/users/country-codes/
```
**Response:**
```json
{
  "countries": [
    {
      "code": "US",
      "name": "United States",
      "dial_code": "+1"
    },
    {
      "code": "GB", 
      "name": "United Kingdom",
      "dial_code": "+44"
    }
  ],
  "total": 100
}
```

## 📝 **Updated Registration Payload**

### **Example Registration Request:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "country_code": "US",
  "password": "password123"
}
```

### **Example Registration Response:**
```json
{
  "user": {
    "id": 123,
    "username": "john@example.com",
    "email": "john@example.com",
    "phone": "+1234567890",
    "country_code": "US",
    "formatted_phone": "US +1234567890",
    "name": "John Doe"
  },
  "access": "access_token_here",
  "refresh": "refresh_token_here",
  "message": "User registered successfully"
}
```

## 🔍 **Validation Rules**

### **Country Code Validation:**
- ✅ Must be 2 uppercase letters (e.g., 'US', 'GB')
- ✅ Must be a valid ISO 3166-1 alpha-2 country code
- ✅ **100+ countries** supported

### **Phone Number Validation:**
- ✅ Must be in international format (e.g., '+1234567890')
- ✅ Must match country-specific pattern
- ✅ **Country-specific validation** for accuracy

### **Consistency Validation:**
- ✅ If phone provided → country_code required
- ✅ If country_code provided → phone required
- ✅ Both must be valid together

## 🛠 **Supported Countries**

Your backend supports **100+ countries** including:

**Popular Countries:**
- 🇺🇸 **US** (United States) - +1
- 🇬🇧 **GB** (United Kingdom) - +44  
- 🇮🇳 **IN** (India) - +91
- 🇨🇦 **CA** (Canada) - +1
- 🇦🇺 **AU** (Australia) - +61
- 🇩🇪 **DE** (Germany) - +49
- 🇫🇷 **FR** (France) - +33
- 🇮🇹 **IT** (Italy) - +39
- 🇪🇸 **ES** (Spain) - +34
- 🇧🇷 **BR** (Brazil) - +55

**And 90+ more countries!**

## 📱 **React Native Implementation**

### **Registration Form Example:**
```javascript
const registerUser = async (userData) => {
  try {
    const response = await fetch('/api/users/register/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: userData.name,
        email: userData.email,
        phone: userData.phone,        // e.g., "+1234567890"
        country_code: userData.country_code,  // e.g., "US"
        password: userData.password
      })
    });
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Registration failed:', error);
  }
};
```

### **Get Country Codes for Dropdown:**
```javascript
const getCountryCodes = async () => {
  try {
    const response = await fetch('/api/users/country-codes/');
    const data = await response.json();
    return data.countries;
  } catch (error) {
    console.error('Failed to get country codes:', error);
  }
};
```

## 🔧 **Error Messages**

### **Invalid Country Code:**
```json
{
  "country_code": "Invalid country code: XX. Please use a valid ISO 3166-1 alpha-2 country code."
}
```

### **Invalid Phone Number:**
```json
{
  "phone": "Invalid phone number format for United States"
}
```

### **Missing Country Code:**
```json
{
  "country_code": "Country code is required when phone number is provided"
}
```

### **Missing Phone Number:**
```json
{
  "phone": "Phone number is required when country code is provided"
}
```

## 🎯 **Admin Interface Updates**

- ✅ **Country code** field in admin
- ✅ **Formatted phone** display
- ✅ **Country code** filtering
- ✅ **Enhanced search** functionality

## ✅ **Database Changes**

- ✅ **New `country_code`** column added
- ✅ **Enhanced `phone`** field validation
- ✅ **Migration** applied successfully
- ✅ **Backward compatible** with existing data

## 🚀 **Ready to Use!**

Your backend now supports:
- ✅ **International phone numbers**
- ✅ **Country code validation**
- ✅ **Enhanced user registration**
- ✅ **Better error messages**
- ✅ **Admin interface updates**

**Perfect for your React Native app!** 📱✨
