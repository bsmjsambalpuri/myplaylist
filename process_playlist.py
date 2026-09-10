import requests
import os
import re

# 1. Define your source public playlists (M3U URLs)
PLAYLIST_URLS = [
    "https://raw.githubusercontent.com/Dhruv0045/Playlist/refs/heads/main/allround.m3u", 
    "https://iptv-org.github.io/iptv/index.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/refs/heads/main/ekamraott.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/refs/heads/main/jtv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/refs/heads/main/ektv.m3u",
    "https://raw.githubusercontent.com/amazeyourself/m3u/refs/heads/main/samsungtvplus/all.m3u",
    "https://github.com/BuddyChewChew/app-m3u-generator/blob/main/playlists/roku_all.m3u", 
    "https://github.com/BuddyChewChew/app-m3u-generator/blob/main/playlists/plutotv_all.m3u", 
    "https://github.com/BuddyChewChew/app-m3u-generator/raw/refs/heads/main/playlists/plex_all.m3u" 
]

# 2. Define your EPG URLs
EPG_URL = "https://github.com/amazeyourself/m3u/raw/refs/heads/main/epg/airtel.xml.gz,https://i.mjh.nz/SamsungTVPlus/all.xml.gz"

def clean_channel_name(name):
    """
    Strips resolution indicators like (1080p), (720p), (504p), (4k), or (hd) 
    from the channel name and normalizes spaces.
    """
    name = re.sub(r'\s*\(\s*\d+p\s*\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(\s*4k\s*\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(\s*hd\s*\)', '', name, flags=re.IGNORECASE)
    
    return re.sub(r'\s+', ' ', name).strip().lower()

def load_whitelist():
    """
    Reads whitelist.txt and returns a dictionary where keys are clean lowercased names
    and values are tuples containing (Original Case Whitelist Name, Category).
    """
    if not os.path.exists("whitelist.txt"):
        print("Warning: whitelist.txt not found! Processing all channels instead.")
        return {}
    
    whitelist_map = {}
    with open("whitelist.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "," in line:
                channel_name, category = line.rsplit(",", 1)
                original_name = channel_name.strip()
                clean_name = clean_channel_name(original_name)
                whitelist_map[clean_name] = (original_name, category.strip())
            else:
                original_name = line.strip()
                clean_name = clean_channel_name(original_name)
                whitelist_map[clean_name] = (original_name, "Uncategorized")
                
    return whitelist_map

def update_metadata(metadata_line, exact_name, category):
    """
    1. Updates or adds the group-title attribute.
    2. Replaces the display name (text after the last comma) with the exact whitelist name.
    """
    # 1. Handle group-title update/insertion
    group_title_pattern = re.compile(r'group-title="[^"]*"', re.IGNORECASE)

    if group_title_pattern.search(metadata_line):
        updated_line = group_title_pattern.sub(f'group-title="{category}"', metadata_line)
    else:
        if "," in metadata_line:
            prefix, display_name = metadata_line.rsplit(",", 1)
            updated_line = f'{prefix} group-title="{category}",{display_name}'
        else:
            updated_line = f'{metadata_line} group-title="{category}"'

    # 2. Replace the display name after the last comma with the exact whitelist name
    if "," in updated_line:
        prefix, _ = updated_line.rsplit(",", 1)
        updated_line = f'{prefix},{exact_name}'
    else:
        updated_line = f'{updated_line},{exact_name}'

    return updated_line

def fetch_and_filter():
    whitelist_map = load_whitelist()
    if whitelist_map:
        print(f"Loaded {len(whitelist_map)} channel filters from whitelist.txt")
    
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
                    # Stream URL line
                    stream_url = line
                    
                    if current_metadata:
                        # --- DUPLICATE CHECK ---
                        if stream_url in seen_urls:
                            current_metadata = None
                            continue

                        # Extract raw display name
                        raw_channel_name = current_metadata.split(",")[-1]
                        normalized_channel_name = clean_channel_name(raw_channel_name)

                        # --- MATCHING & METADATA UPDATE ---
                        is_allowed = False

                        if not whitelist_map:
                            is_allowed = True
                        elif normalized_channel_name in whitelist_map:
                            is_allowed = True
                            exact_name, category = whitelist_map[normalized_channel_name]
                            current_metadata = update_metadata(current_metadata, exact_name, category)

                        if is_allowed:
                            merged_channels.append((current_metadata, stream_url))
                            seen_urls.add(stream_url)

                        current_metadata = None

        except Exception as e:
            print(f"Error processing {url}: {e}")

    # Write output to custom_playlist.m3u
    output_file = "custom_playlist.m3u"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{EPG_URL}"\n')
        
        for metadata, stream_url in merged_channels:
            f.write(f"{metadata}\n{stream_url}\n")

    print(f"Successfully created {output_file} with {len(merged_channels)} unique channels.")

if __name__ == "__main__":
    fetch_and_filter()