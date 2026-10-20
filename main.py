import requests
import re

# ==========================================
# YAHAN APNI COOKIE PASTE KAREIN
# (Browser se c_user, xs, datr, sb sab copy karein)
# ==========================================
COOKIE = "c_user=...; xs=...; datr=...; sb=..."

def get_token():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': COOKIE
    }

    print("Facebook se connect ho rahe hain...")
    
    try:
        # 1. Homepage fetch karo
        r_home = requests.get("https://www.facebook.com/", headers=headers, timeout=15)
        
        # 2. Token dhoondo
        token_match = re.search(r'(EAAAA[A-Za-z0-9_\-]{50,})', r_home.text)
        
        if token_match:
            print("\n✅ SUCCESS! Aapka Token Mil Gaya:\n")
            print(token_match.group(1))
            print("\nIs token ko copy karke apne tool me daal dein.")
        else:
            print("\n❌ Token nahi mila. Iske 2 hi reason ho sakte hain:")
            print("1. Aapki cookie expire ho gayi hai (Browser me dobara login karein).")
            print("2. Account checkpoint me hai (Browser me OTP verify karein).")
            
    except Exception as e:
        print("\nError aaya:", str(e))

if __name__ == "__main__":
    get_token()
