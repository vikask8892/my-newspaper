import feedparser, smtplib, os, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# CONFIG
EMAIL_SENDER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
EMAIL_RECEIVER = EMAIL_SENDER 

# TOPICS
TOPICS = {
    "INDIA": "India Finance OR Politics OR Tech OR Sports OR Travel",
    "WORLD": "Global Economy OR World Politics OR Tech News OR Global Sports"
}

def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.json()['candidates'][0]['content']['parts'][0]['text'].replace('**', '').replace('\n', '<br>')
    except: return "Analysis currently updating. Please check the source links below."

def fetch_news(query):
    feed = feedparser.parse(f"https://news.google.com/rss/search?q={query}+when:1d&hl=en-IN&gl=IN&ceid=IN:en")
    return [f"{e.title} (Source: {e.source.title})" for e in feed.entries[:8]]

def create_html():
    today = datetime.now().strftime("%A, %d %B %Y")
    
    # 1. Get AI Market Snapshot
    market_data = ask_gemini("Provide a 3-line brief bulleted summary of yesterday's Sensex, Nifty, and Global Market closing trends. Keep it very short.")
    
    html = f"""
    <div style="font-family: 'Georgia', serif; background-color: #f4f1ea; padding: 20px; color: #1a1a1a;">
        <div style="max-width: 700px; margin: auto; background: white; padding: 30px; border: 1px solid #ccc;">
            <div style="text-align: center; border-bottom: 3px solid black; padding-bottom: 10px;">
                <h1 style="font-size: 45px; margin: 0; font-family: 'Times New Roman', serif;">THE DAILY GAZETTE</h1>
                <div style="display: flex; justify-content: space-between; border-top: 1px solid black; margin-top: 5px; font-size: 12px; font-weight: bold;">
                    <span>VOL. I ... NO. 01</span><span>{today}</span><span>PRICE: 0.00</span>
                </div>
            </div>

            <div style="background: #eee; padding: 10px; margin-top: 20px; border: 1px solid #ddd;">
                <h4 style="margin: 0; text-transform: uppercase; font-size: 12px;">Market Intelligence Snapshot</h4>
                <p style="font-size: 13px; margin: 5px 0;">{market_data}</p>
            </div>
    """

    for section, query in TOPICS.items():
        headlines = fetch_news(query)
        # Ask AI to write the article
        prompt = f"Write a professional 3-paragraph news analysis for the '{section}' section based on these headlines: {headlines}. Paragraph 1: Politics & Economy. Paragraph 2: Tech & Lifestyle. Paragraph 3: Sports & Travel. Tone: Elegant, serious, newspaper-style. No bullet points."
        analysis = ask_gemini(prompt)
        
        # Image placeholder (High quality Unsplash)
        img_topic = "cityscape" if section == "WORLD" else "india"
        img_url = f"https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=800&q=80" if section == "INDIA" else "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80"

        html += f"""
            <div style="margin-top: 30px;">
                <h2 style="border-bottom: 2px solid #333; padding-bottom: 5px;">{section} DESK</h2>
                <img src="{img_url}" style="width: 100%; border: 1px solid #000; margin-bottom: 15px;">
                <p style="font-size: 16px; line-height: 1.6; text-align: justify; color: #333;">{analysis}</p>
            </div>
        """

    html += "</div></div>"
    return html

def main():
    msg = MIMEMultipart()
    msg['Subject'] = f"The Daily Gazette: {datetime.now().strftime('%d %b')}"
    msg.attach(MIMEText(create_html(), 'html'))
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    main()
