import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Set up the webhook URLs (keep them as environment variables)
os.environ["DISCORD_FINAL_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1376640623297433671/s_W7LeSd-v9B-FWVD5GEHUArryJUy24T0ZCg4buAv3DbuQo60Rd7Ss9wks_osEzd8gO1"
os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/1373286716504277002/3a8I20YEVadrZXGK_W3AcPB4v01d5walWIIySGwl6Xf-rdnpTm52XKNE3sr7HmfOY6OF"

# Define your list of proxies (replace with your actual proxies)
proxies_list = [
    "http://34.210.14.70:80",
    "http://203.19.38.114:1080",
    "http://210.206.242.146:5031",
    "http://190.2.143.81:80",
    "http://20.13.148.109:8080",
    "http://121.230.9.9:1080",
    "http://210.206.242.135:5031",
    "http://161.35.70.249:80",
    "http://8.209.255.13:3128",
    "http://38.250.126.201:999",
    "http://210.206.242.148:5031",
    "http://43.165.70.69:8080",
    "http://91.103.120.55:80",
    "http://159.65.230.46:8888",
    "http://210.206.242.149:5031",
    "http://114.80.36.171:3081",
    "http://168.138.50.91:80",
    "http://188.132.232.210:2158",
    "http://219.65.73.81:80",
    "http://119.18.146.92:96",
    "http://80.249.112.166:80",
    "http://47.56.110.204:8989",
    "http://129.226.155.235:8080",
    "http://190.2.143.81:8080",
    "http://14.241.80.37:8080",
    "http://123.140.100.118:5031",
    "http://218.61.85.209:9090",
    "http://185.105.102.189:80",
    "http://43.133.136.208:8800",
    "http://210.206.242.119:5031",
    "http://185.249.198.105:3128",
    "http://123.140.100.114:5031",
    "http://119.95.248.114:8082",
    "http://218.77.183.214:5224",
    "http://152.228.154.20:80",
    "http://60.187.244.66:8085",
    "http://181.78.74.174:999",
    "http://63.143.57.115:80",
    "http://31.220.78.244:80",
    "http://202.46.95.154:3125",
    "http://103.144.253.234:8080",
    "http://94.103.83.90:3128",
    "http://210.206.242.150:5031",
    "http://190.60.60.220:8080",
    "http://183.88.48.52:8080",
    "http://57.129.81.201:8080",
    "http://35.209.198.222:80",
    "http://51.255.36.182:80",
    "http://47.245.117.43:80",
    "http://38.156.238.121:999",
    "http://34.80.152.137:8866",
    "http://103.168.44.162:3125",
    "http://47.251.43.115:33333",
    "http://85.215.64.49:80",
    "http://131.100.49.109:999",
    "http://23.237.210.82:80",
    "http://45.12.150.82:8080",
    "http://3.35.174.230:3128",
    "http://88.135.72.7:80",
    "http://45.167.126.37:999",
    "http://34.85.11.145:8080",
    "http://180.191.51.218:8082",
    "http://197.164.101.11:1976",
    "http://190.83.15.2:999",
    "http://147.45.104.252:80",
    "http://45.136.198.40:3128",
    "http://200.174.198.86:8888",
    "http://167.250.50.2:999",
    "http://36.138.53.26:10019",
    "http://89.46.249.252:5080",
    "http://8.213.137.155:42",
    "http://93.190.138.107:46182",
    "http://135.181.154.225:80",
    "http://8.213.137.155:258",
    "http://188.69.231.89:8080",
    "http://23.82.137.161:80",
    "http://103.166.32.230:1111",
    "http://190.60.34.13:999",
    "http://187.198.208.82:8080",
    "http://114.230.208.105:3712",
    "http://138.121.121.223:8080",
    "http://46.161.194.65:1976",
    "http://121.233.233.45:3712",
    "http://94.141.122.116:8080",
    "http://200.52.157.138:999",
    "http://8.213.137.155:10001",
    "http://181.78.74.172:999",
    "http://103.172.42.125:1111",
    "http://27.79.173.71:16000",
    "http://103.180.123.227:3127",
    "http://102.44.142.58:8080",
    "http://191.81.233.180:8080",
    "http://103.22.99.46:8080",
    "http://46.47.197.210:3128",
    "http://45.191.152.61:8080",
    "http://27.79.222.78:16000",
    "http://51.81.245.3:17981",
    "http://138.68.60.8:80",
    "http://35.243.127.1:8080",
    "http://221.202.27.194:10809",
    "http://54.38.181.125:3128",
    "http://124.121.94.250:8080",
    "http://162.19.49.131:80",
    "http://200.121.48.195:999",
    "http://8.211.42.167:1080",
    "http://8.222.235.39:3128",
    "http://103.81.175.218:28022",
    "http://202.148.8.130:64321",
    "http://160.19.18.75:8080",
    "http://171.224.0.93:4004",
    "http://38.191.208.11:999",
    "http://114.244.74.32:9000",
    "http://67.43.236.21:12817",
    "http://157.66.16.40:8787",
    "http://119.3.128.227:8808",
    "http://8.211.42.167:8083",
    "http://124.107.205.34:8081",
    "http://172.105.37.192:8888",
    "http://177.234.217.82:999",
    "http://103.21.69.192:83",
    "http://197.248.75.221:8105",
    "http://103.214.144.190:3128",
    "http://45.64.99.129:3125",
    "http://190.119.76.148:8080",
    "http://110.136.50.220:8080",
    "http://103.151.74.37:8080",
    "http://27.69.181.116:5104",
    "http://103.199.139.17:83",
    "http://80.241.251.54:8080",
    "http://219.93.101.63:80",
    "http://103.20.88.6:8080",
    "http://45.140.143.77:18080",
    "http://103.154.230.98:8080",
    "http://36.37.163.113:8080",
    "http://1.33.111.12:8080",
    "http://221.231.13.198:1080",
    "http://210.206.242.147:5031",
    "http://181.78.99.189:999",
    "http://181.39.15.221:999",
    "http://103.160.15.110:8080",
    "http://103.189.197.9:8080",
    "http://38.51.235.216:999",
    "http://159.138.9.58:2221",
    "http://202.61.204.51:80",
    "http://8.211.42.167:8005",
    "http://52.140.40.92:80",
    "http://34.87.109.175:443",
    "http://189.205.215.202:8080",
    "http://185.191.236.162:3128",
    "http://103.82.135.201:31000",
    "http://190.61.44.132:9999",
    "http://186.194.161.141:999",
    "http://45.67.221.230:80",
    "http://87.255.196.143:80",
    "http://57.129.81.201:999",
    "http://38.51.243.81:999",
    "http://45.14.165.47:8080",
    "http://8.219.92.16:5656"
]


def get_random_proxy():
    """Return a random proxy from the list."""
    return {"http": random.choice(proxies_list), "https": random.choice(proxies_list)}

def read_usernames_from_file(filename):
    usernames = []
    with open(filename, "r", encoding="utf-8") as f:
        usernames = [line.strip() for line in f if line.strip()]
    return usernames

def check_username(username):
    url = f"https://api-cops.criticalforce.fi/api/public/profile?usernames={username}"
    try:
        proxy = get_random_proxy()  # Get a random proxy
        response = requests.get(url, proxies=proxy, timeout=5)
        if response.status_code == 500:
            print(f"Server error while checking {username}, assuming name is free.")
            return username  # Free name found
    except requests.RequestException as e:
        print(f"Error checking {username}: {e}")
    return None

def check_usernames_concurrently(usernames, max_workers=10):
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
            if result:
                free_names.append(result)

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
    input_file = "99.txt"  # Change this to your txt filename
    all_usernames = read_usernames_from_file(input_file)
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    batch_size = 99
    total = len(all_usernames)
    all_free_names = []

    for batch_num, start_idx in enumerate(range(0, total, batch_size), start=1):
        batch_usernames = all_usernames[start_idx:start_idx + batch_size]
        print(f"\nProcessing batch {batch_num} with {len(batch_usernames)} usernames...")
        
        free_names = check_usernames_concurrently(batch_usernames)
        if free_names:
            all_free_names.extend(free_names)

        send_discord_notification(free_names, webhook_url, batch_num)

        # If not the last batch, wait 1 minute before next batch
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
