import feedparser
import pymongo
from datetime import datetime
import os

# MongoDB connection using environment variable
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = pymongo.MongoClient(mongo_uri)
db = client["security_updates"]
collection = db["updates"]

# Rest of the script remains the same...

# List of RSS feeds to check
feeds = [
    "https://www.microsoft.com/en-us/msrc/rss/security-advisories",
    "https://www.cisco.com/warp/public/146/news_cisco/rss/Security_Advisory.xml",
    # Add more feeds as needed
]

def fetch_and_store_updates():
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
            collection.update_one(
                {"link": update["link"]},
                {"$setOnInsert": update},
                upsert=True
            )

if __name__ == "__main__":
    fetch_and_store_updates()
