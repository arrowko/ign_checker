import os
import time
import requests

os.environ["DISCORD_FINAL_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1376640623297433671/s_W7LeSd-v9B-FWVD5GEHUArryJUy24T0ZCg4buAv3DbuQo60Rd7Ss9wks_osEzd8gO1"
os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1373286716504277002/3a8I20YEVadrZXGK_W3AcPB4v01d5walWIIySGwl6Xf-rdnpTm52XKNE3sr7HmfOY6OF"

def read_usernames_from_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def check_batch_usernames(usernames_batch):
    # Join usernames comma-separated for API call
    joined_names = ",".join(usernames_batch)
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={joined_names}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 500:
            # All usernames in batch are free
            return True
        else:
            return False
    except requests.RequestException:
        return False

def check_username_individually(username):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={username}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 500:
            return True
        else:
            return False
    except requests.RequestException:
        return False

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

    batch_size = 20
    total = len(all_usernames)

    request_count = 0  # Track total API requests made
    potential_free_names = []

    for batch_num, start_idx in enumerate(range(0, total, batch_size), start=1):
        batch = all_usernames[start_idx:start_idx + batch_size]
        print(f"Checking batch {batch_num} with {len(batch)} usernames: {batch}")

        batch_is_free = check_batch_usernames(batch)
        request_count += 1

        if batch_is_free:
            print(f"Batch {batch_num} returned 500 - adding all {len(batch)} usernames to potential free list.")
            potential_free_names.extend(batch)
        else:
            print(f"Batch {batch_num} did not return 500.")

        # Wait after every 99 requests
        if request_count % 99 == 0:
            print("✅ Reached 99 requests, waiting 1 minute to avoid rate limits...\n")
            time.sleep(60)

    # Step 2: Verify each username individually
    print("\n🔍 Verifying potential free usernames one by one...")
    confirmed_free_names = []

    for i, username in enumerate(potential_free_names, start=1):
        print(f"Checking username {i}/{len(potential_free_names)}: {username}", end='\r')
        if check_username_individually(username):
            confirmed_free_names.append(username)
        request_count += 1

        if request_count % 99 == 0:
            print("✅ Reached 99 requests during individual checks, waiting 1 minute...\n")
            time.sleep(60)

    print("\n\n=== ✅ Summary ===")
    print(f"🟨 Potential free usernames: {len(potential_free_names)}")
    print(f"🟩 Confirmed free usernames: {len(confirmed_free_names)}")

    if confirmed_free_names:
        send_discord_notification(confirmed_free_names, webhook_url, "Final")

    print("🎉 Done.")


if __name__ == "__main__":
    main()
