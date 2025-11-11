from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from transformers import pipeline
import time

def scrape_flipkart_short_reviews(product_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)

    driver.get(product_url)
    time.sleep(3)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    tags = []
    try:
        tag_elements = driver.find_elements(By.CLASS_NAME, "ZmyHeo")
        for tag_div in tag_elements:
            try:
                inner_text = tag_div.find_element(By.TAG_NAME, "div").text.strip()
                if inner_text:
                    tags.append(inner_text)
            except:
                continue
    except Exception as e:
        print("❌ Error:", e)

    driver.quit()
    return tags


def summarize_reviews_huggingface(tags):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    joined_text = ". ".join(tags)  # combine scraped tags
    if len(joined_text) < 50:
        return "Not enough content to summarize."

    summary = summarizer(joined_text, max_length=80, min_length=25, do_sample=False)
    return summary[0]["summary_text"]


# 🔁 TEST
flipkart_url = input("Paste Flipkart product review page URL: ").strip()
short_tags = scrape_flipkart_short_reviews(flipkart_url)

print(f"\n✅ Found {len(short_tags)} short review points:\n")
for i, tag in enumerate(short_tags, 1):
    print(f"{i}. {tag}")

# 🧠 Generate Summary
print("\n📌 Summary from Hugging Face BART:")
summary = summarize_reviews_huggingface(short_tags)
print(summary)
