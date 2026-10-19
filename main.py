from flask import Flask, request, render_template_string, jsonify
import requests, re, threading, uuid, time

app = Flask(__name__)
tasks = {} # Store logs and tokens for each task

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>RK RAJA TOKEN GENERATE</title>
    <style>
        body { background-color: #0d1a2b; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; }
        .content { max-width: 900px; margin: 0 auto; background: #1a0d2b; padding: 30px; border-radius: 15px; box-shadow: 0 0 30px #00ff00; margin-top: 20px;}
        
        /* Header Image Styling */
        .header-container {
            text-align: center;
            margin-bottom: 20px;
        }
        .header-img {
            max-width: 100%;
            max-height: 350px;
            border-radius: 15px;
            box-shadow: 0 0 20px #ff00ff, 0 0 40px #00ff00; /* Neon Glow */
            border: 2px solid #ff00ff;
            object-fit: cover;
        }

        h1 { color: #ff00ff; text-align: center; text-shadow: 0 0 20px #ff00ff; margin-top: 10px;}
        textarea { width: 100%; height: 150px; background: #0d1a2b; color: #ff00ff; border: 1px solid #00ff00; padding: 10px; font-family: monospace; font-size: 1rem; }
        .btn { width: 100%; padding: 15px; background: #ff00ff; color: #000; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; font-size: 1.1rem; }
        .btn:hover { background: #ff1493; box-shadow: 0 0 10px #ff1493; }
        
        #dashboard { margin-top: 30px; border: 1px dashed #00ff00; padding: 20px; background: #000; max-height: 500px; overflow-y: auto; font-size: 0.95rem; }
        .log { margin-bottom: 8px; }
        .token-box { color: #00ff00; word-break: break-all; background: #111; padding: 10px; border: 1px solid #00ff00; margin-top: 5px; display: block; border-radius: 5px;}
        .error { color: #ff3333; font-weight: bold; }
        .success { color: #00ff00; font-weight: bold; }
    </style>
</head>
<body>
    <div class="content">
        <!-- Aapki Image Yahan Lag Gayi Hai -->
        <div class="header-container">
            <img src="https://i.ibb.co/KjtjBDRP/file-00000000f49c821197fdc7fcda40847d.png" alt="RK RAJA" class="header-img">
        </div>

        <h1>RK RAJA TOKEN GENERATE</h1>
        <p style="color: #ff00ff; text-align: center;">Har line mein ek account ki cookie daalein (Format: <b>c_user=12345; xs=abcde...</b>)</p>
        
        <form id="extractForm">
            <textarea name="cookies" id="cookiesInput" placeholder="c_user=10001...; xs=xyz...&#10;c_user=10002...; xs=abc..." required></textarea>
            <button class="btn" type="submit">🔥 Start Extraction 🔥</button>
        </form>

        <h3 style="color: #00ff00;">[ LIVE DASHBOARD ]</h3>
        <div id="dashboard">
            <div class="log" style="color: #888;">Waiting for input...</div>
        </div>
    </div>

    <script>
        let currentTaskId = null;

        document.getElementById('extractForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const cookies = document.getElementById('cookiesInput').value;
            const dashboard = document.getElementById('dashboard');
            dashboard.innerHTML = '<div class="log" style="color: #ff00ff;">Starting process...</div>';

            fetch('/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'cookies=' + encodeURIComponent(cookies)
            })
            .then(res => res.json())
            .then(data => {
                if(data.task_id) {
                    currentTaskId = data.task_id;
                    pollLogs();
                }
            });
        });

        function pollLogs() {
            if(!currentTaskId) return;
            
            fetch('/logs/' + currentTaskId)
            .then(res => res.json())
            .then(data => {
                if(data.logs) {
                    const dashboard = document.getElementById('dashboard');
                    dashboard.innerHTML = '';
                    data.logs.forEach(log => {
                        const div = document.createElement('div');
                        div.className = 'log ' + (log.type || '');
                        div.innerHTML = log.text;
                        dashboard.appendChild(div);
                    });
                    dashboard.scrollTop = dashboard.scrollHeight; // Auto-scroll
                }
                
                if(data.status === 'running') {
                    setTimeout(pollLogs, 1000); // Poll every second
                }
            });
        }
    </script>
</body>
</html>
"""

def add_log(task_id, text, type=""):
    if task_id in tasks:
        tasks[task_id]['logs'].append({"text": text, "type": type})

def extract_real_token(cookie):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie
    }
    
    try:
        # Method 1: Ads Manager se token nikalna
        r = requests.get("https://www.facebook.com/adsmanager/manage/campaigns?act=0", headers=headers, timeout=15)
        if "login" in r.url or "checkpoint" in r.url:
            return None, "Cookie Expired ya Account Locked hai."
        
        # HTML me accessToken search karna
        token_match = re.search(r'"accessToken":"(EAAAA[A-Za-z0-9_-]+)"', r.text)
        if token_match:
            return token_match.group(1), "Success (Ads Manager)"
            
        # Method 2: Business Suite se token nikalna (Agar ads manager fail ho)
        r2 = requests.get("https://business.facebook.com/business_asset_management/", headers=headers, timeout=15)
        token_match2 = re.search(r'"accessToken":"(EAAAA[A-Za-z0-9_-]+)"', r2.text)
        if token_match2:
            return token_match2.group(1), "Success (Business Suite)"
            
        return None, "Token nahi mila. Facebook ne shayad UI change kar diya hai."
    except Exception as e:
        return None, f"Network Error: {str(e)}"

def process_cookies(task_id, cookie_text):
    lines = [line.strip() for line in cookie_text.split('\n') if line.strip()]
    total = len(lines)
    add_log(task_id, f"Total {total} cookies mili. Process shuru ho raha hai...", "success")
    
    for index, line in enumerate(lines, 1):
        # Extract UID
        uid_match = re.search(r'c_user=(\d+)', line)
        uid = uid_match.group(1) if uid_match else "Unknown"
        
        add_log(task_id, f"[{index}/{total}] Processing UID: {uid}...")
        
        token, msg = extract_real_token(line)
        
        if token:
            add_log(task_id, f"✅ UID {uid} ka Token mil gaya! ({msg})", "success")
            add_log(task_id, f"{token}", "token-box")
        else:
            add_log(task_id, f"❌ UID {uid} fail: {msg}", "error")
            
        time.sleep(1.5) # Delay taaki Facebook rate-limit na mare
        
    add_log(task_id, "✅ Saare cookies process ho gaye!", "success")
    tasks[task_id]['status'] = 'completed'

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/start", methods=["POST"])
def start():
    cookie_text = request.form.get("cookies").strip()
    if not cookie_text:
        return jsonify({"error": "No cookies provided"}), 400
        
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"logs": [], "status": "running"}
    
    # Background thread me process start karo
    threading.Thread(target=process_cookies, args=(task_id, cookie_text), daemon=True).start()
    
    return jsonify({"task_id": task_id})

@app.route("/logs/<task_id>")
def get_logs(task_id):
    if task_id in tasks:
        return jsonify(tasks[task_id])
    return jsonify({"logs": [], "status": "not_found"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
