import re
import requests
import os

# 1. Define your source public playlists (M3U URLs)
PLAYLIST_URLS = [
    "https://iptv-org.github.io/iptv/index.m3u",
    "https://raw.githubusercontent.com/BuddyChewChew/samsungtvplus/refs/heads/main/output/samsung_tvplus.m3u",
]

def load_whitelist():
    """Reads the whitelist.txt file and returns a list of clean keywords."""
    if not os.path.exists("whitelist.txt"):
        print("Warning: whitelist.txt not found! Processing all channels instead.")
        return []
    
    with open("whitelist.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def fetch_and_filter():
    whitelist = load_whitelist()
    if whitelist:
        print(f"Loaded {len(whitelist)} channel filters from whitelist.txt")
    
    merged_channels = []
    seen_urls = set()  # Tracks unique URLs to prevent duplicates

    for url in PLAYLIST_URLS:
        print(f"Fetching: {url}")
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                print(f"Skipping {url} (Status Code: {response.status_code})")
                continue

            lines = response.text.splitlines()
            current_metadata = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("#EXTINF:"):
                    current_metadata = line
                elif line.startswith("#") and not line.startswith("#EXTINF:"):
                    continue
                else:
                    # This line is the actual stream URL
                    stream_url = line
                    
                    if current_metadata:
                        # --- DUPLICATE CHECK ---
                        # If we have already added this stream URL, skip it entirely
                        if stream_url in seen_urls:
                            current_metadata = None
                            continue

                        # Extract the display name (everything after the last comma)
                        channel_name = current_metadata.split(",")[-1].strip()

                        # Check whitelist matching
                        is_allowed = False
                        if not whitelist:
                            is_allowed = True
                        else:
                            for allowed_name in whitelist:
                                if re.search(r'\b' + re.escape(allowed_name) + r'\b', channel_name, re.IGNORECASE):
                                    is_allowed = True
                                    break
                                elif allowed_name.lower() in channel_name.lower():
                                    is_allowed = True
                                    break

                        if is_allowed:
                            merged_channels.append((current_metadata, stream_url))
                            seen_urls.add(stream_url) # Mark this URL as processed

                        current_metadata = None

        except Exception as e:
            print(f"Error processing {url}: {e}")

    # 3. Write the unique, whitelisted channels into your final M3U file
    output_file = "custom_playlist.m3u"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for metadata, stream_url in merged_channels:
            f.write(f"{metadata}\n{stream_url}\n")

    print(f"Successfully created {output_file} with {len(merged_channels)} unique channels.")

if __name__ == "__main__":
    fetch_and_filter()