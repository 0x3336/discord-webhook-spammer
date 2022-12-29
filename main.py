import os
from bs4 import BeautifulSoup
import requests
import time
import json

# Read the webhook URLs from the text file
webhook_urls_file = "webhooks.txt"
if not os.path.exists(webhook_urls_file):
    open(webhook_urls_file, "w").close()
with open(webhook_urls_file, "r") as f:
    webhook_urls = [line.strip() for line in f]

# Check the status of each webhook and remove any that are not valid (status 200) or not from Discord
valid_webhook_urls = []
for webhook_url in webhook_urls:
    # Check if the URL is from Discord
    if not (webhook_url.startswith("https://discord.com/") or webhook_url.startswith("https://ptb.discord.com/") or webhook_url.startswith("https://canary.discord.com/") or webhook_url.startswith("http://discord.com/") or webhook_url.startswith("http://ptb.discord.com/") or webhook_url.startswith("http://canary.discord.com/")):
        continue
    try:
        response = requests.get(webhook_url)
        if response.status_code == 200:
            if webhook_url not in valid_webhook_urls:
                valid_webhook_urls.append(webhook_url)
    except:
        continue

# Save the valid webhook URLs to the text file
with open(webhook_urls_file, "w") as f:
    for webhook_url in valid_webhook_urls:
        f.write(webhook_url + "\n")

# Print the username of each webhook
for webhook_url in valid_webhook_urls:
    response = requests.get(webhook_url)
    webhook_info = json.loads(response.content)
    print(f"Username of webhook: {webhook_info['name']}")

if not valid_webhook_urls:
    print("No valid webhook")

# Set the URL of the website to scrape
url = input("Enter the URL to scrape: ")

# Prompt the user for the custom message to send to the webhooks
message = input("Enter the message to send to the webhooks: ")

# Prompt the user for the number of times to loop
num_loops = int(input("Enter the number of times to loop: "))

# Prompt the user whether to download the files to the current directory
download_files = input("Do you want to download the files to the current directory? (y/n) ")


for i in range(num_loops):
    # Send an HTTP request to the website and get the response
    response = requests.get(url)

    # Parse the HTML content of the response
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all img elements on the page
    img_elements = soup.find_all("img")

    # Extract only the img elements that have a supported file type
    supported_img_elements = [img for img in img_elements if img.get("src") is not None and img.get("src").split("/")[-1].endswith((".jpg", ".png", ".jpeg"))]

    # Iterate through the list of supported img elements
    for img in supported_img_elements:
        # Get the src attribute of the img element, which contains the URL of the image file
        file_url = img.get("src")
        # Get the file name from the URL
        file_name = file_url.split("/")[-1]
        print(f"Downloading {file_name}...")
        try:
            # Download the file if requested
            if download_files.lower() == "y":
                response = requests.get(file_url, timeout=10)
                # Save the file to the current directory
                with open(file_name, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded {file_name}")
            # Send a message to all the Discord webhooks
            for webhook_url in webhook_urls:
                l = requests.post(webhook_url, json={
                    "content": message,
                    "embeds": [{
                        "title": file_name,
                        "image": {
                            "url": file_url
                        }
                    }]
                })
                # Rate limit check
                if l.status_code == 429:
                    js = l.json()
                    time.sleep(js['retry_after'])
                    print("Rate Limited... Retrying after " + str(js['retry_after']) + " seconds")
                else:
                    print(f"Sent {file_name} to the webhook")
        except:
            # If there was an error, skip the file
            print(f"Error downloading {file_name}")
            continue

# Prompt the user whether to delete the webhooks
delete_webhooks = input("Do you want to delete the webhooks? (y/n) ")

if delete_webhooks.lower() == "y":
    # Iterate through the list of webhook URLs
    for webhook_url in webhook_urls:
        # Send an HTTP DELETE request to delete the webhook
        requests.delete(webhook_url)
        print(f"Deleted webhook: {webhook_url}")