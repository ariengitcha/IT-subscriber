import feedparser
import pymongo
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# MongoDB connection using environment variable
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = pymongo.MongoClient(mongo_uri)
db = client["security_updates"]
collection = db["updates"]

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')

# List of RSS feeds to check
feeds = [
    "https://api.msrc.microsoft.com/update-guide/rss",
    "https://sec.cloudapps.cisco.com/security/center/psirtrss20/CiscoSecurityAdvisory.xml",
    # Add more feeds as needed
]

def send_email(subject, body):
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = RECIPIENT_EMAIL
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(message)

def fetch_and_store_updates():
    new_updates = []
    for feed_url in feeds:
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries:
            update = {
                "title": entry.title,
                "link": entry.link,
                "summary": entry.summary,
                "published": datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z"),
                "vendor": feed.feed.title,
                "processed": False
            }
            
            # Insert only if the update doesn't already exist
            result = collection.update_one(
                {"link": update["link"]},
                {"$setOnInsert": update},
                upsert=True
            )
            
            if result.upserted_id:
                new_updates.append(update)
    
    # Always send an email for testing
    if True:  # Change this to 'if new_updates:' after testing
        subject = f"Security Update Check Run"
        body = "The security update check script has run. This is a test email."
        if new_updates:
            body += "\n\nNew updates were found:\n\n"
            for update in new_updates:
                body += f"Title: {update['title']}\n"
                body += f"Vendor: {update['vendor']}\n"
                body += f"Link: {update['link']}\n"
                body += f"Published: {update['published']}\n\n"
        else:
            body += "\n\nNo new updates were found."
        
        send_email(subject, body)

if __name__ == "__main__":
    fetch_and_store_updates()
