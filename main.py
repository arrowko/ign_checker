import os
import time
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ["DISCORD_FINAL_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1376640623297433671/s_W7LeSd-v9B-FWVD5GEHUArryJUy24T0ZCg4buAv3DbuQo60Rd7Ss9wks_osEzd8gO1"
os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1373286716504277002/3a8I20YEVadrZXGK_W3AcPB4v01d5walWIIySGwl6Xf-rdnpTm52XKNE3sr7HmfOY6OF"


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
    free_names = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_username = {executor.submit(check_username, name): name for name in usernames}
        for future in as_completed(future_to_username):
            result = future.result()
            if result:
                free_names.append(result)
    return free_names

def send_discord_notification(free_names, webhook_url, batch_number=None, final=False):
    if not webhook_url:
        return

    if not free_names and not final:
        return  # Don't send empty batch notifications

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

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    final_webhook_url = os.getenv("DISCORD_FINAL_WEBHOOK_URL")

    batch_size = 99
    run_duration = timedelta(hours=9)
    end_time = datetime.now() + run_duration

    batch_num = 1
    all_free_names = []

    print(f"Starting 3-hour continuous loop... ({datetime.now().strftime('%H:%M:%S')})")

    while datetime.now() < end_time:
        usernames = read_usernames_from_file(input_file)
        blacklist = read_blacklist(blacklist_file)
        usernames = [u for u in usernames if u.lower() not in blacklist]

        if not usernames:
            print("No usernames to check. Waiting 1 minute...")
            time.sleep(60)
            continue

        all_free_names_in_pass = []

        for start_idx in range(0, len(usernames), batch_size):
            batch_usernames = usernames[start_idx:start_idx + batch_size]
            print(f"\nBatch {batch_num}: checking {len(batch_usernames)} usernames...")

            free_names = check_usernames_concurrently(batch_usernames)
            batch_free = [name for name in free_names if name.lower() not in blacklist]

            if batch_free:
                all_free_names.extend(batch_free)
                all_free_names_in_pass.extend(batch_free)

            send_discord_notification(batch_free, webhook_url, batch_number=batch_num)
            batch_num += 1

            time.sleep(60)  # short wait between batches

        # Send final notification after completing full pass
        if all_free_names_in_pass:
            print(f"\nSending final notification for this pass (found {len(all_free_names_in_pass)} free names)...")
            send_discord_notification(all_free_names_in_pass, final_webhook_url, final=True)
        else:
            print("\nNo free names found this pass. Skipping final notification.")

        print("Sleeping 1 minute before next pass...")
        time.sleep(5)

    print("\n=== 3-hour run complete ===")
    print(f"Total free usernames found: {len(all_free_names)}")
    if all_free_names:
        print("All free usernames found during the run:")
        for name in all_free_names:
            print(f"- {name}")

if __name__ == "__main__":
    main()
