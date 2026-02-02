import feedparser, smtplib, os, requests, urllib.parse, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# CONFIG
EMAIL_SENDER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# YOUR CUSTOM CATEGORIES
GEOS = ["INDIA", "WORLD"]
TOPICS = [
    "POLITICS", "ECONOMICS", "FINANCE & BUSINESS", "MARKETS", 
    "TECH & AUTOMOBILE", "ENTERTAINMENT", "LIFESTYLE", "TRAVEL", "SPORTS"
]

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload, timeout=60)
        res_json = response.json()
        if 'candidates' in res_json:
            text = res_json['candidates'][0]['content']['parts'][0]['text']
            # FIX: Convert Markdown **bold** to HTML <b>bold</b>
            text = re.sub(r'\*\*(.*?)\*\*', r'<b style="color:#000; font-size:18px;">\1</b>', text)
            return text.replace('\n', '<br>')
        return "Editorial details are being updated."
    except:
        return "Error connecting to AI newsroom."

def fetch_category_news(geo, topic):
    query = f"{geo} {topic}"
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    return [e.title for e in feed.entries[:3]]

def create_html():
    today = datetime.now().strftime("%A, %d %B %Y")
    
    html = f"""
    <div style="font-family: 'Georgia', serif; background-color: #f2f2f2; padding: 15px;">
        <div style="max-width: 850px; margin: auto; background: white; padding: 40px; border: 1px solid #333;">
            
            <div style="text-align: center; border-bottom: 4px double #000; padding-bottom: 10px; margin-bottom: 30px;">
                <h1 style="font-size: 50px; margin: 0; font-family: 'Times New Roman', serif; text-transform: uppercase;">The Daily Gazette</h1>
                <div style="border-top: 1px solid #000; margin-top: 5px; padding: 5px 0; font-weight: bold; font-size: 14px;">
                    {today.upper()} &nbsp; | &nbsp; FINAL EDITION
                </div>
            </div>
    """

    for geo in GEOS:
        html += f"""
        <div style='background: #1a1a1a; color: #fff; padding: 10px; font-size: 22px; margin-top: 40px; text-align: center; font-family: sans-serif; letter-spacing: 2px;'>
            {geo} DESK
        </div>"""
        
        for topic in TOPICS:
            headlines = fetch_category_news(geo, topic)
            if not headlines: continue

            # Refined prompt for cleaner HTML output
            prompt = f"""Act as a professional newspaper editor for {geo} {topic}. 
            For EACH headline below, write:
            1. The Headline in bold (use <b> tags).
            2. A 3-sentence expert analysis article.
            
            Headlines: {headlines}
            
            Format:
            <b>HEADLINE</b>
            ARTICLE TEXT
            <br><br>"""

            analysis_block = ask_gemini(prompt)

            html += f"""
            <div style="margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px;">
                <h2 style="color: #8B0000; font-size: 16px; border-bottom: 2px solid #8B0000; display: inline-block; margin-bottom: 15px; text-transform: uppercase;">{topic}</h2>
                <div style="font-size: 16px; line-height: 1.6; color: #222;">
                    {analysis_block}
                </div>
            </div>
            """

    html += "</div></div>"
    return html

def main():
    if not EMAIL_SENDER or not GEMINI_KEY: return
    msg = MIMEMultipart()
    msg['Subject'] = f"The Daily Gazette: {datetime.now().strftime('%d %b %Y')}"
    msg.attach(MIMEText(create_html(), 'html'))
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_SENDER, msg.as_string())

if __name__ == "__main__":
    main()
