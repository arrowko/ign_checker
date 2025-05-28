import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/..."  # your webhook here

def read_usernames_from_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def check_batch(usernames_batch):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={','.join(usernames_batch)}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            taken_profiles = response.json()
            taken = {p["username"] for p in taken_profiles if isinstance(p, dict) and "username" in p}
            return [name for name in usernames_batch if name not in taken]
        elif response.status_code == 500:
            # API failed, return whole batch for later single recheck
            return None
    except requests.RequestException as e:
        print(f"Request error: {e}")
    return []

def recheck_individual(usernames):
    free = []
    for name in usernames:
        url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={name}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    free.append(name)
            elif response.status_code == 500:
                print(f"Still failed for: {name}")
        except requests.RequestException as e:
            print(f"Error on single recheck for {name}: {e}")
    return free

def send_discord_notification(free_names, batch_number):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not free_names or not webhook_url:
        return

    message = f"**🚨 Free Usernames Found (Batch {batch_number})!**\n" + "\n".join(f"- {name}" for name in free_names)
    payload = {"content": message}

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print(f"Notification sent for batch {batch_number}.")
        else:
            print(f"Failed to notify for batch {batch_number}. Code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error sending notification: {e}")

def main():
    input_file = "99.txt"
    all_usernames = read_usernames_from_file(input_file)
    batch_size = 20
    total = len(all_usernames)
    failed_batches = []
    all_free = []

    for i in range(0, total, batch_size):
        batch_num = (i // batch_size) + 1
        batch = all_usernames[i:i + batch_size]
        print(f"Checking batch {batch_num}: {batch}")

        result = check_batch(batch)
        if result is None:
            failed_batches.extend(batch)
        elif result:
            all_free.extend(result)
            send_discord_notification(result, batch_num)

        time.sleep(1)  # small delay to avoid hammering API

    print("\nRechecking failed batches individually...")
    individually_free = recheck_individual(failed_batches)
    if individually_free:
        all_free.extend(individually_free)
        send_discord_notification(individually_free, "Individual Retry")

    print("\n✅ Done. Total free usernames:", len(all_free))
    for name in all_free:
        print(f"- {name}")

if __name__ == "__main__":
    main()
