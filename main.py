from flask import Flask, request, render_template_string, redirect, session
import requests
from urllib.parse import urlencode
import uuid

app = Flask(__name__)
app.secret_key = "rk_raja_secret_key_123"

# ⚠️ YAHAN APNI DETAILS DAALEIN (Facebook Developer se)
APP_ID = "YOUR_APP_ID"               
APP_SECRET = "YOUR_APP_SECRET"       
REDIRECT_URI = "https://YOUR-RENDER-LINK.onrender.com/callback" # /callback zaroor lagana

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>RK RAJ TOKEN GENERATE</title>
    <style>
        body { background-color: #0d1a2b; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; margin: 0;}
        .content { max-width: 900px; margin: 0 auto; background: #1a0d2b; padding: 30px; border-radius: 15px; box-shadow: 0 0 30px #00ff00; margin-top: 20px; text-align: center;}
        .header-img { max-width: 100%; max-height: 300px; border-radius: 15px; box-shadow: 0 0 20px #ff00ff, 0 0 40px #00ff00; border: 2px solid #ff00ff; object-fit: cover; margin-bottom: 20px;}
        h1 { color: #ff00ff; text-shadow: 0 0 20px #ff00ff; }
        .btn { padding: 15px 30px; background: #ff00ff; color: #000; border: none; border-radius: 8px; font-size: 1.2rem; cursor: pointer; text-decoration: none; display: inline-block; font-weight: bold; margin-top: 20px;}
        .btn:hover { background: #ff1493; box-shadow: 0 0 15px #ff1493; }
        .token-box { color: #00ff00; word-break: break-all; background: #111; padding: 15px; border: 1px solid #00ff00; margin-top: 15px; display: block; border-radius: 5px; text-align: left;}
        .card { background: #1a0d2b; border: 1px solid #ff00ff; padding: 20px; margin-bottom: 20px; border-radius: 10px; text-align: left;}
    </style>
</head>
<body>
    <div class="content">
        <img src="https://i.ibb.co/KjtjBDRP/file-00000000f49c821197fdc7fcda40847d.png" class="header-img">
        <h1>RK RAJ TOKEN GENERATE</h1>
        <p style="color: #ff00ff;">Facebook par login karein aur apna Permanent Page Token paayein.</p>
        <a href="/login" class="btn">🔵 Login with Facebook</a>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/login")
def login():
    params = {
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "pages_show_list,pages_messaging,pages_read_engagement",
        "response_type": "code"
    }
    return redirect(f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code: return "Login Fail! Wapas jayein."

    # Code to Short Token
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    token_params = {"client_id": APP_ID, "redirect_uri": REDIRECT_URI, "client_secret": APP_SECRET, "code": code}
    token_res = requests.get(token_url, params=token_params).json()
    
    if "error" in token_res: return f"❌ Error: {token_res['error']['message']}"
    short_token = token_res.get("access_token")

    # Short to Long Token (60 Days)
    exchange_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    exchange_params = {"grant_type": "fb_exchange_token", "client_id": APP_ID, "client_secret": APP_SECRET, "fb_exchange_token": short_token}
    long_token = requests.get(exchange_url, params=exchange_params).json().get("access_token", short_token)

    # Fetch Pages
    pages_res = requests.get("https://graph.facebook.com/v19.0/me/accounts", params={"access_token": long_token}).json()

    if "error" in pages_res or not pages_res.get("data"):
        return "❌ Koi Facebook Page nahi mila. Kripya ek Page banayein."

    result_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Token Result</title>
        <style>
            body { background-color: #0d1a2b; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; }
            h2 { color: #ff00ff; text-align: center; }
            .card { background: #1a0d2b; border: 1px solid #ff00ff; padding: 20px; margin-bottom: 20px; border-radius: 10px; }
            .token { background: #000; padding: 15px; word-break: break-all; color: #00ff00; font-family: monospace; border-radius: 5px; border: 1px solid #00ff00;}
            a { color: #ff00ff; font-size: 1.2rem;}
        </style>
    </head>
    <body>
        <h2>✅ Aapke Permanent Page Tokens:</h2>
    """
    for page in pages_res["data"]:
        result_html += f"""
        <div class="card">
            <h3>📄 Page: {page['name']} (ID: {page['id']})</h3>
            <p><b>Permanent Token:</b></p>
            <div class="token">{page['access_token']}</div>
        </div>
        """
    result_html += "<div style='text-align:center;'><a href='/'>⬅ Wapas Jayein</a></div></body></html>"
    return result_html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
