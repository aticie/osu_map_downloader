import datetime
import os
import subprocess
import time

from osu_collections import CollectionDB
from osu_db import parse_osu_db
from osu_finder import check_registry_entry_for_osu


class MapDownloader:
    def __init__(self):
        osu_path = check_registry_entry_for_osu()

        print(f'Found osu! folder at {osu_path}')

        self.osu_db_path = os.path.join(osu_path, 'osu!.db')
        self.osu_collections_path = os.path.join(osu_path, 'collection.db')
        self.osu_exe_path = os.path.join(osu_path, 'osu!.exe')

        self.beatmap_ids = parse_osu_db(self.osu_db_path)

        self.collections_db = CollectionDB(self.osu_collections_path)
        print(f'You have {len(self.collections_db.collections)} collections.')

        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.downloaded_maps = set()
        self.beatmaps_dict = {}
        self.all_scores = []

        self.continuous_download = False

    def from_txt(self, txt_path):
        with open(txt_path) as f:
            beatmap_ids = f.read().splitlines()

        skipped_beatmaps = []
        bmap_no = 0
        for bmap_id in beatmap_ids:
            bmap_id = int(bmap_id)
            if bmap_id in self.beatmap_ids or bmap_id in self.downloaded_maps:
                skipped_beatmaps.append(bmap_id)
                continue

            subprocess.Popen([self.osu_exe_path, f'osu://b/{bmap_id}'],
                             close_fds=True, creationflags=0x00000008)
            bmap_no += 1
            if not self.continuous_download:
                if bmap_no % 10 == 0:
                    print(f'Skipped {len(skipped_beatmaps)} beatmaps. (Already downloaded)')
                    continue_dl = input(f'{bmap_no} maps queued for download. Continue? [y/n/a]')
                    if continue_dl.lower() == 'n':
                        return
                    elif continue_dl.lower() == 'a':
                        self.continuous_download = True
                    else:
                        pass
            time.sleep(1)


if __name__ == "__main__":
    try:
        m = MapDownloader()
        m.from_txt('beatmaps.txt')
    except Exception as e:
        print(e)
        input("Press enter to exit...")
