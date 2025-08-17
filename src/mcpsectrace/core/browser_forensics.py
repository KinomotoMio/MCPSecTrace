import os
import sqlite3
import datetime
import platform
import shutil  # For copying files
from pathlib import Path
import json  # For structured output

# Optional: psutil to check if browser is running
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil library not found. Cannot check if browsers are running.")
    print("Please ensure target browsers are closed for reliable data extraction.")


def get_user_profile_path():
    """Gets the current user's profile path."""
    if platform.system() == "Windows":
        return Path(os.environ['USERPROFILE'])
    elif platform.system() == "Darwin":  # macOS
        return Path.home()
    elif platform.system() == "Linux":
        return Path.home()
    return None


def convert_chrome_time(chrome_time):
    """Converts Chrome's timestamp (microseconds since Jan 1, 1601 UTC) to datetime."""
    if chrome_time > 0:
        return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=chrome_time)
    return None


def convert_firefox_time(ff_time):
    """Converts Firefox's timestamp (microseconds since Jan 1, 1970 UTC) to datetime."""
    if ff_time > 0:
        return datetime.datetime(1970, 1, 1) + datetime.timedelta(microseconds=ff_time)
    return None


def get_chrome_history(profile_path: Path, max_items=100):
    """
    Retrieves browsing history from Google Chrome.
    """
    print("\n--- Attempting to retrieve Chrome History ---")
    history_items = []
    # Common paths for Chrome history - may need adjustment
    # Default profile, also check other profiles like "Profile 1", "Profile 2", etc.
    chrome_paths_to_check = [
        profile_path / "AppData/Local/Google/Chrome/User Data/Default/History",
        # Add paths for other Chrome-based browsers if needed (e.g., Brave, Vivaldi)
        profile_path / "AppData/Local/Microsoft/Edge/User Data/Default/History"  # Microsoft Edge (Chromium)
    ]

    history_db_path = None
    browser_name = "Chrome/Edge"

    for p_idx, p_path in enumerate(chrome_paths_to_check):
        if p_path.exists():
            history_db_path = p_path
            if "Edge" in str(p_path):
                browser_name = "Microsoft Edge"
            elif "Chrome" in str(p_path):
                browser_name = "Google Chrome"
            print(f"Found {browser_name} history database at: {history_db_path}")
            break
        else:
            if p_idx == 0:
                print(f"Chrome default history DB not found at: {p_path}")
            elif p_idx == 1:
                print(f"Edge default history DB not found at: {p_path}")

    if not history_db_path:
        print("No Chrome/Edge history database found at common locations.")
        return {"browser": browser_name, "status": "error", "message": "History DB not found", "data": []}

    # Copy the database to a temporary location to avoid lock issues
    temp_db_path = profile_path / f"temp_{browser_name.replace(' ', '_')}_history.db"
    try:
        shutil.copy2(history_db_path, temp_db_path)
        print(f"Copied history DB to temporary file: {temp_db_path}")
    except Exception as e:
        print(f"Error copying history DB: {e}. Ensure {browser_name} is closed.")
        return {"browser": browser_name, "status": "error", "message": f"Failed to copy DB: {e}", "data": []}

    conn = None
    try:
        conn = sqlite3.connect(f"file:{temp_db_path}?mode=ro", uri=True)  # Read-only mode
        cursor = conn.cursor()
        # Query to get URL, title, and last visit time
        # last_visit_time is in microseconds since 1601-01-01 00:00:00 UTC
        query = f"""
            SELECT urls.url, urls.title, visits.visit_time
            FROM urls, visits
            WHERE urls.id = visits.url
            ORDER BY visits.visit_time DESC
            LIMIT {max_items};
        """
        cursor.execute(query)
        for row in cursor.fetchall():
            url = row[0]
            title = row[1]
            timestamp_us = row[2]  # This is Chrome's timestamp
            visit_time_dt = convert_chrome_time(timestamp_us)
            history_items.append({
                "url": url,
                "title": title,
                "last_visit_time_utc": visit_time_dt.isoformat() if visit_time_dt else None,
                "timestamp_raw": timestamp_us
            })
        print(f"Retrieved {len(history_items)} history items from {browser_name}.")
        return {"browser": browser_name, "status": "success", "message": f"Retrieved {len(history_items)} items.",
                "data": history_items}
    except sqlite3.Error as e:
        print(f"SQLite error while reading {browser_name} history: {e}")
        return {"browser": browser_name, "status": "error", "message": f"SQLite error: {e}", "data": []}
    finally:
        if conn:
            conn.close()
        if temp_db_path.exists():
            try:
                os.remove(temp_db_path)
                print(f"Removed temporary history DB: {temp_db_path}")
            except OSError as e:
                print(f"Error removing temporary history DB {temp_db_path}: {e}")


