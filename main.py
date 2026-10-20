
import os
import secrets
import requests
from flask import (
    Flask, request, render_template_string,
    redirect, session
)
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

APP_ID = os.environ.get("APP_ID", "").strip()
APP_SECRET = os.environ.get("APP_SECRET", "").strip()
REDIRECT_URI = os.environ.get(
    "REDIRECT_URI",
    "https://cookies-convert-by-token-rk-raja-xwd-8lwq.onrender.com/callback"
).strip()

GRAPH_VERSION = "v23.0"
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RK RAJA TOKEN GENERATE</title>
<style>
body{background:#0d1a2b;color:#00ff00;font-family:monospace;
padding:20px;margin:0}
.content{max-width:900px;margin:20px auto;background:#1a0d2b;
padding:25px;border-radius:15px;box-shadow:0 0 25px #00ff00;
text-align:center}
.header-img{max-width:100%;max-height:280px;border-radius:15px;
border:2px solid #ff00ff;object-fit:cover}
h1,h2{color:#ff00ff}
.btn{padding:14px 24px;background:#ff00ff;color:#000;
border-radius:8px;text-decoration:none;display:inline-block;
font-weight:bold;margin:15px 0}
.card{background:#080812;border:1px solid #ff00ff;
padding:18px;margin:18px 0;border-radius:10px;overflow-wrap:anywhere}
.error{color:#ff7777}
</style>
</head>
<body>
<div class="content">
<img src="https://i.ibb.co/KjtjBDRP/file-00000000f49c821197fdc7fcda40847d.png"
class="header-img" alt="RK RAJA">
<h1>RK RAJA TOKEN GENERATE</h1>
<p>Official Facebook Login &amp; Page Access</p>
{% if message %}
<div class="card">{{ message }}</div>
{% endif %}
<a class="btn" href="/login">🔵 Login with Facebook</a>
</div>
</body>
</html>
"""

def show(message="", status=200):
    return render_template_string(HTML, message=message), status

@app.get("/")
def home():
    return show()

@app.get("/login")
def login():
    if not APP_ID or not REDIRECT_URI:
        return show(
            "Configuration missing: set APP_ID and REDIRECT_URI in Render.",
            500
        )

    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    params = {
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "public_profile,pages_show_list",
        "state": state
    }

    return redirect(
        "https://www.facebook.com/"
        + GRAPH_VERSION
        + "/dialog/oauth?"
        + urlencode(params)
    )

@app.get("/callback")
def callback():
    if request.args.get("error"):
        return show("Facebook login cancelled or permission denied.")

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return show("Authorization code missing.", 400)

    saved_state = session.pop("oauth_state", None)
    if not saved_state or not secrets.compare_digest(saved_state, state or ""):
        return show("Invalid login state. Please login again.", 400)

    if not APP_ID or not APP_SECRET or not REDIRECT_URI:
        return show("Set APP_ID, APP_SECRET and REDIRECT_URI in Render.", 500)

    try:
        response = requests.get(
            f"{GRAPH_URL}/oauth/access_token",
            params={
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code
            },
            timeout=20
        )
        data = response.json()

        if response.status_code != 200 or not data.get("access_token"):
            # Do not display secrets or raw token responses.
            return show(
                "Token exchange failed. Check Meta app settings, "
                "redirect URI and permissions.",
                400
            )

        # Validate the token without exposing it in the webpage.
        token = data["access_token"]
        check = requests.get(
            f"{GRAPH_URL}/me",
            params={"fields": "id,name", "access_token": token},
            timeout=20
        )
        profile = check.json()

        if check.status_code != 200 or not profile.get("id"):
            return show("Token validation failed. Please try logging in again.", 400)

        return show(
            "Login successful! Token generated and validated for "
            + str(profile.get("name", "your account"))
            + ". Token is not displayed publicly."
        )

    except (requests.RequestException, ValueError):
        return show("Facebook connection error. Please retry.", 502)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000"))
    )
