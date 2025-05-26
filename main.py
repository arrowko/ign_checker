import os
import time
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

def read_usernames_from_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def read_blacklist(filename):
    if not os.path.exists(filename):
        return set()
    with open(filename, "r", encoding="utf-8") as f:
        return set(line.strip().lower() for line in f if line.strip())

def check_username(username):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={username}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 500:
            return username
    except requests.RequestException:
        pass
    return None

def check_usernames_concurrently(usernames, max_workers=10):
    total = len(usernames)
    free_names = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_username = {executor.submit(check_username, name): name for name in usernames}

        for i, future in enumerate(as_completed(future_to_username), start=1):
            username = future_to_username[future]
            result = future.result()
            if result:
                free_names.append(result)

    return free_names

def send_discord_notification(free_names, webhook_url, batch_number=None, final=False):
    if not webhook_url:
        return

    if not free_names and not final:
        return  # Don't notify empty batches unless it's final

    if final:
        title = f"✅ Final Username Report"
    else:
        title = f"🚨 @everyone Free Usernames Found (Batch {batch_number})!"

    message = f"**{title}**\n" + "\n".join(f"- `{name}`" for name in free_names)
    payload = {"content": message}

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code in (200, 204):
            print(f"{'Final' if final else 'Batch'} notification sent.")
        else:
            print(f"Discord webhook failed: HTTP {response.status_code}")
    except requests.RequestException as e:
        print(f"Discord webhook error: {e}")

def main():
    input_file = "99.txt"
    blacklist_file = "blacklist.txt"

    all_usernames = read_usernames_from_file(input_file)
    blacklist = read_blacklist(blacklist_file)

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    final_webhook_url = os.getenv("DISCORD_FINAL_WEBHOOK_URL")

    batch_size = 99
    run_duration = timedelta(hours=3)
    end_time = datetime.now() + run_duration

    batch_num = 1
    all_free_names = []

    print(f"Starting 3-hour loop... ({datetime.now().strftime('%H:%M:%S')})")

    while datetime.now() < end_time:
        usernames = read_usernames_from_file(input_file)
        usernames = [u for u in usernames if u.lower() not in blacklist]

        if not usernames:
            print("No usernames to check. Waiting 1 minute...")
            time.sleep(60)
            continue

        for start_idx in range(0, len(usernames), batch_size):
            batch_usernames = usernames[start_idx:start_idx + batch_size]
            print(f"\nBatch {batch_num}: checking {len(batch_usernames)} usernames...")

            free_names = check_usernames_concurrently(batch_usernames)
            batch_free = [name for name in free_names if name.lower() not in blacklist]

            if batch_free:
                all_free_names.extend(batch_free)

            send_discord_notification(batch_free, webhook_url, batch_number=batch_num)
            batch_num += 1

            time.sleep(60)  # short wait between batches

        print("Sleeping 1 minute before next batch cycle...")
        time.sleep(60)

    # After 3 hours:
    print("\n✅ Run complete. Sending final report...")
    send_discord_notification(all_free_names, final_webhook_url, final=True)

    print(f"Total free usernames found: {len(all_free_names)}")
    for name in all_free_names:
        print(f"- {name}")

if __name__ == "__main__":
    main()
