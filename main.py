import os
import subprocess
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, USER_ID, BASE_OUTPUT_PATH

# Initialize Spotipy client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope="playlist-read-private"))

def get_user_playlists(user_id):
    """
    Fetch all playlist links and names for the given user ID.
    """
    playlists_data = []  # List to store (playlist_name, playlist_url) tuples
    offset = 0
    limit = 50  # Maximum number of playlists per request

    while True:
        try:
            # Fetch playlists with pagination
            playlists = sp.user_playlists(user_id, offset=offset, limit=limit)
            print(playlists)  # Debugging: Print the API response
            if not playlists or 'items' not in playlists:
                print("No playlists found or invalid response.")
                break

            # Add playlist names and URLs to the list
            for playlist in playlists['items']:
                playlist_name = playlist['name']
                playlist_url = playlist['external_urls']['spotify']
                playlists_data.append((playlist_name, playlist_url))

            # Check if there are more playlists to fetch
            if playlists['next']:
                offset += limit
            else:
                break

        except Exception as e:
            print(f"Error fetching playlists: {e}")
            break

    return playlists_data

def download_playlist(playlist_url, output_folder):
    """
    Use spotdl CLI to download a playlist into the specified folder.
    """
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Use spotdl CLI to download the playlist
    # Use the current Python executable to run spotdl
    python_executable = sys.executable  # Path to the current Python interpreter
    command = f'"{python_executable}" -m spotdl --bitrate 192k  {playlist_url} --output "{output_folder}"'

    try:
        print(f"Downloading playlist: {playlist_url}")
        subprocess.run(command, shell=True, check=True)
        print(f"Downloaded playlist to {output_folder}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to download playlist: {e}")

def main(user_id, base_output_path):
    """
    Main function to fetch playlists and download them.
    """
    # Get all playlist names and links for the user
    playlists_data = get_user_playlists(user_id)

    if not playlists_data:
        print("No playlists found for the user.")
        return

    for playlist_name, playlist_url in playlists_data:
        # Create a folder for the playlist using its name
        # Replace invalid characters in the playlist name (e.g., slashes)
        safe_playlist_name = "".join(c if c.isalnum() or c in " -_." else "_" for c in playlist_name)
        output_folder = os.path.join(base_output_path, safe_playlist_name)

        try:
            # Download the playlist
            download_playlist(playlist_url, output_folder)
        except KeyboardInterrupt:
            # Handle Ctrl+C: Skip to the next playlist
            print(f"\nSkipping playlist: {playlist_name}")
            continue

if __name__ == "__main__":
    # Run the script
    main(USER_ID, BASE_OUTPUT_PATH)