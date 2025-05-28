import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set environment variables (webhooks)
os.environ["DISCORD_FINAL_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1376640623297433671/s_W7LeSd-v9B-FWVD5GEHUArryJUy24T0ZCg4buAv3DbuQo60Rd7Ss9wks_osEzd8gO1"
os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1373286716504277002/3a8I20YEVadrZXGK_W3AcPB4v01d5walWIIySGwl6Xf-rdnpTm52XKNE3sr7HmfOY6OF"

def read_usernames_from_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def check_batch_usernames(usernames_batch):
    joined_names = ",".join(usernames_batch)
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={joined_names}"
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 500
    except requests.RequestException:
        return False

def check_username_individually(username):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={username}"
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 500
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
            request_counter += 1
            print(f"📡 Request #{request_counter} - Checked: {name_list[0]}")
            if request_counter % 99 == 0:
                print("⏱️ Reached 99 requests, waiting 1 minute...")
                time.sleep(60)
            return name_list if check_username_individually(name_list[0]) else []

        # Check batch
        if check_batch_usernames(name_list):
            request_counter += 1
            print(f"📡 Request #{request_counter} - Batch likely free: {name_list}")
            if request_counter % 99 == 0:
                print("⏱️ Reached 99 requests, waiting 1 minute...")
                time.sleep(60)
            return name_list
        else:
            request_counter += 1
            print(f"📡 Request #{request_counter} - Batch had taken names")
            if request_counter % 99 == 0:
                print("⏱️ Reached 99 requests, waiting 1 minute...")
                time.sleep(60)
            mid = len(name_list) // 2
            return recursive_check(name_list[:mid]) + recursive_check(name_list[mid:])

    def threaded_check(usernames):
        nonlocal request_counter
        confirmed = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_username_individually, u): u for u in usernames}
            for i, future in enumerate(as_completed(futures), start=1):
                result = future.result()
                request_counter += 1
                print(f"📡 Request #{request_counter} - Checked: {futures[future]}")
                if request_counter % 99 == 0:
                    print("⏱️ Reached 99 requests, waiting 1 minute...")
                    time.sleep(60)
                if result:
                    confirmed.append(futures[future])
        return confirmed

    usernames_to_verify = recursive_check(usernames)
    print(f"\n🧠 Recursively collected {len(usernames_to_verify)} usernames to verify individually.\n")

    confirmed_free = threaded_check(usernames_to_verify)
    return confirmed_free, request_counter

def main():
    input_file = "99.txt"
    all_usernames = read_usernames_from_file(input_file)
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    request_counter = 0

    print(f"📄 Loaded {len(all_usernames)} usernames from {input_file}.")
    confirmed_free_usernames, request_counter = divide_and_conquer(all_usernames, request_counter, max_workers=10)

    print("\n=== ✅ Summary ===")
    print(f"🟨 Potential free usernames: {len(all_usernames)}")
    print(f"🟩 Confirmed free usernames: {len(confirmed_free_usernames)}")

    if confirmed_free_usernames:
        send_discord_notification(confirmed_free_usernames, webhook_url, "Final")

    print("🎉 Done.")

if __name__ == "__main__":
    main()
