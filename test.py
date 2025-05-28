import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1373286716504277002/3a8I20YEVadrZXGK_W3AcPB4v01d5walWIIySGwl6Xf-rdnpTm52XKNE3sr7HmfOY6OF"

def read_usernames_from_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def check_usernames_batch(usernames_batch):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={','.join(usernames_batch)}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            taken_profiles = response.json()
            taken_names = {
                profile.get("username") for profile in taken_profiles
                if isinstance(profile, dict) and "username" in profile
            }
            return [name for name in usernames_batch if name not in taken_names], []
        elif response.status_code == 500:
            return [], usernames_batch  # mark entire batch as suspicious
    except requests.RequestException as e:
        print(f"Request error for batch: {','.join(usernames_batch)} -> {e}")
    return [], []

def check_single_username(username):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={username}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 500:
            return username  # likely free
    except requests.RequestException:
        pass
    return None

def check_suspected_usernames(suspected_usernames):
    free_names = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_single_username, name): name for name in suspected_usernames}
        for future in as_completed(futures):
            result = future.result()
            if result:
                free_names.append(result)
    return free_names

def check_usernames(usernames, max_workers=10):
    total = len(usernames)
    free_names = []
    suspected_free = []

    print(f"Checking {total} usernames in batches of 20...\n")
    batches = [usernames[i:i + 20] for i in range(0, total, 20)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_usernames_batch, batch): batch for batch in batches}
        for i, future in enumerate(as_completed(futures), start=1):
            batch = futures[future]
            progress = (i / len(batches)) * 100
            print(f"[{i}/{len(batches)}] ({progress:.2f}%) Checked batch: {', '.join(batch)}", end='\r')

            free, suspected = future.result()
            free_names.extend(free)
            suspected_free.extend(suspected)

    print("\nNow checking suspected usernames individually...")
    free_from_suspected = check_suspected_usernames(suspected_free)
    free_names.extend(free_from_suspected)
    return free_names

def send_discord_notification(free_names, webhook_url, batch_number):
    if not free_names or not webhook_url:
        return
    message = f"**🚨 @everyone Free Usernames Found (Batch {batch_number})!**\n" + "\n".join(f"- `{name}`" for name in free_names)
    payload = {"content": message}
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print(f"Discord notification for batch {batch_number} sent successfully.")
        else:
            print(f"Failed to send Discord notification for batch {batch_number}: HTTP {response.status_code}")
    except requests.RequestException as e:
        print(f"Error sending Discord notification for batch {batch_number}: {e}")

def main():
    input_file = "99.txt"
    all_usernames = read_usernames_from_file(input_file)
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    batch_size = 99
    total = len(all_usernames)
    all_free_names = []

    for batch_num, start_idx in enumerate(range(0, total, batch_size), start=1):
        batch_usernames = all_usernames[start_idx:start_idx + batch_size]
        print(f"\nProcessing batch {batch_num} with {len(batch_usernames)} usernames...")

        free_names = check_usernames(batch_usernames)
        if free_names:
            all_free_names.extend(free_names)

        send_discord_notification(free_names, webhook_url, batch_num)

        if start_idx + batch_size < total:
            print("Waiting 1 minute before next batch to avoid hitting API rate limits...\n")
            time.sleep(60)

    print("\n=== All batches processed ===")
    print(f"Total free usernames found: {len(all_free_names)}")
    if all_free_names:
        print("All free usernames:")
        for name in all_free_names:
            print(f"- {name}")

if __name__ == "__main__":
    main()
