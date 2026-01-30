import feedparser, smtplib, os, requests, urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# CONFIG
EMAIL_SENDER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# CATEGORIES & GEOGRAPHIES
GEOS = ["INDIA", "WORLD"]
TOPICS = [
    "POLITICS", "ECONOMICS", "FINANCE & BUSINESS", "MARKETS", 
    "TECH & AUTOMOBILE", "ENTERTAINMENT", "LIFESTYLE", "TRAVEL", "SPORTS"
]

def ask_gemini(prompt):
    # Using 2.5-flash-lite for speed and reliability in 2026
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
    url = f"https://news.google.com/rss/search?q={encoded_query}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    # Get top 3 headlines per category
    return [e.title for e in feed.entries[:3]]

def create_html():
    today = datetime.now().strftime("%A, %d %B %Y")
    
    html = f"""
    <div style="font-family: 'Georgia', serif; background-color: #f0f0f0; padding: 10px;">
        <div style="max-width: 900px; margin: auto; background: white; padding: 40px; border: 2px solid #333;">
            
            <div style="text-align: center; border-bottom: 5px solid black; padding-bottom: 10px; margin-bottom: 20px;">
                <h1 style="font-size: 60px; margin: 0; font-family: 'Times New Roman', serif; text-transform: uppercase;">The Daily Gazette</h1>
                <p style="font-weight: bold; border-top: 1px solid black; padding-top: 5px;">{today} | Comprehensive Global Coverage</p>
            </div>
    """

    for geo in GEOS:
        html += f"<div style='background: #333; color: white; padding: 10px; font-size: 24px; margin-top: 30px; text-align: center;'>{geo} EDITION</div>"
        
        for topic in TOPICS:
            headlines = fetch_category_news(geo, topic)
            if not headlines: continue

            # Ask Gemini to process the whole category at once to save your quota
            prompt = f"""Act as a senior editor. For the following {topic} headlines in {geo}, provide a structured response.
            For EACH headline, write:
            1. The original Headline in bold.
            2. A 3-sentence professional analysis/summary.
            
            Headlines: {headlines}
            Format: Headline followed by analysis. Separate each story clearly."""

            analysis_block = ask_gemini(prompt).replace('\n', '<br>')

            html += f"""
            <div style="margin-top: 25px; border-left: 4px solid #cc0000; padding-left: 15px;">
                <h2 style="color: #cc0000; font-size: 18px; margin: 0; text-transform: uppercase;">{topic}</h2>
                <div style="font-size: 16px; line-height: 1.6; color: #111; margin-top: 10px;">
                    {analysis_block}
                </div>
            </div>
            """

    html += """
            <div style="text-align: center; margin-top: 50px; border-top: 2px solid black; padding-top: 20px; font-size: 12px; color: #666;">
                &copy; 2026 The Daily Gazette | Automated AI Reporting
            </div>
        </div>
    </div>
    """
    return html

def main():
    if not EMAIL_SENDER or not GEMINI_KEY:
        print("Configuration missing!")
        return
        
    msg = MIMEMultipart()
    msg['Subject'] = f"The Daily Gazette: {datetime.now().strftime('%d %b %Y')}"
    msg.attach(MIMEText(create_html(), 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_SENDER, msg.as_string())
        print("Success: Your full-edition newspaper has been sent.")
    except Exception as e:
        print(f"Failed to send: {e}")

if __name__ == "__main__":
    main()
