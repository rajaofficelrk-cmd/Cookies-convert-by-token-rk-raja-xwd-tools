from flask import Flask, request, render_template_string, jsonify
from curl_cffi import requests 
import re, threading, uuid, time

app = Flask(__name__)
tasks = {} 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>RK RAJ TOKEN GENERATE</title>
    <style>
        body { background-color: #0d1a2b; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; margin: 0;}
        .content { max-width: 900px; margin: 0 auto; background: #1a0d2b; padding: 30px; border-radius: 15px; box-shadow: 0 0 30px #00ff00; margin-top: 20px;}
        .header-container { text-align: center; margin-bottom: 20px; }
        .header-img { max-width: 100%; max-height: 300px; border-radius: 15px; box-shadow: 0 0 20px #ff00ff, 0 0 40px #00ff00; border: 2px solid #ff00ff; object-fit: cover; }
        h1 { color: #ff00ff; text-align: center; text-shadow: 0 0 20px #ff00ff; margin-top: 10px;}
        textarea { width: 100%; height: 120px; background: #0d1a2b; color: #ff00ff; border: 1px solid #00ff00; padding: 10px; font-family: monospace; font-size: 1rem; box-sizing: border-box; }
        .btn { width: 100%; padding: 15px; background: #ff00ff; color: #000; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; font-size: 1.1rem; }
        .btn:hover { background: #ff1493; box-shadow: 0 0 10px #ff1493; }
        #dashboard { margin-top: 30px; border: 1px dashed #00ff00; padding: 20px; background: #000; max-height: 400px; overflow-y: auto; font-size: 0.95rem; }
        .log { margin-bottom: 8px; }
        .token-box { color: #00ff00; word-break: break-all; background: #111; padding: 10px; border: 1px solid #00ff00; margin-top: 5px; display: block; border-radius: 5px; font-size: 1.1rem;}
        .error { color: #ff3333; font-weight: bold; }
        .success { color: #00ff00; font-weight: bold; }
    </style>
</head>
<body>
    <div class="content">
        <div class="header-container">
            <img src="https://i.ibb.co/KjtjBDRP/file-00000000f49c821197fdc7fcda40847d.png" alt="RK RAJA" class="header-img">
        </div>
        <h1>RK RAJ TOKEN GENERATE</h1>
        <p style="color: #ff00ff; text-align: center; font-size: 0.9rem;">Har line me ek account ki cookie daalein (Format: c_user=...; xs=...; datr=...; sb=...)</p>
        <form id="extractForm">
            <textarea name="cookies" id="cookiesInput" placeholder="c_user=10001...; xs=xyz...; datr=abc...; sb=def..." required></textarea>
            <button class="btn" type="submit">🔥 Start Extraction 🔥</button>
        </form>
        <h3 style="color: #00ff00;">[ LIVE DASHBOARD ]</h3>
        <div id="dashboard">
            <div class="log" style="color: #888;">Waiting for cookies...</div>
        </div>
    </div>
    <script>
        let currentTaskId = null;
        document.getElementById('extractForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const cookies = document.getElementById('cookiesInput').value;
            const dashboard = document.getElementById('dashboard');
            dashboard.innerHTML = '<div class="log" style="color: #ff00ff;">Starting Extraction... Please wait.</div>';
            fetch('/start', { method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: 'cookies=' + encodeURIComponent(cookies) })
            .then(res => res.json())
            .then(data => { if(data.task_id) { currentTaskId = data.task_id; pollLogs(); } });
        });
        function pollLogs() {
            if(!currentTaskId) return;
            fetch('/logs/' + currentTaskId).then(res => res.json()).then(data => {
                if(data.logs) {
                    const dashboard = document.getElementById('dashboard');
                    dashboard.innerHTML = '';
                    data.logs.forEach(log => {
                        const div = document.createElement('div');
                        div.className = 'log ' + (log.type || '');
                        div.innerHTML = log.text;
                        dashboard.appendChild(div);
                    });
                    dashboard.scrollTop = dashboard.scrollHeight; 
                }
                if(data.status === 'running') { setTimeout(pollLogs, 1000); }
            });
        }
    </script>
</body>
</html>
"""

def add_log(task_id, text, type=""):
    if task_id in tasks:
        tasks[task_id]['logs'].append({"text": text, "type": type})

def extract_token_ultimate(cookie, task_id):
    uid_match = re.search(r'c_user=(\d+)', cookie)
    if not uid_match:
        return None, "Format Error: c_user nahi mila."
    uid = uid_match.group(1)

    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        add_log(task_id, f"🔍 UID {uid}: Checking endpoints...")

        # 1. Watch Page (Sabse zyada token leak hota hai yahan)
        r_watch = requests.get("https://www.facebook.com/watch/", headers=headers, impersonate="chrome120", timeout=15)
        token_watch = re.search(r'"accessToken":"(EAAAA[A-Za-z0-9_\-]+)"', r_watch.text)
        if token_watch: return token_watch.group(1), "Success (Watch Page)"

        # 2. Messages Page
        r_msg = requests.get("https://www.facebook.com/messages/", headers=headers, impersonate="chrome120", timeout=15)
        token_msg = re.search(r'"accessToken":"(EAAAA[A-Za-z0-9_\-]+)"', r_msg.text)
        if token_msg: return token_msg.group(1), "Success (Messenger Page)"

        # 3. Business Suite (Agar account purana hai, toh yahan pakka milega)
        r_biz = requests.get("https://business.facebook.com/latest/home", headers=headers, impersonate="chrome120", timeout=15)
        token_biz = re.search(r'"accessToken":"(EAAAA[A-Za-z0-9_\-]+)"', r_biz.text)
        if token_biz: return token_biz.group(1), "Success (Business Suite)"

        # 4. Composer (Mobile mBasic)
        r_comp = requests.get("https://m.facebook.com/composer/", headers=headers, impersonate="chrome120", timeout=15)
        token_comp = re.search(r'access_token=(EAAAA[A-Za-z0-9_\-]+)', r_comp.text)
        if token_comp: return token_comp.group(1), "Success (Mobile Composer)"

        # 5. Direct GraphQL (Naya Doc ID)
        dtsg_match = re.search(r'"DTSGInitialData",\[\],\{"token":"(.*?)"', r_watch.text)
        if dtsg_match:
            fb_dtsg = dtsg_match.group(1)
            graphql_url = "https://www.facebook.com/api/graphql/"
            payload = {
                "av": uid, "__user": uid, "__a": "1", "fb_dtsg": fb_dtsg,
                "fb_api_req_friendly_name": "CometUserTokenQuery",
                "variables": "{}", "doc_id": "8490247306714249" # UPDATED DOC ID
            }
            graphql_res = requests.post(graphql_url, headers=headers, data=payload, impersonate="chrome120", timeout=15)
            token_match_g = re.search(r'(EAAAA[A-Za-z0-9_\-]{50,})', graphql_res.text)
            if token_match_g: return token_match_g.group(1), "Success (GraphQL API)"

        return None, "Facebook ne saare raste band kar diye hain. Account restricted hai."
        
    except Exception as e:
        return None, f"System Error: {str(e)}"

def process_cookies(task_id, cookie_text):
    lines = [line.strip() for line in cookie_text.split('\n') if line.strip()]
    for index, line in enumerate(lines, 1):
        uid_match = re.search(r'c_user=(\d+)', line)
        uid = uid_match.group(1) if uid_match else "Unknown"
        
        token, msg = extract_token_ultimate(line, task_id)
        
        if token:
            add_log(task_id, f"✅ Token mil gaya! ({msg})", "success")
            add_log(task_id, f"{token}", "token-box")
        else:
            add_log(task_id, f"❌ {msg}", "error")
        time.sleep(1.5) 
        
    tasks[task_id]['status'] = 'completed'

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/start", methods=["POST"])
def start():
    cookie_text = request.form.get("cookies").strip()
    task_id = str(uuid.uuid4())[:8]
    tasks[task_id] = {"logs": [], "status": "running"}
    threading.Thread(target=process_cookies, args=(task_id, cookie_text), daemon=True).start()
    return jsonify({"task_id": task_id})

@app.route("/logs/<task_id>")
def get_logs(task_id):
    if task_id in tasks:
        return jsonify(tasks[task_id])
    return jsonify({"logs": [], "status": "not_found"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
