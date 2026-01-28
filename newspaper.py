import feedparser, smtplib, os, requests, urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# CONFIG
EMAIL_SENDER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
EMAIL_RECEIVER = EMAIL_SENDER 

TOPICS = {
    "INDIA": "India Business Politics Tech",
    "WORLD": "Global Economy World Events"
}

def ask_gemini(prompt):
    # Fixed URL and added safety settings to prevent "Unavailable" errors
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        
        if 'candidates' in res_json and res_json['candidates'][0].get('content'):
            text = res_json['candidates'][0]['content']['parts'][0]['text']
            return text.replace('**', '').replace('\n', '<br>')
        else:
            # This returns the actual error from Google to your email
            error_msg = res_json.get('error', {}).get('message', 'Safety block or Invalid Key')
            return f"<i>Editorial Note: {error_msg}</i>"
    except Exception as e:
        return f"<i>Connection Error: {str(e)}</i>"

def fetch_news(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    return [e.title for e in feed.entries[:8]]

def create_html():
    today = datetime.now().strftime("%A, %d %B %Y")
    market_data = ask_gemini("Summarize Nifty 50 and Sensex closing trends in 2 sentences.")
    
    html = f"""
    <div style="font-family: 'Georgia', serif; background-color: #f4f1ea; padding: 20px; color: #1a1a1a;">
        <div style="max-width: 700px; margin: auto; background: white; padding: 30px; border: 1px solid #ccc;">
            <div style="text-align: center; border-bottom: 3px solid black; padding-bottom: 10px;">
                <h1 style="font-size: 45px; margin: 0; font-family: 'Times New Roman', serif;">THE DAILY GAZETTE</h1>
                <div style="display: flex; justify-content: space-between; border-top: 1px solid black; margin-top: 5px; font-size: 12px; font-weight: bold;">
                    <span>VOL. I ... NO. 01</span><span>{today}</span><span>PRICE: FREE</span>
                </div>
            </div>
            <div style="background: #eee; padding: 10px; margin-top: 20px; border: 1px solid #ddd;">
                <h4 style="margin: 0; text-transform: uppercase; font-size: 11px;">Market Snapshot</h4>
                <p style="font-size: 13px; margin: 5px 0;">{market_data}</p>
            </div>
    """

    for section, query in TOPICS.items():
        headlines = fetch_news(query)
        prompt = f"Write 3 professional newspaper paragraphs for the {section} section based on these headlines: {headlines}. Paragraph 1: Politics. Paragraph 2: Business. Paragraph 3: Tech/Sports. No bullets."
        analysis = ask_gemini(prompt)
        
        img_url = "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=800" if section == "INDIA" else "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800"

        html += f"""
            <div style="margin-top: 30px;">
                <h2 style="border-bottom: 2px solid #333; padding-bottom: 5px;">{section} DESK</h2>
                <img src="{img_url}" style="width: 100%; border: 1px solid #000; margin-bottom: 15px;">
                <p style="font-size: 15px; line-height: 1.6; text-align: justify;">{analysis}</p>
            </div>
        """

    html += "</div></div>"
    return html

def main():
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not GEMINI_KEY:
        print("MISSING SECRETS!")
        return
        
    msg = MIMEMultipart()
    msg['Subject'] = f"The Daily Gazette: {datetime.now().strftime('%d %b')}"
    msg.attach(MIMEText(create_html(), 'html'))
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_SENDER, msg.as_string())

if __name__ == "__main__":
    main()