def get_chrome_downloads(profile_path: Path, max_items=50):
    """
    Retrieves download history from Google Chrome.
    """
    print("\n--- Attempting to retrieve Chrome Downloads ---")
    download_items = []
    # Common paths for Chrome history (downloads are in the same DB)
    chrome_paths_to_check = [
        profile_path / "AppData/Local/Google/Chrome/User Data/Default/History",
        profile_path / "AppData/Local/Microsoft/Edge/User Data/Default/History"  # Microsoft Edge (Chromium)
    ]

    history_db_path = None
    browser_name = "Chrome/Edge"

    for p_idx, p_path in enumerate(chrome_paths_to_check):
        if p_path.exists():
            history_db_path = p_path
            if "Edge" in str(p_path):
                browser_name = "Microsoft Edge"
            elif "Chrome" in str(p_path):
                browser_name = "Google Chrome"
            print(f"Found {browser_name} history database (for downloads) at: {history_db_path}")
            break
        else:
            if p_idx == 0:
                print(f"Chrome default history DB not found at: {p_path}")
            elif p_idx == 1:
                print(f"Edge default history DB not found at: {p_path}")

    if not history_db_path:
        print("No Chrome/Edge history database found for downloads.")
        return {"browser": browser_name, "status": "error", "message": "History DB not found for downloads", "data": []}

    temp_db_path = profile_path / f"temp_{browser_name.replace(' ', '_')}_downloads_history.db"
    try:
        shutil.copy2(history_db_path, temp_db_path)
        print(f"Copied downloads history DB to temporary file: {temp_db_path}")
    except Exception as e:
        print(f"Error copying downloads history DB: {e}. Ensure {browser_name} is closed.")
        return {"browser": browser_name, "status": "error", "message": f"Failed to copy DB: {e}", "data": []}

    conn = None
    try:
        conn = sqlite3.connect(f"file:{temp_db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        # The 'downloads' table contains download information
        # target_path is the full path to the downloaded file
        # start_time is in microseconds since 1601-01-01 00:00:00 UTC
        query = f"""
            SELECT target_path, tab_url, mime_type, total_bytes, start_time, end_time, state, danger_type
            FROM downloads
            ORDER BY start_time DESC
            LIMIT {max_items};
        """
        cursor.execute(query)
        for row in cursor.fetchall():
            start_time_dt = convert_chrome_time(row[4])
            end_time_dt = convert_chrome_time(row[5])
            # State: 0=IN_PROGRESS, 1=COMPLETE, 2=CANCELLED, 3=INTERRUPTED, 4=DANGEROUS, 5=BUG_147583_FIX, etc.
            # Danger Type: 0=NOT_DANGEROUS, 1=DANGEROUS_FILE, 2=DANGEROUS_URL, etc.
            download_items.append({
                "target_path": row[0],
                "source_url": row[1],
                "mime_type": row[2],
                "total_bytes": row[3],
                "start_time_utc": start_time_dt.isoformat() if start_time_dt else None,
                "end_time_utc": end_time_dt.isoformat() if end_time_dt else None,
                "state": row[6],
                "danger_type": row[7],
                "start_timestamp_raw": row[4]
            })
        print(f"Retrieved {len(download_items)} download items from {browser_name}.")
        return {"browser": browser_name, "status": "success", "message": f"Retrieved {len(download_items)} items.",
                "data": download_items}
    except sqlite3.Error as e:
        print(f"SQLite error while reading {browser_name} downloads: {e}")
        return {"browser": browser_name, "status": "error", "message": f"SQLite error: {e}", "data": []}
    finally:
        if conn:
            conn.close()
        if temp_db_path.exists():
            try:
                os.remove(temp_db_path)
                print(f"Removed temporary downloads DB: {temp_db_path}")
            except OSError as e:
                print(f"Error removing temporary downloads DB {temp_db_path}: {e}")


def get_firefox_history(profile_path: Path, max_items=100):
    """
    Retrieves browsing history from Mozilla Firefox.
    Firefox profiles are more complex to locate.
    """
    print("\n--- Attempting to retrieve Firefox History ---")
    history_items = []
    firefox_base_path = None
    if platform.system() == "Windows":
        firefox_base_path = profile_path / "AppData/Roaming/Mozilla/Firefox/Profiles"
    elif platform.system() == "Darwin":  # macOS
        firefox_base_path = profile_path / "Library/Application Support/Firefox/Profiles"
    elif platform.system() == "Linux":
        firefox_base_path = profile_path / ".mozilla/firefox"

    if not firefox_base_path or not firefox_base_path.exists():
        print(f"Firefox profiles base path not found: {firefox_base_path}")
        return {"browser": "Firefox", "status": "error", "message": "Profiles base path not found", "data": []}

    history_db_path = None
    # Firefox profile folders have a random string and a profile name (e.g., xxxxxxxx.default-release)
    for item in firefox_base_path.iterdir():
        if item.is_dir() and (item.name.endswith(".default") or item.name.endswith(".default-release")):
            potential_db = item / "places.sqlite"
            if potential_db.exists():
                history_db_path = potential_db
                print(f"Found Firefox history database at: {history_db_path}")
                break

    if not history_db_path:
        print("No Firefox history database (places.sqlite) found in default profiles.")
        return {"browser": "Firefox", "status": "error", "message": "places.sqlite not found", "data": []}

    temp_db_path = profile_path / "temp_firefox_history.db"
    try:
        shutil.copy2(history_db_path, temp_db_path)
        print(f"Copied Firefox history DB to temporary file: {temp_db_path}")
    except Exception as e:
        print(f"Error copying Firefox history DB: {e}. Ensure Firefox is closed.")
        return {"browser": "Firefox", "status": "error", "message": f"Failed to copy DB: {e}", "data": []}

    conn = None
    try:
        conn = sqlite3.connect(f"file:{temp_db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        # moz_places stores URLs and titles, moz_historyvisits stores visit times
        # last_visit_date is in microseconds since 1970-01-01 00:00:00 UTC
        query = f"""
            SELECT p.url, p.title, h.visit_date
            FROM moz_places p, moz_historyvisits h
            WHERE p.id = h.place_id
            ORDER BY h.visit_date DESC
            LIMIT {max_items};
        """
        cursor.execute(query)
        for row in cursor.fetchall():
            url = row[0]
            title = row[1]
            timestamp_us = row[2]  # Firefox timestamp
            visit_time_dt = convert_firefox_time(timestamp_us)
            history_items.append({
                "url": url,
                "title": title,
                "last_visit_time_utc": visit_time_dt.isoformat() if visit_time_dt else None,
                "timestamp_raw": timestamp_us
            })
        print(f"Retrieved {len(history_items)} history items from Firefox.")
        return {"browser": "Firefox", "status": "success", "message": f"Retrieved {len(history_items)} items.",
                "data": history_items}
    except sqlite3.Error as e:
        print(f"SQLite error while reading Firefox history: {e}")
        return {"browser": "Firefox", "status": "error", "message": f"SQLite error: {e}", "data": []}
    finally:
        if conn:
            conn.close()
        if temp_db_path.exists():
            try:
                os.remove(temp_db_path)
                print(f"Removed temporary Firefox history DB: {temp_db_path}")
            except OSError as e:
                print(f"Error removing temporary Firefox history DB {temp_db_path}: {e}")


def get_firefox_downloads(profile_path: Path, max_items=50):
    """
    Retrieves download history from Mozilla Firefox.
    Downloads are also in places.sqlite.
    """
    print("\n--- Attempting to retrieve Firefox Downloads ---")
    download_items = []
    # Path logic is the same as for history
    firefox_base_path = None
    if platform.system() == "Windows":
        firefox_base_path = profile_path / "AppData/Roaming/Mozilla/Firefox/Profiles"
    # ... (add macOS and Linux paths as in get_firefox_history) ...

    if not firefox_base_path or not firefox_base_path.exists():
        print(f"Firefox profiles base path not found for downloads: {firefox_base_path}")
        return {"browser": "Firefox", "status": "error", "message": "Profiles base path not found", "data": []}

    history_db_path = None
    for item in firefox_base_path.iterdir():
        if item.is_dir() and (item.name.endswith(".default") or item.name.endswith(".default-release")):
            potential_db = item / "places.sqlite"
            if potential_db.exists():
                history_db_path = potential_db
                print(f"Found Firefox database (for downloads) at: {history_db_path}")
                break

    if not history_db_path:
        print("No Firefox database (places.sqlite) found for downloads.")
        return {"browser": "Firefox", "status": "error", "message": "places.sqlite not found for downloads", "data": []}

    temp_db_path = profile_path / "temp_firefox_downloads.db"
    try:
        shutil.copy2(history_db_path, temp_db_path)
        print(f"Copied Firefox downloads DB to temporary file: {temp_db_path}")
    except Exception as e:
        print(f"Error copying Firefox downloads DB: {e}. Ensure Firefox is closed.")
        return {"browser": "Firefox", "status": "error", "message": f"Failed to copy DB: {e}", "data": []}

    conn = None
    try:
        conn = sqlite3.connect(f"file:{temp_db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        # Download information is in moz_annos (annotations) linked to moz_places
        # and moz_items_annos. This query is more complex.
        # This gets the download target and source URL.
        # Date is dateAdded to moz_places, which is less precise than Chrome's start/end time for downloads.
        # For more precise download times and states, one might need to parse download manager's own logs or newer DB structures if they exist.
        # Firefox's 'places.sqlite' schema for downloads:
        # - moz_places: Stores URLs (both visited and download sources).
        # - moz_annos: Stores annotations. For downloads, an annotation with name 'downloads/destinationFileURI' points to the saved file path.
        # - moz_items_annos: Links moz_places (fk column, for source URL) to moz_annos.
        # - Other annotations like 'downloads/metaData' (JSON blob) might contain more info.
        query = f"""
            SELECT
                p_target.url AS target_file_uri,
                p_source.url AS source_url,
                a_meta.content AS metadata_json, -- Contains more details if available
                p_source.last_visit_date AS download_init_time_approx_us -- This is an approximation
            FROM
                moz_annos AS a_target
            JOIN
                moz_items_annos AS ia ON a_target.id = ia.anno_attribute_id
            JOIN
                moz_places AS p_source ON ia.item_id = p_source.id
            LEFT JOIN -- metadata is optional
                moz_items_annos AS ia_meta ON p_source.id = ia_meta.item_id
            LEFT JOIN
                moz_annos AS a_meta ON ia_meta.anno_attribute_id = a_meta.id AND a_meta.name = 'downloads/metaData'
            JOIN -- The target file path is stored as a URL (file:///) in moz_places
                moz_places AS p_target ON a_target.content = p_target.uri_hash -- This join is tricky, content is a hash of the target URI
                                        -- A simpler approach is to just take a_target.content if it's the direct file path annotation.
                                        -- The schema can be complex. For simplicity, let's assume a_target.content IS the file URI if name is 'downloads/destinationFileURI'
            WHERE
                a_target.name = 'downloads/destinationFileURI'
            ORDER BY
                p_source.last_visit_date DESC
            LIMIT {max_items};
        """
        # Simpler query if the above is too complex or doesn't work reliably across versions:
        # This focuses on finding the 'downloads/destinationFileURI' and 'downloads/metaData' annotations.
        simple_query = f"""
            SELECT
                (SELECT plc.url FROM moz_places plc WHERE plc.id = ia.item_id) AS source_url,
                anno.content AS annotation_content, -- This can be target path or metadata
                anno.name AS annotation_name,
                ia.dateAdded AS annotation_date_us
            FROM moz_items_annos ia
            JOIN moz_annos anno ON ia.anno_attribute_id = anno.id
            WHERE anno.name LIKE 'downloads/%'
            ORDER BY ia.dateAdded DESC
            LIMIT {max_items * 5}; -- Fetch more to sort and group later
        """  # This simpler query will require post-processing to group related download annotations

        cursor.execute(simple_query)  # Using the simpler query for now, requires post-processing

        # Post-processing for the simpler query (this is basic)
        raw_downloads = {}
        for row in cursor.fetchall():
            source_url, content, name, date_us = row
            if source_url not in raw_downloads:
                raw_downloads[source_url] = {"source_url": source_url, "approx_date_utc": None, "target_path": None,
                                             "metadata": None}

            dt_obj = convert_firefox_time(date_us)
            if dt_obj:
                raw_downloads[source_url]["approx_date_utc"] = dt_obj.isoformat()

            if name == 'downloads/destinationFileURI':
                raw_downloads[source_url]["target_path"] = content.replace("file:///", "")  # Clean file URI
            elif name == 'downloads/metaData':
                try:
                    raw_downloads[source_url]["metadata"] = json.loads(content)
                except json.JSONDecodeError:
                    raw_downloads[source_url]["metadata"] = {"error": "Could not parse metadata JSON",
                                                             "raw_content": content}

        # Convert dictionary to list and sort
        processed_downloads = sorted(
            [v for v in raw_downloads.values() if v.get("target_path")],  # Only include if we found a target_path
            key=lambda x: x.get("approx_date_utc", "0"),
            reverse=True
        )[:max_items]

        download_items = processed_downloads

        print(
            f"Retrieved {len(download_items)} potential download items from Firefox (requires careful interpretation).")
        return {"browser": "Firefox", "status": "success_partial" if download_items else "success_no_items",
                "message": f"Retrieved {len(download_items)} items. Firefox download data is complex.",
                "data": download_items}

    except sqlite3.Error as e:
        print(f"SQLite error while reading Firefox downloads: {e}")
        return {"browser": "Firefox", "status": "error", "message": f"SQLite error: {e}", "data": []}
    finally:
        if conn:
            conn.close()
        if temp_db_path.exists():
            try:
                os.remove(temp_db_path)
                print(f"Removed temporary Firefox downloads DB: {temp_db_path}")
            except OSError as e:
                print(f"Error removing temporary Firefox downloads DB {temp_db_path}: {e}")


def check_browser_processes(browser_executables):
    """Checks if specified browser executables are running."""
    if not PSUTIL_AVAILABLE:
        return
    running_browsers = []
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] in browser_executables:
            running_browsers.append(proc.info['name'])
    if running_browsers:
        print("\nWARNING: The following browser processes are running:")
        for b in set(running_browsers):
            print(f"  - {b}")
        print("Please close them for more reliable data extraction, as database files might be locked.")
    else:
        print("\nNo target browser processes detected as running (good!).")


if __name__ == "__main__":
    user_profile = get_user_profile_path()
    all_browser_data = {}

    if not user_profile:
        print("Could not determine user profile path. Exiting.")
        exit()

    print(f"Current user profile path: {user_profile}")
    print(f"Current OS: {platform.system()}")

    # List of common browser executables to check if running
    # (add more if you're targeting other browsers)
    browser_exes = ["chrome.exe", "msedge.exe", "firefox.exe", "opera.exe", "brave.exe"]
    check_browser_processes(browser_exes)

    # --- Collect Chrome and Edge Data ---
    if platform.system() == "Windows":  # Chrome/Edge paths are most common on Windows
        chrome_history = get_chrome_history(user_profile)
        all_browser_data["chrome_edge_history"] = chrome_history

        chrome_downloads = get_chrome_downloads(user_profile)
        all_browser_data["chrome_edge_downloads"] = chrome_downloads

    # --- Collect Firefox Data ---
    # Firefox paths are more consistent across OSes, but the AppData/Library parts differ
    firefox_history = get_firefox_history(user_profile)
    all_browser_data["firefox_history"] = firefox_history

    firefox_downloads = get_firefox_downloads(user_profile)  # This one is more complex
    all_browser_data["firefox_downloads"] = firefox_downloads

    # --- Output ---
    output_filename = f"browser_activity_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_dir = Path("browser_data_collection")
    output_dir.mkdir(parents=True, exist_ok=True)
    full_output_path = output_dir / output_filename

    try:
        with open(full_output_path, "w", encoding="utf-8") as f:
            json.dump(all_browser_data, f, indent=4, ensure_ascii=False)
        print(f"\nAll collected browser data saved to: {full_output_path}")
    except Exception as e:
        print(f"\nError saving data to JSON: {e}")
        print("\n--- Raw Data (if saving failed) ---")
        # Fallback to printing if file save fails
        for key, value_dict in all_browser_data.items():
            print(f"\n--- {key} ---")
            if value_dict and "data" in value_dict:
                for item in value_dict["data"][:5]:  # Print first 5 items as sample
                    print(item)
                if len(value_dict["data"]) > 5:
                    print(f"... and {len(value_dict['data']) - 5} more items.")
            else:
                print(value_dict)

    print("\nReminder: Ensure you have proper authorization before accessing user data.")