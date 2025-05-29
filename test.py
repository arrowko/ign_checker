import os
import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set webhook URLs as environment variables
os.environ["DISCORD_FINAL_WEBHOOK_URL"] = "your_webhook_1"
os.environ["DISCORD_WEBHOOK_URL"] = "your_webhook_2"

lock = threading.Lock()

def read_usernames_from_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def check_batch_usernames(usernames_batch):
    joined_names = ",".join(usernames_batch)
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={joined_names}"
    try:
        response = requests.get(url, timeout=5)
        print(f"🌐 Batch response ({len(usernames_batch)} usernames): {response.status_code}")
        return response.status_code == 500
    except requests.RequestException as e:
        print(f"❌ Batch request error: {e}")
        return False

def check_username_individually(username):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={username}"
    try:
        response = requests.get(url, timeout=5)
        print(f"🔍 Checking {username} -> Status: {response.status_code}")
        return username if response.status_code == 500 else None
    except requests.RequestException:
        return None

def send_discord_notification(free_names, webhook_url, batch_number):
    if not free_names or not webhook_url:
        return

    message = f"**🚨 @everyone Free Usernames Found (Batch {batch_number})!**\n" + "\n".join(f"- {name}" for name in free_names)
    payload = {"content": message}

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print(f"✅ Discord notification for batch {batch_number} sent successfully.")
        else:
            print(f"❌ Failed to send Discord notification: HTTP {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Error sending Discord notification: {e}")

def divide_and_conquer(usernames, request_counter, max_workers=10):
    def recursive_check(name_list):
        nonlocal request_counter
        if not name_list:
            return []

        if len(name_list) == 1:
            result = check_username_individually(name_list[0])
            with lock:
                request_counter += 1
                if request_counter % 99 == 0:
                    print("⏱️ Reached 99 requests, waiting 1 minute...")
                    time.sleep(60)
            return [result] if result else []

        if check_batch_usernames(name_list):
            with lock:
                request_counter += 1
                if request_counter % 99 == 0:
                    print("⏱️ Reached 99 requests, waiting 1 minute...")
                    time.sleep(60)
            mid = len(name_list) // 2
            return recursive_check(name_list[:mid]) + recursive_check(name_list[mid:])
        else:
            with lock:
                request_counter += 1
                if request_counter % 99 == 0:
                    print("⏱️ Reached 99 requests, waiting 1 minute...")
                    time.sleep(60)
            return []

    def threaded_check(usernames):
        nonlocal request_counter
        confirmed = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_username_individually, u): u for u in usernames}
            for future in as_completed(futures):
                username = futures[future]
                result = future.result()
                with lock:
                    request_counter += 1
                    if result:
                        print(f"📡 Request #{request_counter} - ✅ Free: {username}")
                        confirmed.append(username)
                    else:
                        print(f"📡 Request #{request_counter} - ❌ Taken: {username}")
                    if request_counter % 99 == 0:
                        print("⏱️ Reached 99 requests, waiting 1 minute...")
                        time.sleep(60)
        return confirmed

    midlevel = recursive_check(usernames)
    return threaded_check(midlevel), request_counter

def process_batch(batch_num, batch, request_counter, confirmed_free_names, webhook_url):
    print(f"\n🔍 Checking batch {batch_num} with {len(batch)} usernames: {batch}")

    if check_batch_usernames(batch):
        print(f"✅ Batch {batch_num} returned 500 - running divide and conquer for batch.")
        confirmed, updated_counter = divide_and_conquer(batch, request_counter)
        with lock:
            request_counter = updated_counter
            confirmed_free_names.extend(confirmed)
        if confirmed:
            send_discord_notification(confirmed, webhook_url, batch_num)
    else:
        print(f"❌ Batch {batch_num} did not return 500.")

    with lock:
        request_counter += 1
        print(f"📡 Request #{request_counter}")
        if request_counter % 99 == 0:
            print("⏱️ Reached 99 requests, waiting 1 minute...\n")
            time.sleep(60)

    return request_counter

def main():
    input_file = "chcene.txt"
    all_usernames = read_usernames_from_file(input_file)
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    batch_size = 20
    total = len(all_usernames)
    request_counter = 0
    confirmed_free_names = []

    futures = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        for batch_num, start_idx in enumerate(range(0, total, batch_size), start=1):
            batch = all_usernames[start_idx:start_idx + batch_size]
            futures.append(executor.submit(process_batch, batch_num, batch, request_counter, confirmed_free_names, webhook_url))

        for future in as_completed(futures):
            result = future.result()
            with lock:
                request_counter = max(request_counter, result)

    print("\n=== ✅ Summary ===")
    print(f"🟩 Confirmed free usernames: {len(confirmed_free_names)}")
    print(f"📝 Confirmed list: {confirmed_free_names}")
    print("🎉 Done.")

if __name__ == "__main__":
    main()
