import os
import subprocess
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, USER_ID, BASE_OUTPUT_PATH
import multiprocessing  # To detect CPU cores

# Initialize Spotipy client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope="playlist-read-private"))

def get_user_playlists(user_id):
    playlists_data = []
    offset = 0
    limit = 50

    while True:
        try:
            playlists = sp.user_playlists(user_id, offset=offset, limit=limit)
            if not playlists or 'items' not in playlists:
                break

            for playlist in playlists['items']:
                playlist_name = playlist['name']
                playlist_url = playlist['external_urls']['spotify']
                playlists_data.append((playlist_name, playlist_url))

            if playlists['next']:
                offset += limit
            else:
                break

        except Exception as e:
            print(f"Error fetching playlists: {e}")
            break

    return playlists_data

def download_playlist(playlist_url, output_folder):
    import shlex

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    python_executable = sys.executable
    cpu_threads = multiprocessing.cpu_count()  # All CPU threads

    command = f'"{python_executable}" -m spotdl download "{playlist_url}" --threads {cpu_threads} --output "{output_folder}"'
    command_list = shlex.split(command)  # Safe splitting for subprocess

    print(f"Downloading playlist: {playlist_url} (per-song timeout:240s)")

    try:
        # subprocess.run with timeout per call
        subprocess.run(command_list, timeout=600, check=True)
        print(f"Downloaded playlist to {output_folder}")
    except subprocess.TimeoutExpired:
        print(f"Song download exceeded  skipping to next.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to download playlist: {e}")

def main(user_id, base_output_path):
    playlists_data = get_user_playlists(user_id)

    if not playlists_data:
        print("No playlists found for the user.")
        return

    for playlist_name, playlist_url in playlists_data:
        safe_playlist_name = "".join(c if c.isalnum() or c in " -_." else "_" for c in playlist_name)
        output_folder = os.path.join(base_output_path, safe_playlist_name)

        try:
            download_playlist(playlist_url, output_folder)
        except KeyboardInterrupt:
            print(f"\nSkipping playlist: {playlist_name}")
            continue

if __name__ == "__main__":
    main(USER_ID, BASE_OUTPUT_PATH)
