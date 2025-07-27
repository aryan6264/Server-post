from flask import Flask, request, render_template
import requests
from threading import Thread, Event
import uuid
import time
import random

app = Flask(__name__)
stop_event = Event()
comment_count = 0
session_id = str(uuid.uuid4())
is_commenting = False
token_status = "Unknown"

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept-Language': 'en-US,en;q=0.9',
}

def send_comments(tokens, post_id, prefix, interval, messages):
    global comment_count, token_status, is_commenting
    is_commenting = True
    while not stop_event.is_set():
        for token in tokens:
            for msg in messages:
                if stop_event.is_set():
                    break
                full_msg = f"{prefix} {msg}" if prefix else msg
                url = f"https://graph.facebook.com/v20.0/{post_id}/comments"
                params = {'access_token': token, 'message': full_msg}
                response = requests.post(url, data=params, headers=headers)
                if response.status_code == 200:
                    comment_count += 1
                    token_status = "✅ Valid"
                    print(f"[✅] Comment: {full_msg}")
                else:
                    token_status = f"❌ {response.status_code}"
                    print(f"[❌] Failed: {response.text}")
                time.sleep(max(interval, 120))  # 2 mins gap
    is_commenting = False

@app.route('/', methods=['GET', 'POST'])
def index():
    global comment_count, session_id, token_status, is_commenting
    if request.method == 'POST':
        stop_event.clear()
        comment_count = 0
        session_id = str(uuid.uuid4())
        tokens = request.files['tokenFile'].read().decode().splitlines()
        post_id = request.form['postId']
        prefix = request.form.get('prefix')
        interval = int(request.form['time'])
        messages = request.files['txtFile'].read().decode().splitlines()
        thread = Thread(target=send_comments, args=(tokens, post_id, prefix, interval, messages))
        thread.start()
    return render_template('index.html', comment_count=comment_count, session_id=session_id,
                           status="Running ✅" if is_commenting else "Stopped ❌")

@app.route('/stop', methods=['POST'])
def stop():
    stop_event.set()
    return "✅ Bot Stopped. Go back."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)