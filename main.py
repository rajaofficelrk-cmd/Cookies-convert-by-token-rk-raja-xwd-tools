
import os
import secrets
import requests
from flask import Flask, request, redirect, session, render_template_string
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

APP_ID = os.environ.get("APP_ID", "").strip()
APP_SECRET = os.environ.get("APP_SECRET", "").strip()
REDIRECT_URI = os.environ.get(
    "REDIRECT_URI",
    "https://cookies-convert-by-token-rk-raja-xwd-8lwq.onrender.com/callback"
).strip()

VERSION = "v23.0"
GRAPH = f"https://graph.facebook.com/{VERSION}"

PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RK RAJA TOKEN GENERATE</title>
<style>
body{background:#0d1a2b;color:#00ff00;font-family:monospace;padding:16px}
main{max-width:700px;margin:auto;background:#1a0d2b;padding:22px;
border-radius:18px;box-shadow:0 0 25px #00ff00;text-align:center}
img{width:100%;max-width:480px;border:2px solid #ff00ff;border-radius:16px}
h1,h2{color:#ff00ff}
.card{background:#080812;border:1px solid #ff00ff;border-radius:12px;
padding:18px;margin:20px 0;overflow-wrap:anywhere}
a,button{display:inline-block;padding:14px 22px;background:#ff00ff;
color:black;text-decoration:none;border:0;border-radius:8px;font-weight:bold}
</style>
</head>
<body><main>
<img src="https://i.ibb.co/KjtjBDRP/file-00000000f49c821197fdc7fcda40847d.png" alt="RK RAJA">
<h1>RK RAJA TOKEN GENERATE</h1>
<p>Facebook Official Login</p>
<div class="card"><h2>{{ status }}</h2><p>{{ message }}</p></div>
{% if enabled %}<a href="/login">Login with Facebook</a>{% endif %}
</main></body></html>
"""

def page(status, message, enabled=False, code=200):
    return render_template_string(
        PAGE, status=status, message=message, enabled=enabled
    ), code

@app.get("/")
def home():
    if not all([APP_ID, APP_SECRET, REDIRECT_URI]):
        return page(
            "DEMO MODE",
            "Set APP_ID, APP_SECRET and REDIRECT_URI in Render Environment."
        )
    return page("READY", "Official Facebook OAuth is configured.", True)

@app.get("/login")
def login():
    if not all([APP_ID, APP_SECRET, REDIRECT_URI]):
        return page("CONFIGURATION MISSING", "Configure the required Render variables.", code=503)

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
        f"https://www.facebook.com/{VERSION}/dialog/oauth?{urlencode(params)}"
    )

@app.get("/callback")
def callback():
    if request.args.get("error"):
        return page("LOGIN CANCELLED", "Facebook denied or cancelled login.")

    code = request.args.get("code")
    state = request.args.get("state")
    saved = session.pop("oauth_state", None)

    if not code or not saved or not secrets.compare_digest(saved, state or ""):
        return page("LOGIN FAILED", "Missing code or invalid login state.", code=400)

    try:
        response = requests.get(
            f"{GRAPH}/oauth/access_token",
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
            return page(
                "TOKEN ERROR",
                "Check Meta App settings, callback URL and permissions.",
                code=400
            )

        check = requests.get(
            f"{GRAPH}/me",
            params={"fields": "id,name", "access_token": token},
            timeout=20
        )
        profile = check.json()

        if check.status_code != 200 or not profile.get("id"):
            return page("TOKEN INVALID", "Facebook could not validate the token.", code=400)

        return page(
            "TOKEN GENERATED",
            f"Authorized account verified: {profile.get('name', 'Facebook user')}. "
            "Token validated; it is not displayed publicly."
        )

    except (requests.RequestException, ValueError):
        return page("CONNECTION ERROR", "Facebook request failed. Please retry.", code=502)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
