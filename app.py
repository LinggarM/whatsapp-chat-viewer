from flask import Flask, render_template_string, request
import re
from datetime import datetime

app = Flask(__name__)

def parse_whatsapp_chat(text):
    messages = []
    pattern = r'^(\d{2}/\d{2}/\d{2,4})\s+(\d{2}[\.\:]\d{2})(?:\s+-\s+|\s+)([^:]+?):\s+(.+?)(?=(?:\d{2}/\d{2}/\d{2,4}\s+\d{2}[\.\:]\d{2})|$)'
    system_pattern = r'^(\d{2}/\d{2}/\d{2,4})\s+(\d{2}[\.\:]\d{2})\s+-\s+(.+?)(?=(?:\d{2}/\d{2}/\d{2,4}\s+\d{2}[\.\:]\d{2})|$)'
    
    lines = text.strip().split('\n')
    current_msg = None
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_msg:
                current_msg['content'] += '\n'
            continue
        
        msg_match = re.match(r'^(\d{2}/\d{2}/\d{2,4})\s+(\d{2}[\.\:]\d{2})\s+-\s+(.+?):\s+(.*)', line)
        sys_match = re.match(r'^(\d{2}/\d{2}/\d{2,4})\s+(\d{2}[\.\:]\d{2})\s+-\s+(.+?)$', line) if not msg_match else None
        
        if msg_match:
            if current_msg:
                messages.append(current_msg)
            date_str, time_str, sender, content = msg_match.groups()
            time_str = time_str.replace('.', ':')
            current_msg = {
                'date': date_str,
                'time': time_str,
                'sender': sender.strip(),
                'content': content.strip(),
                'type': 'message'
            }
        elif sys_match:
            if current_msg:
                messages.append(current_msg)
                current_msg = None
            date_str, time_str, content = sys_match.groups()
            time_str = time_str.replace('.', ':')
            messages.append({
                'date': date_str,
                'time': time_str,
                'sender': None,
                'content': content.strip(),
                'type': 'system'
            })
        else:
            if current_msg:
                current_msg['content'] += '\n' + line
    
    if current_msg:
        messages.append(current_msg)
    
    return messages

def group_by_date(messages):
    groups = {}
    for msg in messages:
        date = msg['date']
        if date not in groups:
            groups[date] = []
        groups[date].append(msg)
    return groups

def get_senders(messages):
    senders = list(set(m['sender'] for m in messages if m['sender']))
    return senders

