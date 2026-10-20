import os
import secrets
import requests

from flask import (
    Flask, request, render_template_string,
    redirect, session
)
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", secrets.token_hex(32)
)

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
*{box-sizing:border-box}
body{
 background:#0d1a2b;color:#00ff00;
 font-family:'Courier New',monospace;
 padding:15px;margin:0
}
.content{
 max-width:800px;margin:20px auto;background:#1a0d2b;
 padding:25px;border-radius:15px;
 box-shadow:0 0 25px #00ff00;text-align:center
}
.header-img{
 max-width:100%;max-height:280px;
 border-radius:15px;border:2px solid #ff00ff;
 object-fit:cover
}
h1,h2{color:#ff00ff;text-shadow:0 0 10px #ff00ff}
.card{
 background:#080812;border:1px solid #ff00ff;
 padding:18px;margin:20px 0;border-radius:10px;
 overflow-wrap:anywhere
}
.btn{
 padding:14px 22px;background:#ff00ff;color:#000;
 border-radius:8px;text-decoration:none;
 display:inline-block;font-weight:bold;margin:12px 0
}
.status{color:#00ff00}
.note{color:#ddd;font-size:14px;line-height:1.6}
</style>
</head>
<body>
<div class="content">
<img src="https://i.ibb.co/KjtjBDRP/file-00000000f49c821197fdc7fcda40847d.png"
 class="header-img" alt="RK RAJA">

<h1>RK RAJA TOKEN GENERATE</h1>
<p>Facebook Official Login</p>

<div class="card">
<h2>Website Status</h2>
<p class="status">{{ status }}</p>
<p class="note">{{ message }}</p>
</div>

{% if login_enabled %}
<a class="btn" href="/login">🔵 Login with Facebook</a>
{% else %}
<p class="note">Facebook login abhi configure nahi hai.</p>
{% endif %}

<p class="note">
Access tokens aur session cookies ko public page par share mat karo.
</p>
</div>
</body>
</html>
"""

def show(status, message, login_enabled=False, code=200):
    return render_template_string(
        HTML,
        status=status,
        message=message,
        login_enabled=login_enabled
    ), code

def oauth_configured():
    return bool(APP_ID and APP_SECRET and REDIRECT_URI)

@app.get("/")
def home():
    if oauth_configured():
        return show(
            "READY",
            "Official Facebook OAuth configuration detected.",
            True
        )

    return show(
        "DEMO MODE",
        "Website is running. Facebook login needs your own Meta App ID, "
        "App Secret and matching callback URL."
    )

@app.get("/login")
def login():
    if not oauth_configured():
        return show(
            "CONFIGURATION REQUIRED",
            "Set APP_ID, APP_SECRET and REDIRECT_URI in your deployment environment.",
            code=503
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
        f"https://www.facebook.com/{GRAPH_VERSION}/dialog/oauth?"
        + urlencode(params)
    )

@app.get("/callback")
def callback():
    if request.args.get("error"):
        return show(
            "LOGIN CANCELLED",
            "Facebook login was cancelled or permission was denied."
        )

    code = request.args.get("code")
    state = request.args.get("state")
    saved_state = session.pop("oauth_state", None)

    if not code:
        return show(
            "LOGIN FAILED",
            "Authorization code was not returned.",
            code=400
        )

    if not saved_state or not secrets.compare_digest(
        saved_state, state or ""
    ):
        return show(
            "LOGIN FAILED",
            "Invalid login state. Please start again.",
            code=400
        )

    if not oauth_configured():
        return show(
            "CONFIGURATION REQUIRED",
            "Facebook OAuth credentials are not configured.",
            code=503
        )

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
        token = data.get("access_token")

        if response.status_code != 200 or not token:
            return show(
                "TOKEN EXCHANGE FAILED",
                "Check your Meta app settings, callback URL and permissions.",
                code=400
            )

        check = requests.get(
            f"{GRAPH_URL}/me",
            params={
                "fields": "id,name",
                "access_token": token
            },
            timeout=20
        )

        profile = check.json()

        if check.status_code != 200 or not profile.get("id"):
            return show(
                "TOKEN VALIDATION FAILED",
                "Facebook did not validate the access token.",
                code=400
            )

        # Never print or place the token in public HTML.
        return show(
            "LOGIN SUCCESSFUL",
            "Facebook OAuth succeeded for "
            + str(profile.get("name", "your account"))
            + ". The token was validated but is not displayed."
        )

    except (requests.RequestException, ValueError):
        return show(
            "CONNECTION ERROR",
            "Facebook could not be reached. Please try again.",
            code=502
        )

@app.get("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000"))
    )
