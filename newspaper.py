import feedparser, smtplib, os, requests, urllib.parse
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
    # Using the Lite model as per your update for better quota handling
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload, timeout=60)
        res_json = response.json()
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        return "Editorial details are being updated."
    except:
        return "Error connecting to AI newsroom."

def fetch_category_news(geo, topic):
    query = f"{geo} {topic}"
    encoded_query = urllib.parse.quote(query)
    # Fetching the most recent RSS results
    url = f"https://news.google.com/rss/search?q={encoded_query}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    # We take the top 3-4 most relevant stories per category
    return [e.title for e in feed.entries[:3]]

def create_html():
    today = datetime.now().strftime("%A, %d %B %Y")
    
    html = f"""
    <div style="font-family: 'Times New Roman', serif; background-color: #f2f2f2; padding: 15px;">
        <div style="max-width: 850px; margin: auto; background: white; padding: 40px; border: 1px solid #333; box-shadow: 5px 5px 15px rgba(0,0,0,0.1);">
            
            <div style="text-align: center; border-bottom: 4px double #000; padding-bottom: 10px; margin-bottom: 30px;">
                <h1 style="font-size: 50px; margin: 0; text-transform: uppercase; letter-spacing: -1px;">The Daily Gazette</h1>
                <div style="border-top: 1px solid #000; margin-top: 5px; padding: 5px 0; font-weight: bold; font-size: 14px;">
                    {today.upper()} &nbsp; | &nbsp; SPECIAL MULTI-TOPIC EDITION
                </div>
            </div>
    """

    for geo in GEOS:
        html += f"""
        <div style='background: #1a1a1a; color: #fff; padding: 8px; font-size: 22px; margin-top: 40px; text-align: center; font-family: sans-serif; letter-spacing: 2px;'>
            {geo} DESK
        </div>"""
        
        for topic in TOPICS:
            headlines = fetch_category_news(geo, topic)
            if not headlines: continue

            # Ask Gemini to write individual articles for each headline
            prompt = f"""You are a professional newspaper editor for the {geo} {topic} section. 
            I will give you a list of headlines. For EACH headline, you MUST provide:
            1. The exact Headline in bold.
            2. A 3 to 4 sentence summarized analysis article that explains the 'why' and the impact.
            
            Headlines to process: {headlines}
            
            Format strictly as:
            **HEADLINE**
            ARTICLE TEXT
            (Repeat for each)"""

            analysis_block = ask_gemini(prompt).replace('\n', '<br>')

            html += f"""
            <div style="margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 20px;">
                <h2 style="color: #8B0000; font-size: 20px; border-bottom: 2px solid #8B0000; display: inline-block; margin-bottom: 15px;">{topic}</h2>
                <div style="font-size: 16px; line-height: 1.6; color: #222;">
                    {analysis_block}
                </div>
            </div>
            """

    html += """
            <div style="text-align: center; margin-top: 50px; border-top: 1px solid #000; padding-top: 20px; font-size: 12px; font-style: italic; color: #555;">
                This newspaper is generated using Google Gemini 2.5-Flash-Lite & Google News RSS.
            </div>
        </div>
    </div>
    """
    return html

def main():
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not GEMINI_KEY:
        print("CRITICAL ERROR: Missing environment variables (Secrets).")
        return
        
    msg = MIMEMultipart()
    msg['Subject'] = f"The Daily Gazette: {datetime.now().strftime('%d %b %Y')}"
    msg['From'] = f"The Daily Gazette <{EMAIL_SENDER}>"
    msg['To'] = EMAIL_SENDER
    msg.attach(MIMEText(create_html(), 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Newspaper successfully dispatched to your inbox.")
    except Exception as e:
        print(f"SMTP Error: {e}")

if __name__ == "__main__":
    main()
