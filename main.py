import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def read_lines_from_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: File '{filename}' not found. Continuing without it.")
        return []

def read_usernames_from_file(filename):
    return read_lines_from_file(filename)

def read_blacklist(filename="blacklist.txt"):
    return set(read_lines_from_file(filename))

def is_blacklisted(username, blacklist):
    return any(bad_word.lower() in username.lower() for bad_word in blacklist)

def check_username(username):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={username}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 500:
            return username  # Free name found
    except requests.RequestException:
        pass
    return None

def check_usernames_concurrently(usernames, blacklist, max_workers=10):
    total = len(usernames)
    free_names = []

    print(f"Checking {total} usernames with {max_workers} threads...\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_username = {executor.submit(check_username, name): name for name in usernames}

        for i, future in enumerate(as_completed(future_to_username), start=1):
            username = future_to_username[future]
            progress = (i / total) * 100
            print(f"[{i}/{total}] ({progress:.2f}%) Checked: {username}", end='\r')

            result = future.result()
            if result and not is_blacklisted(result, blacklist):
                free_names.append(result)

    print()
    return free_names

def send_discord_notification(free_names, webhook_url, batch_number=None, final=False):
    if not free_names or not webhook_url:
        return

    if final:
        title = "**✅ Final Free Usernames Summary!**"
        if batch_number:
            title += f" (Batches Processed: {batch_number})"
    else:
        title = f"**🚨 @everyone Free Usernames Found (Batch {batch_number})!**"

    message = f"{title}\n" + "\n".join(f"- `{name}`" for name in free_names)
    payload = {"content": message}

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code in [200, 204]:
            print("✅ Discord notification sent successfully.")
        else:
            print(f"❌ Failed to send Discord notification: HTTP {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Error sending Discord notification: {e}")

def main():
    input_file = "99.txt"
    blacklist_file = "blacklist.txt"

    all_usernames = read_usernames_from_file(input_file)
    blacklist = read_blacklist(blacklist_file)

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    final_webhook_url = os.getenv("DISCORD_FINAL_WEBHOOK_URL")

    batch_size = 99
    total = len(all_usernames)
    all_free_names = []

    for batch_num, start_idx in enumerate(range(0, total, batch_size), start=1):
        batch_usernames = all_usernames[start_idx:start_idx + batch_size]
        print(f"\nProcessing batch {batch_num} with {len(batch_usernames)} usernames...")

        free_names = check_usernames_concurrently(batch_usernames, blacklist)
        if free_names:
            all_free_names.extend(free_names)
            send_discord_notification(free_names, webhook_url, batch_num)

        if start_idx + batch_size < total:
            print("Waiting 2 minutes before next batch to avoid hitting API rate limits...\n")
            time.sleep(60)

    print("\n=== All batches processed ===")
    print(f"Total free usernames found: {len(all_free_names)}")
    if all_free_names:
        print("All free usernames:")
        for name in all_free_names:
            print(f"- {name}")

        send_discord_notification(all_free_names, final_webhook_url, batch_number=batch_num, final=True)

if __name__ == "__main__":
    main()
