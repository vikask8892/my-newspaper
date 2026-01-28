import feedparser, smtplib, os, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Get keys from GitHub Vault
EMAIL_SENDER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

def ask_ai(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, json=payload)
    return r.json()['candidates'][0]['content']['parts'][0]['text'].replace('**', '').replace('\n', '<br>')

def get_news(q):
    f = feedparser.parse(f"https://news.google.com/rss/search?q={q}+when:1d&hl=en-IN&gl=IN&ceid=IN:en")
    return [e.title for e in f.entries[:8]]

def make_paper():
    date = datetime.now().strftime("%A, %d %B %Y")
    market = ask_ai("Summarize yesterday's Nifty and Sensex closing in 2 short lines.")
    
    html = f"<div style='font-family:serif;background:#f4f1ea;padding:20px;'><div style='max-width:600px;margin:auto;background:white;padding:20px;border:1px solid #000;'>"
    html += f"<h1 style='text-align:center;border-bottom:2px solid #000;'>THE DAILY GAZETTE</h1><p style='text-align:center;'>{date}</p>"
    html += f"<div style='background:#eee;padding:10px;'><b>Market:</b> {market}</div>"

    for sec, q in {"INDIA": "India News", "WORLD": "World News"}.items():
        news = get_news(q)
        analysis = ask_ai(f"Write 3 professional paragraphs about these headlines: {news}")
        html += f"<h2>{sec} DESK</h2><p>{analysis}</p><hr>"
    
    html += "</div></div>"
    return html

msg = MIMEMultipart()
msg['Subject'] = f"Daily Gazette - {datetime.now().strftime('%d %b')}"
msg.attach(MIMEText(make_paper(), 'html'))
with smtplib.SMTP('smtp.gmail.com', 587) as s:
    s.starttls()
    s.login(EMAIL_SENDER, EMAIL_PASSWORD)
    s.sendmail(EMAIL_SENDER, EMAIL_SENDER, msg.as_string())
