from imapclient import IMAPClient
import time
import os

# === USER CONFIG ===
EMAIL = os.environ.get("GMAIL")
APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")  # Get from environment variable
OUT_PATH = "C:\\Users\\petri\\Documents\\gmail_unread.txt"

# === CORE ===
def get_unread_count(client):
    client.select_folder("INBOX")
    messages = client.search(["UNSEEN"])
    return len(messages)

def write_unread_count(count):
    with open(OUT_PATH, "w") as f:
        f.write(str(count))

# === MAIN LOOP ===
def main():
    if not APP_PASSWORD:
        print("Error: GMAIL_APP_PASSWORD environment variable not set")
        print("Set it using: $env:GMAIL_APP_PASSWORD = 'your-app-password'")
        return

    while True:
        try:
            with IMAPClient("imap.gmail.com") as client:
                client.login(EMAIL, APP_PASSWORD)

                # Initial update
                count = get_unread_count(client)
                write_unread_count(count)

                while True:
                    client.idle()
                    responses = client.idle_check(timeout=10)  # up to 10s
                    client.idle_done()
                    
                    count = get_unread_count(client)
                    write_unread_count(count)
                    print("done")

        except Exception:
            time.sleep(5)  # wait and try again if disconnected

if __name__ == "__main__":
    main()

