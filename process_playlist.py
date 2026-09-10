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

def load_whitelist():
    """
    Reads whitelist.txt and returns a dictionary mapping lowercased channel names
    to their assigned group/category.
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
            
            # Split line into channel name and category using the last comma as separator
            if "," in line:
                channel_name, category = line.rsplit(",", 1)
                whitelist_map[channel_name.strip().lower()] = category.strip()
            else:
                whitelist_map[line.strip().lower()] = "Uncategorized"
                
    return whitelist_map

def update_group_title(metadata_line, category):
    """
    Updates or adds the group-title attribute in the #EXTINF metadata string.
    """
    if not category:
        return metadata_line

    # Regex to check if group-title already exists
    group_title_pattern = re.compile(r'group-title="[^"]*"', re.IGNORECASE)

    if group_title_pattern.search(metadata_line):
        # Update existing group-title
        updated_line = group_title_pattern.sub(f'group-title="{category}"', metadata_line)
    else:
        # Insert group-title right before the comma separating attributes and display name
        if "," in metadata_line:
            prefix, display_name = metadata_line.rsplit(",", 1)
            updated_line = f'{prefix} group-title="{category}",{display_name}'
        else:
            updated_line = f'{metadata_line} group-title="{category}"'

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

                        # Extract display name (text after the last comma)
                        raw_channel_name = current_metadata.split(",")[-1].strip().lower()

                        # --- EXACT MATCH FILTERING & CATEGORY UPDATE ---
                        is_allowed = False
                        category = None

                        if not whitelist_map:
                            is_allowed = True
                        elif raw_channel_name in whitelist_map:
                            is_allowed = True
                            category = whitelist_map[raw_channel_name]

                        if is_allowed:
                            # Update or inject group-title if category exists
                            if category:
                                current_metadata = update_group_title(current_metadata, category)
                                
                            merged_channels.append((current_metadata, stream_url))
                            seen_urls.add(stream_url)

                        current_metadata = None

        except Exception as e:
            print(f"Error processing {url}: {e}")

    # Write the unique, whitelisted channels into the final M3U file
    output_file = "custom_playlist.m3u"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{EPG_URL}"\n')
        
        for metadata, stream_url in merged_channels:
            f.write(f"{metadata}\n{stream_url}\n")

    print(f"Successfully created {output_file} with {len(merged_channels)} unique channels.")

if __name__ == "__main__":
    fetch_and_filter()