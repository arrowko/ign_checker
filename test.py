import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Set webhook URLs as environment variables
os.environ["DISCORD_FINAL_WEBHOOK_URL"] = "your_final_webhook_here"
os.environ["DISCORD_WEBHOOK_URL"] = "your_webhook_here"

lock = Lock()
request_counter = 0

def read_usernames_from_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def increment_request_count():
    global request_counter
    with lock:
        request_counter += 1
        if request_counter % 99 == 0:
            print("⏱️ Reached 99 requests, waiting 1 minute...")
            time.sleep(60)
        return request_counter

def check_batch_usernames(usernames_batch):
    joined_names = ",".join(usernames_batch)
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={joined_names}"
    try:
        response = requests.get(url, timeout=5)
        print(f"🌐 Batch response ({len(usernames_batch)}): {response.status_code}")
        increment_request_count()
        return response.status_code == 500
    except requests.RequestException as e:
        print(f"❌ Batch request error: {e}")
        increment_request_count()
        return False

def check_username_individually(username):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={username}"
    try:
        response = requests.get(url, timeout=5)
        increment_request_count()
        print(f"🔍 Checking {username} -> Status: {response.status_code}")
        return username if response.status_code == 500 else None
    except requests.RequestException:
        increment_request_count()
        return None

def send_discord_notification(free_names, webhook_url, batch_number):
    if not free_names or not webhook_url:
        return

    message = f"**🚨 @everyone Free Usernames Found (Batch {batch_number})!**\n" + "\n".join(f"- `{name}`" for name in free_names)
    payload = {"content": message}

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print(f"✅ Discord notification for batch {batch_number} sent successfully.")
        else:
            print(f"❌ Failed to send Discord notification: HTTP {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Error sending Discord notification: {e}")

def divide_and_conquer(usernames):
    if not usernames:
        return []

    if len(usernames) == 1:
        result = check_username_individually(usernames[0])
        return [result] if result else []

    if check_batch_usernames(usernames):
        mid = len(usernames) // 2
        return divide_and_conquer(usernames[:mid]) + divide_and_conquer(usernames[mid:])
    else:
        return []

def threaded_divide_and_conquer(usernames, max_workers=10):
    confirmed = []

    def process_chunk(chunk):
        return divide_and_conquer(chunk)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_chunk, [u]) for u in usernames]
        for future in as_completed(futures):
            result = future.result()
            if result:
                confirmed.extend(result)

    return confirmed

def main():
    input_file = "chcene.txt"
    all_usernames = read_usernames_from_file(input_file)
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    batch_size = 20
    total = len(all_usernames)
    confirmed_free_names = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for batch_num, start_idx in enumerate(range(0, total, batch_size), start=1):
            batch = all_usernames[start_idx:start_idx + batch_size]

            def process_batch(batch=batch, batch_num=batch_num):
                print(f"\n🔍 Checking batch {batch_num} with {len(batch)} usernames: {batch}")
                if check_batch_usernames(batch):
                    print(f"✅ Batch {batch_num} returned 500 - processing individually.")
                    confirmed = threaded_divide_and_conquer(batch)
                    if confirmed:
                        send_discord_notification(confirmed, webhook_url, batch_num)
                    return confirmed
                else:
                    print(f"❌ Batch {batch_num} did not return 500.")
                    return []

            futures.append(executor.submit(process_batch))

        for future in as_completed(futures):
            result = future.result()
            if result:
                confirmed_free_names.extend(result)

    print("\n=== ✅ Summary ===")
    print(f"🟩 Confirmed free usernames: {len(confirmed_free_names)}")
    print(f"📝 Confirmed list: {confirmed_free_names}")
    print("🎉 Done.")

if __name__ == "__main__":
    main()
