import datetime
import os
import subprocess
import time

from ossapi import OssapiV2, RankingType, UserStatistics, Score, Cursor

from osu_collections import Collection, CollectionDB
from osu_db import parse_osu_db

if __name__ == "__main__":
    api = OssapiV2(os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET'))
    osu_folder = r'E:\osu!'

    osu_db_path = os.path.join(osu_folder, 'osu!.db')
    osu_collections_path = os.path.join(osu_folder, 'collection.db')
    osu_exe_path = os.path.join(osu_folder, 'osu!.exe')

    beatmap_ids = parse_osu_db(osu_db_path)
    already_downloaded = set()

    top_player_page_start = 1
    top_player_page_end = 3
    beatmaps_dict = {}

    collections_db = CollectionDB(osu_collections_path)
    try:
        for page_num in range(top_player_page_start, top_player_page_end):
            cursor = Cursor(page=page_num)
            rankings = api.ranking("osu", RankingType.PERFORMANCE, cursor=cursor)
            time.sleep(0.5)
            print(f'Looking at page {page_num} of top rankings.')
            for rank in rankings.ranking:
                rank: UserStatistics
                user_id = rank.user.id
                username = rank.user.username
                best_scores = api.user_scores(user_id, "best", mode='osu', limit=50)
                time.sleep(0.5)
                best_scores.extend(api.user_scores(user_id, "best", mode='osu', limit=50, offset=50))
                time.sleep(0.4)

                print(f'Looking at top scores of {username} - {len(best_scores)} scores collected.')
                for score in best_scores:
                    score: Score
                    score_modifier = str(score.mods)
                    beatmap_id = score.beatmap.id
                    beatmap_hash = score.beatmap.checksum
                    if score_modifier in beatmaps_dict:
                        beatmaps_dict[score_modifier].add_beatmap(beatmap_hash)
                    else:
                        collection_name = f"{datetime.datetime.now().strftime('%Y-%m-%d')}.{score_modifier}"
                        beatmaps_dict[score_modifier] = Collection.from_values(name=collection_name,
                                                                               beatmap_hashes=[beatmap_hash])

                    if not (beatmap_id in beatmap_ids) and not (beatmap_id in already_downloaded):
                        subprocess.Popen([osu_exe_path, f'osu://b/{beatmap_id}'],
                                         close_fds=True, creationflags=0x00000008)
                        already_downloaded.add(beatmap_id)
    except KeyboardInterrupt:
        pass
    finally:
        for modifier, collection in beatmaps_dict.items():
            collections_db.add_collection(collection)
