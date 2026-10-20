
import os
import requests
from flask import Flask, request, render_template_string, redirect, session
from urllib.parse import urlencode
from markupsafe import escape

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret")

APP_ID = os.environ.get("APP_ID", "")
APP_SECRET = os.environ.get("APP_SECRET", "")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "")

GRAPH_VERSION = "v23.0"
GRAPH = f"https://graph.facebook.com/{GRAPH_VERSION}"

HTML_TEMPLATE = """
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
padding:30px;border-radius:15px;box-shadow:0 0 30px #00ff00;
text-align:center}
.header-img{max-width:100%;max-height:300px;border-radius:15px;
border:2px solid #ff00ff;object-fit:cover}
h1,h2{color:#ff00ff}
.btn{padding:15px 30px;background:#ff00ff;color:#000;
border-radius:8px;text-decoration:none;display:inline-block;
font-weight:bold;margin-top:20px}
.card{background:#10091c;border:1px solid #ff00ff;
padding:20px;margin:20px 0;border-radius:10px;overflow-wrap:anywhere}
.error{color:#ff6666}
</style>
</head>
<body><div class="content">
<img src="https://i.ibb.co/KjtjBDRP/file-00000000f49c821197fdc7fcda40847d.png"
class="header-img" alt="RK RAJA">
<h1>RK RAJA TOKEN GENERATE</h1>
<p>Official Facebook Login &amp; Page Access</p>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
{% if token %}
<div class="card">
<h2>Login Successful</h2>
<p>Token received. For security, it is not displayed on this page.</p>
</div>
{% endif %}
<a href="/login" class="btn">🔵 Login with Facebook</a>
</div></body></html>
"""

def page(message=None, token=False, status=200):
    return render_template_string(
        HTML_TEMPLATE, error=message, token=token
    ), status

@app.route("/")
def home():
    return page()

@app.route("/login")
def login():
    if not APP_ID or not REDIRECT_URI:
        return page("Server configuration missing. Check APP_ID and REDIRECT_URI.",  status=500)

    import secrets
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    params = {
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "public_profile,pages_show_list",
        "response_type": "code",
        "state": state,
    }
    return redirect(
        "https://www.facebook.com/" + GRAPH_VERSION
        + "/dialog/oauth?" + urlencode(params)
    )

@app.route("/callback")
def callback():
    if request.args.get("error"):
        return page("Facebook login cancelled or denied.")

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return page("Authorization code missing.", status=400)

    if not state or state != session.pop("oauth_state", None):
        return page("Invalid login state. Please try again.", status=400)

    if not APP_ID or not APP_SECRET or not REDIRECT_URI:
        return page("Server OAuth configuration is incomplete.", status=500)

    try:
        response = requests.get(
            f"{GRAPH}/oauth/access_token",
            params={
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
            timeout=15,
        )
        data = response.json()

        if response.status_code != 200 or "access_token" not in data:
            return page("Token exchange failed. Check Meta app settings and redirect URI.", status=400)

        # Do not print or expose the token in public HTML.
        return page("Token generated successfully. Configure a secure server-side token storage workflow.", token=True)

    except (requests.RequestException, ValueError):
        return page("Facebook connection failed. Please retry.", status=502)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
