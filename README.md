# News Automation 

This project is a complete automation pipeline that pulls news from top financial sources, generates social media posts using OpenAI GPT, creates image previews, and visualizes everything in a web dashboard.


## What It Does

1. **Fetches News:**
   - Sources: CNBC, Yahoo News, Financial Times, Bloomberg
   - Uses RSS scraping and BeautifulSoup for structured extraction

2. **Scores & Selects Top Stories:**
   - Each article is scored using mock engagement (likes, shares, comments)
   - Best 1-per-source is selected for posting

3. **Schedules for CRM Distribution:**
   - Auto-assigns each story to one of 3 daily CRM slots:
     - `08:30`, `12:30`, `17:30` IST

4. **Generates Social Media Posts:**
   - GPT-4o generates punchy, brand-styled captions (≤ 200 characters)

5. **Creates Images:**
   - Generates 512x512 gray square images with overlaid headlines
   - Saves in `/images/` folder with sanitized filenames

6. **Builds Dashboard:**
   - Outputs structured post data to `dashboard.json`
   - Renders cards with likes, shares, comments, time, and image preview


## Project Structure


NEWS_AUTOMATION/
├── images/                  # Generated news image cards
├── automation.log           # Log file for fetch + rewrite
├── dashboard.html           # Frontend dashboard (JS + CSS)
├── dashboard.json           # Data source for dashboard
├── fetch_News.py            # Main fetcher and CRM scheduler
├── reWrite.py               # GPT + image generator
├── final_posts.json         # Final post output with schedule
├── top_stories.json         # 1 top story per source
├── recent_stories.json      # All 5 stories per source
├── .env                     # Your OpenAI API key
└── README.md                # This documentation

## Setup Instructions

### 1. Install dependencies

pip install openai python-dotenv pillow feedparser beautifulsoup4


### 2. Add your OpenAI API key
Create a `.env` file:

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

### 3. Run the full pipeline

python fetch_News.py

This:
- Pulls stories
- Assigns CRM slot
- Triggers `rewrite.py`
- Generates posts, images, and dashboard


## View the Dashboard

To open the dashboard:

python -m http.server 8000

Then go to:

http://localhost:8000/dashboard.html


## Highlights

-  CRM slot assignment (auto: 08:30 / 12:30 / 17:30)
-  GPT-generated post copy (200 chars max)
-  Clean image previews with overlaid headlines
-  Slack/console alerts + retry handling (in fetch)
-  Static dashboard powered by JSON