import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import textwrap
from datetime import datetime
import shutil
import re
import logging

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_social_post(story):
    prompt = "\n".join([
        "You are a social media assistant for a financial news brand.",
        "Your job is to turn a news story into a short social media post with:",
        "- A punchy hook",
        "- A brief summary (if needed)",
        "- A clear call-to-action",
        "Keep it under 200 characters. Brand tone is confident, clever, and professional.",
        "",
        "Title: {}".format(story['title']),
        "Subhead: {}".format(story.get('subhead', '')),
        "Source: {}".format(story['source']),
        "URL: {}".format(story['url'])
    ])

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional social media copywriter."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(" GPT error for '{}': {}".format(story['title'], e))
        return " GPT failed"



def generate_image_from_headline(headline, source=''):
    os.makedirs("images", exist_ok=True)

    safe_name = re.sub(r'[\\\\/:*?"<>|]', '', headline[:50])
    filename = safe_name.replace(" ", "_") + ".png"
    filepath = os.path.join("images", filename)

    img = Image.new("RGB", (512, 512), color="gray")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    wrapped_text = textwrap.wrap(headline, width=30)
    total_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in wrapped_text)
    y_start = (512 - total_height) // 2

    for line in wrapped_text:
        text_width = draw.textbbox((0, 0), line, font=font)[2]
        x = (512 - text_width) // 2
        draw.text((x, y_start), line, fill="white", font=font)
        y_start += draw.textbbox((0, 0), line, font=font)[3] + 5

    img.save(filepath)
    return filepath


if __name__ == "__main__":
    image_dir = "images"
    if os.path.exists(image_dir):
        shutil.rmtree(image_dir)
    os.makedirs(image_dir)
    try:
        with open("top_stories.json", "r", encoding="utf-8") as f:
            stories = json.load(f)
    except Exception as e:
        print(" Failed to load top_stories.json: {}".format(e))
        exit()

    final_output = []

    for story in stories:
        print("\n***************************")
        print("Source:", story['source'])
        print("Title:", story['title'])
        print("Subhead:", story.get('subhead', ''))
        print("URL:", story['url'])
        social_post = generate_social_post(story)
        image_asset = generate_image_from_headline(story['title'], story['source'])
        scheduled_time = story.get('scheduled_time', datetime.now().strftime("%Y-%m-%d %H:%M"))
        print(" Post:", social_post)
        print(" Image:", image_asset)

        final_output.append({
            "source": story['source'],
            "title": story['title'],
            "subhead": story.get('subhead', ''),
            "url": story['url'],
            "social_post": social_post,
            "image_asset": image_asset,
            "scheduled_time": scheduled_time,
            "engagement": story.get('engagement', {
                "likes": 0,
                "shares": 0,
                "comments": 0
            })
        })

    with open("final_posts.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print("\n All posts saved to final_posts.json")


def generate_dashboard():
    try:
        with open("final_posts.json", "r", encoding="utf-8") as f:
            posts = json.load(f)
        stats = []
        for post in posts:
            engagement = post.get("engagement", {})
            stats.append({
                "source": post["source"],
                "title": post["title"],
                "likes": engagement.get("likes", 0),
                "shares": engagement.get("shares", 0),
                "comments": engagement.get("comments", 0),
                "scheduled_time": post.get("scheduled_time"),
                "image": post["image_asset"],
                "post": post["social_post"]
            })
        with open("dashboard.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        logging.info(" dashboard.json created.")
    except Exception as e:
        logging.error("Dashboard generation failed: {}".format(e))

generate_dashboard()