import __main__
import argparse
import logging
import re
import time
from datetime import datetime
from os.path import dirname, basename, splitext, sep

# https://ytmusicapi.readthedocs.io/en/stable/
from ytmusicapi import YTMusic

VID_PATTERN = r"""^.*(?:(?:youtu\.be\/|v\/|vi\/|u\/\w\/|embed\/|shorts\/)|(?:(?:watch)?\?v(?:i)?=|\&v(?:i)?=))([^#\&\?]*).*"""
PID_PATTERN = r"""^.*(?:(?:youtu\.be\/|v\/|vi\/|u\/\w\/|embed\/|shorts\/)|(?:(?:watch)?\?list(?:i)?=|\&v(?:i)?=))([^#\&\?]*).*"""


def setup_logger():
    outdir = dirname(__main__.__file__)
    base_py = basename(__main__.__file__)
    base = splitext(base_py)[0]
    logging.basicConfig(format="[%(name)s][%(levelname)s] %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        level=logging.INFO,
                        handlers=[
                            logging.FileHandler(
                                f"{outdir + sep + 'logs' + sep + base}_{time.strftime('%Y%m%d%H%M%S')}.log"),
                            logging.StreamHandler()
                        ])
    return logging.getLogger(base_py)


def create_playlist(ytmusic):
    return ytmusic.create_playlist(
        f'Generated playlist ({datetime.fromtimestamp(datetime.now().timestamp())})',
        'Playlist created by youtube-playlist-generator v2.'
    )


if __name__ == '__main__':
    logger = setup_logger()

    parser = argparse.ArgumentParser()
    parser.add_argument('--file',
                        help='File containing list of youtube videos and playlists.')
    parser.add_argument('--playlist_id',
                        nargs='?',
                        help='ID of youtube playlist to insert into.')
    parser.add_argument('--oauth',
                        nargs='?',
                        help='Json file containing oauth info.')
    parser.add_argument('--browser',
                        nargs='?',
                        help='Json file containing browser authentication info.')

    args = parser.parse_args()
    oauth = args.oauth
    browser = args.browser
    ytmusic = YTMusic(oauth if oauth else browser if browser else "oauth.json")

    playlist_id = args.playlist_id if args.playlist_id else create_playlist(ytmusic)
    print(f"Playlist ID: {playlist_id}\n\n")

    offset = 7125
    for i, url in enumerate(open(args.file).read().splitlines()[offset:]):
        while True:
            time.sleep(2)
            info = ''

            try:
                if 'watch' in url:
                    vid = re.match(VID_PATTERN, url)[1]
                    info = f'vid: {vid}'
                    response = ytmusic.add_playlist_items(playlist_id, [vid])
                else:
                    pid = re.match(PID_PATTERN, url)[1]
                    info = f'pid: {pid}'
                    response = ytmusic.add_playlist_items(playlist_id, source_playlist=pid)

                logger.info(f'Response ({info}), index {offset + i}:\n\n{response}\n')

                break
            except Exception as e:
                str = e.__str__()

                logger.error(f'Exception occurred ({info}), index {offset + i}:\n\n\t{str}\n')

                if 'Maximum playlist size exceeded.' in str:
                    playlist_id = create_playlist(ytmusic)
                    continue
                elif '400' in str or '404' in str:
                    break

                exit(2)
