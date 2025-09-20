"""
Country codes utility for phone number validation
ISO 3166-1 alpha-2 country codes
"""

# Common country codes with their phone number patterns
COUNTRY_CODES = {
    'US': {'name': 'United States', 'dial_code': '+1', 'pattern': r'^\+1\d{10}$'},
    'GB': {'name': 'United Kingdom', 'dial_code': '+44', 'pattern': r'^\+44\d{10,11}$'},
    'IN': {'name': 'India', 'dial_code': '+91', 'pattern': r'^\+91\d{10}$'},
    'CA': {'name': 'Canada', 'dial_code': '+1', 'pattern': r'^\+1\d{10}$'},
    'AU': {'name': 'Australia', 'dial_code': '+61', 'pattern': r'^\+61\d{9}$'},
    'DE': {'name': 'Germany', 'dial_code': '+49', 'pattern': r'^\+49\d{10,12}$'},
    'FR': {'name': 'France', 'dial_code': '+33', 'pattern': r'^\+33\d{9}$'},
    'IT': {'name': 'Italy', 'dial_code': '+39', 'pattern': r'^\+39\d{9,10}$'},
    'ES': {'name': 'Spain', 'dial_code': '+34', 'pattern': r'^\+34\d{9}$'},
    'BR': {'name': 'Brazil', 'dial_code': '+55', 'pattern': r'^\+55\d{10,11}$'},
    'MX': {'name': 'Mexico', 'dial_code': '+52', 'pattern': r'^\+52\d{10}$'},
    'AR': {'name': 'Argentina', 'dial_code': '+54', 'pattern': r'^\+54\d{10,11}$'},
    'CL': {'name': 'Chile', 'dial_code': '+56', 'pattern': r'^\+56\d{9}$'},
    'CO': {'name': 'Colombia', 'dial_code': '+57', 'pattern': r'^\+57\d{10}$'},
    'PE': {'name': 'Peru', 'dial_code': '+51', 'pattern': r'^\+51\d{9}$'},
    'VE': {'name': 'Venezuela', 'dial_code': '+58', 'pattern': r'^\+58\d{10}$'},
    'PK': {'name': 'Pakistan', 'dial_code': '+92', 'pattern': r'^\+92\d{10}$'},
    'BD': {'name': 'Bangladesh', 'dial_code': '+880', 'pattern': r'^\+880\d{10}$'},
    'LK': {'name': 'Sri Lanka', 'dial_code': '+94', 'pattern': r'^\+94\d{9}$'},
    'NP': {'name': 'Nepal', 'dial_code': '+977', 'pattern': r'^\+977\d{10}$'},
    'MY': {'name': 'Malaysia', 'dial_code': '+60', 'pattern': r'^\+60\d{9,10}$'},
    'SG': {'name': 'Singapore', 'dial_code': '+65', 'pattern': r'^\+65\d{8}$'},
    'TH': {'name': 'Thailand', 'dial_code': '+66', 'pattern': r'^\+66\d{9}$'},
    'VN': {'name': 'Vietnam', 'dial_code': '+84', 'pattern': r'^\+84\d{9,10}$'},
    'PH': {'name': 'Philippines', 'dial_code': '+63', 'pattern': r'^\+63\d{10}$'},
    'ID': {'name': 'Indonesia', 'dial_code': '+62', 'pattern': r'^\+62\d{9,12}$'},
    'JP': {'name': 'Japan', 'dial_code': '+81', 'pattern': r'^\+81\d{9,10}$'},
    'KR': {'name': 'South Korea', 'dial_code': '+82', 'pattern': r'^\+82\d{9,10}$'},
    'CN': {'name': 'China', 'dial_code': '+86', 'pattern': r'^\+86\d{11}$'},
    'RU': {'name': 'Russia', 'dial_code': '+7', 'pattern': r'^\+7\d{10}$'},
    'UA': {'name': 'Ukraine', 'dial_code': '+380', 'pattern': r'^\+380\d{9}$'},
    'PL': {'name': 'Poland', 'dial_code': '+48', 'pattern': r'^\+48\d{9}$'},
    'CZ': {'name': 'Czech Republic', 'dial_code': '+420', 'pattern': r'^\+420\d{9}$'},
    'HU': {'name': 'Hungary', 'dial_code': '+36', 'pattern': r'^\+36\d{9}$'},
    'RO': {'name': 'Romania', 'dial_code': '+40', 'pattern': r'^\+40\d{9}$'},
    'BG': {'name': 'Bulgaria', 'dial_code': '+359', 'pattern': r'^\+359\d{9}$'},
    'HR': {'name': 'Croatia', 'dial_code': '+385', 'pattern': r'^\+385\d{8,9}$'},
    'RS': {'name': 'Serbia', 'dial_code': '+381', 'pattern': r'^\+381\d{8,9}$'},
    'SI': {'name': 'Slovenia', 'dial_code': '+386', 'pattern': r'^\+386\d{8}$'},
    'SK': {'name': 'Slovakia', 'dial_code': '+421', 'pattern': r'^\+421\d{9}$'},
    'LT': {'name': 'Lithuania', 'dial_code': '+370', 'pattern': r'^\+370\d{8}$'},
    'LV': {'name': 'Latvia', 'dial_code': '+371', 'pattern': r'^\+371\d{8}$'},
    'EE': {'name': 'Estonia', 'dial_code': '+372', 'pattern': r'^\+372\d{8}$'},
    'FI': {'name': 'Finland', 'dial_code': '+358', 'pattern': r'^\+358\d{9}$'},
    'SE': {'name': 'Sweden', 'dial_code': '+46', 'pattern': r'^\+46\d{9}$'},
    'NO': {'name': 'Norway', 'dial_code': '+47', 'pattern': r'^\+47\d{8}$'},
    'DK': {'name': 'Denmark', 'dial_code': '+45', 'pattern': r'^\+45\d{8}$'},
    'NL': {'name': 'Netherlands', 'dial_code': '+31', 'pattern': r'^\+31\d{9}$'},
    'BE': {'name': 'Belgium', 'dial_code': '+32', 'pattern': r'^\+32\d{9}$'},
    'CH': {'name': 'Switzerland', 'dial_code': '+41', 'pattern': r'^\+41\d{9}$'},
    'AT': {'name': 'Austria', 'dial_code': '+43', 'pattern': r'^\+43\d{10,11}$'},
    'IE': {'name': 'Ireland', 'dial_code': '+353', 'pattern': r'^\+353\d{9}$'},
    'PT': {'name': 'Portugal', 'dial_code': '+351', 'pattern': r'^\+351\d{9}$'},
    'GR': {'name': 'Greece', 'dial_code': '+30', 'pattern': r'^\+30\d{10}$'},
    'TR': {'name': 'Turkey', 'dial_code': '+90', 'pattern': r'^\+90\d{10}$'},
    'IL': {'name': 'Israel', 'dial_code': '+972', 'pattern': r'^\+972\d{9}$'},
    'SA': {'name': 'Saudi Arabia', 'dial_code': '+966', 'pattern': r'^\+966\d{9}$'},
    'AE': {'name': 'United Arab Emirates', 'dial_code': '+971', 'pattern': r'^\+971\d{9}$'},
    'EG': {'name': 'Egypt', 'dial_code': '+20', 'pattern': r'^\+20\d{10}$'},
    'ZA': {'name': 'South Africa', 'dial_code': '+27', 'pattern': r'^\+27\d{9}$'},
    'NG': {'name': 'Nigeria', 'dial_code': '+234', 'pattern': r'^\+234\d{10}$'},
    'KE': {'name': 'Kenya', 'dial_code': '+254', 'pattern': r'^\+254\d{9}$'},
    'GH': {'name': 'Ghana', 'dial_code': '+233', 'pattern': r'^\+233\d{9}$'},
    'ET': {'name': 'Ethiopia', 'dial_code': '+251', 'pattern': r'^\+251\d{9}$'},
    'TZ': {'name': 'Tanzania', 'dial_code': '+255', 'pattern': r'^\+255\d{9}$'},
    'UG': {'name': 'Uganda', 'dial_code': '+256', 'pattern': r'^\+256\d{9}$'},
    'MW': {'name': 'Malawi', 'dial_code': '+265', 'pattern': r'^\+265\d{9}$'},
    'ZM': {'name': 'Zambia', 'dial_code': '+260', 'pattern': r'^\+260\d{9}$'},
    'ZW': {'name': 'Zimbabwe', 'dial_code': '+263', 'pattern': r'^\+263\d{9}$'},
    'BW': {'name': 'Botswana', 'dial_code': '+267', 'pattern': r'^\+267\d{8}$'},
    'NA': {'name': 'Namibia', 'dial_code': '+264', 'pattern': r'^\+264\d{9}$'},
    'MZ': {'name': 'Mozambique', 'dial_code': '+258', 'pattern': r'^\+258\d{9}$'},
    'MG': {'name': 'Madagascar', 'dial_code': '+261', 'pattern': r'^\+261\d{9}$'},
    'MU': {'name': 'Mauritius', 'dial_code': '+230', 'pattern': r'^\+230\d{8}$'},
    'SC': {'name': 'Seychelles', 'dial_code': '+248', 'pattern': r'^\+248\d{7}$'},
    'KM': {'name': 'Comoros', 'dial_code': '+269', 'pattern': r'^\+269\d{7}$'},
    'DJ': {'name': 'Djibouti', 'dial_code': '+253', 'pattern': r'^\+253\d{8}$'},
    'SO': {'name': 'Somalia', 'dial_code': '+252', 'pattern': r'^\+252\d{8}$'},
    'ER': {'name': 'Eritrea', 'dial_code': '+291', 'pattern': r'^\+291\d{7}$'},
    'SD': {'name': 'Sudan', 'dial_code': '+249', 'pattern': r'^\+249\d{9}$'},
    'SS': {'name': 'South Sudan', 'dial_code': '+211', 'pattern': r'^\+211\d{9}$'},
    'CF': {'name': 'Central African Republic', 'dial_code': '+236', 'pattern': r'^\+236\d{8}$'},
    'TD': {'name': 'Chad', 'dial_code': '+235', 'pattern': r'^\+235\d{8}$'},
    'CM': {'name': 'Cameroon', 'dial_code': '+237', 'pattern': r'^\+237\d{8}$'},
    'GQ': {'name': 'Equatorial Guinea', 'dial_code': '+240', 'pattern': r'^\+240\d{9}$'},
    'GA': {'name': 'Gabon', 'dial_code': '+241', 'pattern': r'^\+241\d{8}$'},
    'CG': {'name': 'Republic of the Congo', 'dial_code': '+242', 'pattern': r'^\+242\d{9}$'},
    'CD': {'name': 'Democratic Republic of the Congo', 'dial_code': '+243', 'pattern': r'^\+243\d{9}$'},
    'AO': {'name': 'Angola', 'dial_code': '+244', 'pattern': r'^\+244\d{9}$'},
    'GW': {'name': 'Guinea-Bissau', 'dial_code': '+245', 'pattern': r'^\+245\d{7}$'},
    'CV': {'name': 'Cape Verde', 'dial_code': '+238', 'pattern': r'^\+238\d{7}$'},
    'GM': {'name': 'Gambia', 'dial_code': '+220', 'pattern': r'^\+220\d{7}$'},
    'SN': {'name': 'Senegal', 'dial_code': '+221', 'pattern': r'^\+221\d{9}$'},
    'ML': {'name': 'Mali', 'dial_code': '+223', 'pattern': r'^\+223\d{8}$'},
    'BF': {'name': 'Burkina Faso', 'dial_code': '+226', 'pattern': r'^\+226\d{8}$'},
    'NE': {'name': 'Niger', 'dial_code': '+227', 'pattern': r'^\+227\d{8}$'},
    'TD': {'name': 'Chad', 'dial_code': '+235', 'pattern': r'^\+235\d{8}$'},
    'MR': {'name': 'Mauritania', 'dial_code': '+222', 'pattern': r'^\+222\d{8}$'},
    'MA': {'name': 'Morocco', 'dial_code': '+212', 'pattern': r'^\+212\d{9}$'},
    'DZ': {'name': 'Algeria', 'dial_code': '+213', 'pattern': r'^\+213\d{9}$'},
    'TN': {'name': 'Tunisia', 'dial_code': '+216', 'pattern': r'^\+216\d{8}$'},
    'LY': {'name': 'Libya', 'dial_code': '+218', 'pattern': r'^\+218\d{9}$'},
    'JO': {'name': 'Jordan', 'dial_code': '+962', 'pattern': r'^\+962\d{9}$'},
    'LB': {'name': 'Lebanon', 'dial_code': '+961', 'pattern': r'^\+961\d{8}$'},
    'SY': {'name': 'Syria', 'dial_code': '+963', 'pattern': r'^\+963\d{9}$'},
    'IQ': {'name': 'Iraq', 'dial_code': '+964', 'pattern': r'^\+964\d{10}$'},
    'KW': {'name': 'Kuwait', 'dial_code': '+965', 'pattern': r'^\+965\d{8}$'},
    'QA': {'name': 'Qatar', 'dial_code': '+974', 'pattern': r'^\+974\d{8}$'},
    'BH': {'name': 'Bahrain', 'dial_code': '+973', 'pattern': r'^\+973\d{8}$'},
    'OM': {'name': 'Oman', 'dial_code': '+968', 'pattern': r'^\+968\d{8}$'},
    'YE': {'name': 'Yemen', 'dial_code': '+967', 'pattern': r'^\+967\d{9}$'},
}

def is_valid_country_code(country_code):
    """Check if country code is valid"""
    return country_code.upper() in COUNTRY_CODES

def get_country_info(country_code):
    """Get country information by country code"""
    return COUNTRY_CODES.get(country_code.upper())

def get_all_country_codes():
    """Get list of all valid country codes"""
    return list(COUNTRY_CODES.keys())

def validate_phone_for_country(phone, country_code):
    """Validate phone number for specific country"""
    country_info = get_country_info(country_code)
    if not country_info:
        return False, f"Invalid country code: {country_code}"
    
    import re
    if not re.match(country_info['pattern'], phone):
        return False, f"Invalid phone number format for {country_info['name']}"
    
    return True, "Valid phone number"

def get_country_dial_code(country_code):
    """Get dial code for country"""
    country_info = get_country_info(country_code)
    return country_info['dial_code'] if country_info else None
