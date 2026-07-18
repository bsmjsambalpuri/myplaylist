import requests

# 1. Define your source public playlists (M3U URLs)
PLAYLIST_URLS = [
    "http://yaarokayaar2026iptv.fun/index.html"
]

# 2. Define your EPG URLs
EPG_URL = "https://github.com/amazeyourself/m3u/raw/refs/heads/main/epg/airtel.xml.gz,https://i.mjh.nz/SamsungTVPlus/all.xml.gz"

def fetch_all():
    print("Starting collection for another_playlist.m3u (Domain Filter Mode)")
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
                    stream_url = line
                    
                    if current_metadata:
                        # --- DOMAIN BLOCK FILTER ---
                        # Instantly skips URLs containing github.io or youtube.com
                        if "github.io" in stream_url.lower() or "youtube.com" in stream_url.lower():
                            current_metadata = None
                            continue

                        # --- DUPLICATE CHECK ---
                        if stream_url in seen_urls:
                            current_metadata = None
                            continue

                        # Add valid, filtered channels
                        merged_channels.append((current_metadata, stream_url))
                        seen_urls.add(stream_url)

                        current_metadata = None

        except Exception as e:
            print(f"Error processing {url}: {e}")

    # 3. Write all unique, filtered channels into another_playlist.m3u
    output_file = "another_playlist.m3u"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{EPG_URL}"\n')
        
        for metadata, stream_url in merged_channels:
            f.write(f"{metadata}\n{stream_url}\n")

    print(f"Successfully created {output_file} with {len(merged_channels)} channels.")

if __name__ == "__main__":
    fetch_all()