def format_content(content):
    content = content.strip()
    media_patterns = [
        '<Media tidak disertakan>',
        'Pesan ini dihapus',
        'Anda menghapus pesan ini',
        '<Pesan ini diedit>',
    ]
    for p in media_patterns:
        if p in content:
            return content, True
    url_pattern = re.compile(r'(https?://[^\s]+)')
    formatted = url_pattern.sub(r'<a href="\1" target="_blank" rel="noopener">\1</a>', content)
    formatted = formatted.replace('\n', '<br>')
    return formatted, False

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WhatsApp Chat Viewer</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: #111b21;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .app-wrapper {
    width: 100%;
    max-width: 900px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: #0b141a;
  }

  /* Upload screen */
  .upload-screen {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 24px;
    padding: 40px 20px;
  }
  .upload-icon {
    width: 80px; height: 80px;
    border-radius: 50%;
    background: #00a884;
    display: flex; align-items: center; justify-content: center;
  }
  .upload-icon svg { width: 44px; height: 44px; fill: white; }
  .upload-title { font-size: 22px; font-weight: 600; color: #e9edef; }
  .upload-sub { font-size: 14px; color: #8696a0; text-align: center; max-width: 320px; line-height: 1.6; }
  
  .upload-area {
    border: 2px dashed #2a3942;
    border-radius: 16px;
    padding: 40px 60px;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
    background: #1f2c34;
    width: 100%; max-width: 480px;
  }
  .upload-area:hover, .upload-area.drag { border-color: #00a884; background: #1a2e25; }
  .upload-area p { color: #8696a0; font-size: 14px; margin-top: 8px; }
  .upload-area strong { color: #e9edef; }
  
  .or-divider { color: #8696a0; font-size: 13px; display: flex; align-items: center; gap: 12px; width: 100%; max-width: 480px; }
  .or-divider::before, .or-divider::after { content: ''; flex: 1; height: 1px; background: #2a3942; }
  
  textarea.paste-area {
    width: 100%; max-width: 480px;
    height: 160px;
    background: #1f2c34;
    border: 1px solid #2a3942;
    border-radius: 12px;
    color: #e9edef;
    font-size: 13px;
    padding: 14px;
    resize: vertical;
    outline: none;
    font-family: monospace;
    transition: border-color 0.2s;
  }
  textarea.paste-area:focus { border-color: #00a884; }
  textarea.paste-area::placeholder { color: #8696a0; }
  
  .btn-primary {
    background: #00a884;
    color: white;
    border: none;
    border-radius: 24px;
    padding: 12px 36px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s, transform 0.1s;
  }
  .btn-primary:hover { background: #06cf9c; }
  .btn-primary:active { transform: scale(0.97); }

  /* Chat screen */
  .chat-screen { display: flex; flex-direction: column; height: 100vh; }
  
  .chat-header {
    background: #1f2c34;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-bottom: 1px solid #2a3942;
    position: sticky; top: 0; z-index: 10;
  }
  .back-btn {
    background: none; border: none; cursor: pointer;
    color: #aebac1; font-size: 22px; line-height: 1;
    padding: 4px; border-radius: 50%;
    transition: background 0.2s;
  }
  .back-btn:hover { background: #2a3942; }
  
  .chat-avatar {
    width: 40px; height: 40px; border-radius: 50%;
    background: #6b7c85;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; color: white; font-weight: 500; flex-shrink: 0;
  }
  .chat-info { flex: 1; min-width: 0; }
  .chat-info .name { font-size: 16px; font-weight: 600; color: #e9edef; }
  .chat-info .members { font-size: 12px; color: #8696a0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  
  .chat-search {
    background: #2a3942;
    border: none;
    border-radius: 20px;
    padding: 6px 14px;
    color: #e9edef;
    font-size: 13px;
    outline: none;
    width: 180px;
    transition: width 0.2s;
  }
  .chat-search:focus { width: 240px; }
  .chat-search::placeholder { color: #8696a0; }

  .chat-body {
    flex: 1;
    overflow-y: auto;
    padding: 12px 16px;
    background-image: url("data:image/svg+xml,%3Csvg width='40' height='40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0h40v40H0z' fill='%230b141a'/%3E%3C/svg%3E");
    scroll-behavior: smooth;
  }
  
  .date-divider {
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 16px 0 8px;
  }
  .date-divider span {
    background: #1f2c34;
    color: #8696a0;
    font-size: 12px;
    padding: 5px 12px;
    border-radius: 8px;
    border: 1px solid #2a3942;
  }
  
  .system-msg {
    display: flex;
    justify-content: center;
    margin: 4px 0;
  }
  .system-msg span {
    background: #1f2c34;
    color: #8696a0;
    font-size: 12px;
    padding: 5px 12px;
    border-radius: 8px;
    max-width: 80%;
    text-align: center;
    border: 1px solid #2a3942;
  }
  
  .msg-row {
    display: flex;
    margin: 2px 0;
    align-items: flex-end;
    gap: 6px;
  }
  .msg-row.outgoing { flex-direction: row-reverse; }
  .msg-row.incoming { flex-direction: row; }
  
  .msg-row + .msg-row.outgoing.new-sender,
  .msg-row + .msg-row.incoming.new-sender {
    margin-top: 10px;
  }
  
  .mini-avatar {
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 600; flex-shrink: 0;
    color: white;
  }
  .mini-avatar.hidden { visibility: hidden; }
  
  .bubble {
    max-width: 65%;
    padding: 7px 10px 6px;
    border-radius: 7.5px;
    font-size: 14.2px;
    line-height: 1.5;
    word-break: break-word;
    position: relative;
  }
  
  .bubble.outgoing {
    background: #005c4b;
    color: #e9edef;
    border-top-right-radius: 2px;
  }
  .bubble.incoming {
    background: #1f2c34;
    color: #e9edef;
    border-top-left-radius: 2px;
  }
  
  .bubble.tail-outgoing::after {
    content: '';
    position: absolute;
    right: -8px; top: 0;
    width: 0; height: 0;
    border-left: 8px solid #005c4b;
    border-bottom: 8px solid transparent;
  }
  .bubble.tail-incoming::before {
    content: '';
    position: absolute;
    left: -8px; top: 0;
    width: 0; height: 0;
    border-right: 8px solid #1f2c34;
    border-bottom: 8px solid transparent;
  }
  
  .sender-name {
    font-size: 12.5px;
    font-weight: 600;
    margin-bottom: 2px;
  }
  
  .bubble-meta {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 4px;
    margin-top: 2px;
  }
  .bubble-time {
    font-size: 11px;
    color: #8696a0;
    white-space: nowrap;
  }
  .outgoing .bubble-time { color: #8696a0; }
  
  .bubble a { color: #53bdeb; text-decoration: none; }
  .bubble a:hover { text-decoration: underline; }
  
  .media-placeholder {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #8696a0;
    font-size: 13px;
    font-style: italic;
  }
  .media-placeholder svg { width: 18px; height: 18px; fill: #8696a0; flex-shrink: 0; }
  
  .deleted-msg { color: #8696a0 !important; font-style: italic; }
  
  .highlight { background: #ffd60a; color: #111; border-radius: 2px; }
  
  /* Scrollbar */
  .chat-body::-webkit-scrollbar { width: 6px; }
  .chat-body::-webkit-scrollbar-track { background: transparent; }
  .chat-body::-webkit-scrollbar-thumb { background: #2a3942; border-radius: 3px; }
  
  /* Sender colors */
  .color-0 { background: #df7daa; }
  .color-1 { background: #fd7e14; }
  .color-2 { background: #6ea9d7; }
  .color-3 { background: #56b4e9; }
  .color-4 { background: #e6a817; }
  .color-5 { background: #20c997; }
  .color-6 { background: #6f42c1; }
  .color-7 { background: #dc3545; }
  
  .sname-0 { color: #e39fc0; }
  .sname-1 { color: #f0a265; }
  .sname-2 { color: #7fbde0; }
  .sname-3 { color: #7ccef8; }
  .sname-4 { color: #f5c97a; }
  .sname-5 { color: #49cfad; }
  .sname-6 { color: #9b72d5; }
  .sname-7 { color: #e67070; }
  
  .msg-count-badge {
    background: #00a884;
    color: white;
    font-size: 11px;
    padding: 1px 6px;
    border-radius: 10px;
    margin-left: 6px;
  }
  
  @media (max-width: 600px) {
    .bubble { max-width: 85%; }
    .chat-search { width: 120px; }
    .chat-search:focus { width: 160px; }
  }
</style>
</head>
<body>
<div class="app-wrapper">

{% if not messages %}
<!-- Upload Screen -->
<div class="upload-screen">
  <div class="upload-icon">
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M20.52 3.449C18.24 1.245 15.24 0 12 0 5.373 0 0 5.373 0 12c0 2.117.555 4.188 1.61 6.007L0 24l6.137-1.61A11.943 11.943 0 0 0 12 24c6.627 0 12-5.373 12-12 0-3.24-1.245-6.279-3.48-8.551zM12 22c-1.851 0-3.656-.498-5.23-1.44l-.375-.222-3.885 1.02 1.036-3.774-.244-.387A9.944 9.944 0 0 1 2 12c0-5.514 4.486-10 10-10s10 4.486 10 10-4.486 10-10 10zm5.49-7.488c-.3-.15-1.775-.876-2.05-.976-.274-.1-.474-.15-.674.15-.2.299-.774.976-.95 1.175-.174.2-.349.224-.648.075-.3-.15-1.265-.466-2.41-1.486-.89-.795-1.491-1.776-1.666-2.076-.175-.299-.018-.46.131-.61.135-.134.3-.349.449-.524.15-.174.199-.299.299-.499.1-.199.05-.374-.025-.524-.075-.149-.674-1.624-.924-2.224-.244-.586-.49-.506-.674-.516l-.574-.01c-.199 0-.524.075-.8.374-.274.3-1.05 1.025-1.05 2.5s1.075 2.9 1.225 3.1c.15.199 2.113 3.227 5.12 4.524.716.308 1.274.492 1.71.63.716.227 1.37.195 1.885.118.575-.086 1.775-.726 2.025-1.425.25-.7.25-1.3.175-1.424-.075-.125-.275-.2-.575-.35z"/>
    </svg>
  </div>
  <div class="upload-title">WhatsApp Chat Viewer</div>
  <div class="upload-sub">Upload file ekspor chat WhatsApp (.txt) atau paste teks langsung di bawah</div>
  
  <form method="POST" enctype="multipart/form-data" id="mainForm">
    <div class="upload-area" id="dropZone" onclick="document.getElementById('fileInput').click()">
      <input type="file" id="fileInput" name="file" accept=".txt" style="display:none" onchange="this.form.submit()">
      <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#00a884" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="12" y1="18" x2="12" y2="12"/>
        <polyline points="9 15 12 12 15 15"/>
      </svg>
      <p style="margin-top: 12px;"><strong>Klik untuk upload</strong></p>
      <p>atau drag & drop file .txt di sini</p>
    </div>
    
    <div class="or-divider">atau</div>
    
    <textarea class="paste-area" name="text" placeholder="Paste teks chat WhatsApp di sini...&#10;&#10;Contoh format:&#10;03/06/24 12.46 - Nama: Pesan..."></textarea>
    <br><br>
    <div style="display:flex; justify-content:center;">
      <button type="submit" class="btn-primary">Lihat Chat</button>
    </div>
  </form>
</div>

{% else %}
<!-- Chat Screen -->
<div class="chat-screen">
  <div class="chat-header">
    <form method="POST" style="display:contents">
      <button type="submit" name="reset" class="back-btn" title="Kembali">&#8592;</button>
    </form>
    <div class="chat-avatar">💬</div>
    <div class="chat-info">
      <div class="name">Chat WhatsApp
        <span class="msg-count-badge">{{ messages|length }} pesan</span>
      </div>
      <div class="members">{{ senders|join(', ') }}</div>
    </div>
    <input type="text" class="chat-search" placeholder="🔍 Cari..." id="searchInput" oninput="searchMessages(this.value)">
  </div>
  
  <div class="chat-body" id="chatBody">
    {% set my_sender = senders[-1] if senders else '' %}
    {% set prev_date = namespace(v='') %}
    {% set prev_sender = namespace(v='') %}
    
    {% for msg in messages %}
      {% if msg.date != prev_date.v %}
        <div class="date-divider">
          <span>{{ msg.date }}</span>
        </div>
        {% set prev_date.v = msg.date %}
        {% set prev_sender.v = '' %}
      {% endif %}
      
      {% if msg.type == 'system' %}
        <div class="system-msg" data-content="{{ msg.content|lower }}">
          <span>{{ msg.content }}</span>
        </div>
        {% set prev_sender.v = '' %}
        
      {% else %}
        {% set is_outgoing = (msg.sender == my_sender) %}
        {% set sender_idx = senders.index(msg.sender) % 8 if msg.sender in senders else 0 %}
        {% set is_new_sender = (msg.sender != prev_sender.v) %}
        
        <div class="msg-row {{ 'outgoing' if is_outgoing else 'incoming' }} {{ 'new-sender' if is_new_sender else '' }}"
             data-content="{{ msg.content|lower }} {{ msg.sender|lower }}">
          
          {% if not is_outgoing %}
            {% if is_new_sender %}
              <div class="mini-avatar color-{{ sender_idx }}">{{ msg.sender[0]|upper }}</div>
            {% else %}
              <div class="mini-avatar hidden"></div>
            {% endif %}
          {% endif %}
          
          <div class="bubble {{ 'outgoing' if is_outgoing else 'incoming' }} {{ 'tail-outgoing' if (is_outgoing and is_new_sender) else '' }} {{ 'tail-incoming' if (not is_outgoing and is_new_sender) else '' }}">
            
            {% if not is_outgoing and is_new_sender and senders|length > 1 %}
              <div class="sender-name sname-{{ sender_idx }}">{{ msg.sender }}</div>
            {% endif %}
            
            {% if '<Media tidak disertakan>' in msg.content %}
              <div class="media-placeholder">
                <svg viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
                <em>Media tidak disertakan</em>
              </div>
            {% elif 'pesan ini dihapus' in msg.content|lower or 'anda menghapus pesan ini' in msg.content|lower %}
              <span class="deleted-msg">🚫 {{ msg.content }}</span>
            {% else %}
              {{ msg.content_html|safe }}
            {% endif %}
            
            <div class="bubble-meta">
              <span class="bubble-time">{{ msg.time }}</span>
              {% if is_outgoing %}
                <svg width="16" height="11" viewBox="0 0 16 11" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11.071.653l-5.833 5.834-2.476-2.476-.943.943 3.419 3.419 6.776-6.777-.943-.943z" fill="#53bdeb"/>
                  <path d="M15.071.653l-5.833 5.834-1.476-1.476-.943.943 2.419 2.419 6.776-6.777-.943-.943z" fill="#53bdeb"/>
                </svg>
              {% endif %}
            </div>
          </div>
          
          {% if is_outgoing %}
            {% if is_new_sender %}
              <div class="mini-avatar color-{{ sender_idx }}">{{ msg.sender[0]|upper }}</div>
            {% else %}
              <div class="mini-avatar hidden"></div>
            {% endif %}
          {% endif %}
        </div>
        {% set prev_sender.v = msg.sender %}
      {% endif %}
    {% endfor %}
  </div>
</div>

<script>
window.onload = () => {
  const body = document.getElementById('chatBody');
  if (body) body.scrollTop = body.scrollHeight;
};

function searchMessages(q) {
  q = q.trim().toLowerCase();
  const rows = document.querySelectorAll('[data-content]');
  rows.forEach(el => {
    if (!q || el.dataset.content.includes(q)) {
      el.style.display = '';
      if (q) {
        el.querySelectorAll('.highlight').forEach(h => {
          h.outerHTML = h.textContent;
        });
        highlightText(el, q);
      }
    } else {
      el.style.display = 'none';
    }
  });
}

function highlightText(el, q) {
  const bubbles = el.querySelectorAll('.bubble');
  bubbles.forEach(b => {
    const walker = document.createTreeWalker(b, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(node => {
      const idx = node.textContent.toLowerCase().indexOf(q);
      if (idx > -1) {
        const span = document.createElement('span');
        span.innerHTML = node.textContent.substring(0, idx) +
          '<mark class="highlight">' + node.textContent.substring(idx, idx + q.length) + '</mark>' +
          node.textContent.substring(idx + q.length);
        node.parentNode.replaceChild(span, node);
      }
    });
  });
}

const dz = document.getElementById('dropZone');
if (dz) {
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
  dz.addEventListener('drop', e => {
    e.preventDefault(); dz.classList.remove('drag');
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      document.getElementById('fileInput').files = dt.files;
      document.getElementById('mainForm').submit();
    }
  });
}
</script>
{% endif %}

</div>
</body>
</html>'''

@app.route('/', methods=['GET', 'POST'])
def index():
    messages = []
    senders = []
    
    if request.method == 'POST' and 'reset' not in request.form:
        text = ''
        
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            text = file.read().decode('utf-8', errors='ignore')
        elif request.form.get('text', '').strip():
            text = request.form['text']
        
        if text:
            messages = parse_whatsapp_chat(text)
            senders = get_senders(messages)
            
            for msg in messages:
                if msg['type'] == 'message':
                    html, is_special = format_content(msg['content'])
                    msg['content_html'] = html
    
    return render_template_string(HTML_TEMPLATE, messages=messages, senders=senders)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
