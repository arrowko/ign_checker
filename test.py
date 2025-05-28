import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ["DISCORD_FINAL_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1376640623297433671/s_W7LeSd-v9B-FWVD5GEHUArryJUy24T0ZCg4buAv3DbuQo60Rd7Ss9wks_osEzd8gO1"
os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1373286716504277002/3a8I20YEVadrZXGK_W3AcPB4v01d5walWIIySGwl6Xf-rdnpTm52XKNE3sr7HmfOY6OF"


def read_usernames_from_file(filename):
    usernames = []
    with open(filename, "r", encoding="utf-8") as f:
        usernames = [line.strip() for line in f if line.strip()]
    return usernames

def check_usernames_batch(usernames_batch):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={','.join(usernames_batch)}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            taken_profiles = response.json()
            taken_names = {profile["username"] for profile in taken_profiles}
            free_names = [name for name in usernames_batch if name not in taken_names]
            return free_names
        elif response.status_code == 500:
            # If entire batch fails, assume all free (use with caution)
            return usernames_batch
    except requests.RequestException:
        pass
    return []

def check_usernames_concurrently(usernames, max_workers=10):
    total = len(usernames)
    free_names = []
    print(f"Checking {total} usernames with {max_workers} threads (in batches of 20)...\n")

    # Split usernames into batches of 20
    batches = [usernames[i:i + 20] for i in range(0, len(usernames), 20)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_batch = {executor.submit(check_usernames_batch, batch): batch for batch in batches}

        for i, future in enumerate(as_completed(future_to_batch), start=1):
            batch = future_to_batch[future]
            progress = (i / len(batches)) * 100
            print(f"[{i}/{len(batches)}] ({progress:.2f}%) Checked batch: {', '.join(batch)}", end='\r')

            result = future.result()
            if result:
                free_names.extend(result)

    print()
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
   
    input_file = "99.txt"  # <--- Change this to your txt filename
    all_usernames = read_usernames_from_file(input_file)
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    batch_size = 99
    total = len(all_usernames)
    all_free_names = []

    for batch_num, start_idx in enumerate(range(0, total, batch_size  ), start=1):
        batch_usernames = all_usernames[start_idx:start_idx + batch_size]
        print(f"\nProcessing batch {batch_num} with {len(batch_usernames)} usernames...")
    

        free_names = check_usernames_concurrently(batch_usernames)
        if free_names:
            all_free_names.extend(free_names)

        send_discord_notification(free_names, webhook_url, batch_num)

        # If not the last batch, wait 2 minutes before next batch
        if start_idx + batch_size < total:
            print("Waiting 1 minutes before next batch to avoid hitting API rate limits...\n")
            time.sleep(60)

    print("\n=== All batches processed ===")
    print(f"Total free usernames found: {len(all_free_names)}")
    if all_free_names:
        print("All free usernames:")
        for name in all_free_names:
            print(f"- {name}")

if __name__ == "__main__":
    main()
