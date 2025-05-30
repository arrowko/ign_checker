import os
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set webhook URLs as environment variables
os.environ["DISCORD_FINAL_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1376640623297433671/s_W7LeSd-v9B-FWVD5GEHUArryJUy24T0ZCg4buAv3DbuQo60Rd7Ss9wks_osEzd8gO1"

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

def divide_and_conquer(usernames, request_data, max_workers=10):
    def increment_and_check():
        with lock:
            request_data["count"] += 1
            if request_data["count"] % 95 == 0:
                print("⏱️ Reached 95 requests, waiting 1 minute...")
                time.sleep(60)
            print(f"📡 Request #{request_data['count']}")

    def recursive_check(name_list):
        if not name_list:
            return []
        if len(name_list) == 1:
            result = check_username_individually(name_list[0])
            increment_and_check()
            return [result] if result else []

        if check_batch_usernames(name_list):
            increment_and_check()
            mid = len(name_list) // 2
            return recursive_check(name_list[:mid]) + recursive_check(name_list[mid:])
        else:
            increment_and_check()
            return []

    def threaded_check(usernames):
        confirmed = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_username_individually, u): u for u in usernames}
            for future in as_completed(futures):
                username = futures[future]
                result = future.result()
                increment_and_check()
                if result:
                    print(f"✅ Free: {username}")
                    confirmed.append(username)
                else:
                    print(f"❌ Taken: {username}")
        return confirmed

    midlevel = recursive_check(usernames)
    return threaded_check(midlevel)

def process_batch(batch_num, batch, confirmed_free_names, webhook_url, request_data):
    print(f"\n🔍 Checking batch {batch_num} with {len(batch)} usernames: {batch}")

    if check_batch_usernames(batch):
        with lock:
            request_data["count"] += 1
            if request_data["count"] % 95 == 0:
                print("⏱️ Reached 95 requests, waiting 1 minute...")
                time.sleep(60)
            print(f"📡 Request #{request_data['count']}")
        print(f"✅ Batch {batch_num} returned 500 - running divide and conquer for batch.")
        confirmed = divide_and_conquer(batch, request_data)
        if confirmed:
            with lock:
                confirmed_free_names.extend(confirmed)
            send_discord_notification(confirmed, webhook_url, batch_num)
    else:
        with lock:
            request_data["count"] += 1
            if request_data["count"] % 95 == 0:
                print("⏱️ Reached 95 requests, waiting 1 minute...")
                time.sleep(60)
            print(f"📡 Request #{request_data['count']}")
        print(f"❌ Batch {batch_num} did not return 500.")

def main_loop():
    input_file = "testsada.txt"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    batch_size = 20

    while True:
        all_usernames = read_usernames_from_file(input_file)
        total = len(all_usernames)
        confirmed_free_names = []
        request_data = {"count": 0}

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for batch_num, start_idx in enumerate(range(0, total, batch_size), start=1):
                batch = all_usernames[start_idx:start_idx + batch_size]
                futures.append(executor.submit(
                    process_batch, batch_num, batch, confirmed_free_names, webhook_url, request_data))

            for future in as_completed(futures):
                future.result()

        print("\n=== ✅ Loop Summary ===")
        print(f"🟩 Free usernames this loop: {len(confirmed_free_names)}")
        print(f"📝 List: {confirmed_free_names}")
        print("🔁 Restarting loop in 60 seconds...\n")
        time.sleep(60)  # Adjust delay between full loops as needed

if __name__ == "__main__":
    main_loop()
