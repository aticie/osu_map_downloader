import datetime
import json
import os
import time
from typing import Tuple, List

from ossapi import OssapiV2, RankingType, UserStatistics, Score, Cursor, Mod

from osu_collections import Collection, CollectionDB
from osu_db import parse_osu_db
from osu_finder import check_registry_entry_for_osu


class MapDownloader:
    def __init__(self, rank_search_range: Tuple = (100, 300), pp_range: Tuple = (580, 1000),
                 accuracy_range: Tuple = (0.90, 0.995), collection_creation_threshold: int = 10):
        self.api = OssapiV2(os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET'))
        osu_path = check_registry_entry_for_osu()

        self.collection_creation_threshold = collection_creation_threshold

        self.osu_db_path = os.path.join(osu_path, 'osu!.db')
        self.osu_collections_path = os.path.join(osu_path, 'collection.db')
        self.osu_exe_path = os.path.join(osu_path, 'osu!.exe')

        self.beatmap_ids = parse_osu_db(self.osu_db_path)

        self.acc_range = accuracy_range
        self.rank_range = rank_search_range
        self.pp_range = pp_range

        self.rank_page_start = rank_search_range[0] // 50 + 1
        self.rank_page_start_offset = rank_search_range[0] % 50 - 1 if rank_search_range[0] != 50 else 0

        self.rank_page_end = rank_search_range[1] // 50 + 2
        self.rank_page_end_offset = rank_search_range[1] % 50 if rank_search_range[1] != 50 else 0

        self.collections_db = CollectionDB(self.osu_collections_path)
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')

    def search(self):
        downloaded_maps = set()
        beatmaps_dict = {}
        all_scores = []
        for page_num in range(self.rank_page_start, self.rank_page_end):
            cursor = Cursor(page=page_num)
            rankings = self.api.ranking("osu", RankingType.PERFORMANCE, cursor=cursor)
            user_rankings = rankings.ranking
            if page_num == self.rank_page_start:
                user_rankings = user_rankings[self.rank_page_start_offset:]
            if page_num == self.rank_page_end:
                user_rankings = user_rankings[:self.rank_page_end_offset]
            time.sleep(0.3)

            for rank in user_rankings:
                rank: UserStatistics
                user_id = rank.user.id
                username = rank.user.username
                best_scores = self.api.user_scores(user_id, "best", mode='osu', limit=50)
                time.sleep(0.3)
                best_scores.extend(self.api.user_scores(user_id, "best", mode='osu', limit=50, offset=50))
                time.sleep(0.3)

                filtered_scores = self.filter_by_acc(best_scores)
                filtered_scores = self.filter_by_pp(filtered_scores)
                print(f'Looking at top scores of {username} - {len(filtered_scores)} scores collected.')
                all_scores.extend(filtered_scores)
                for score in filtered_scores:
                    score: Score

                    if Mod('NC') in score.mods:
                        score.mods = score.mods - Mod(21101) + Mod('DT')
                    else:
                        score.mods -= Mod(21101)

                    score_modifier = f'{str(score.mods)}(HD)'
                    beatmap_id = score.beatmap.id
                    beatmap_hash = score.beatmap.checksum
                    if score_modifier in beatmaps_dict:
                        beatmaps_dict[score_modifier].add_beatmap(beatmap_hash)
                    else:
                        collection_name = f"{self.today}.{score_modifier}"
                        beatmaps_dict[score_modifier] = Collection.from_values(name=collection_name,
                                                                               beatmap_hashes=[beatmap_hash])

                    if not (beatmap_id in self.beatmap_ids) and not (beatmap_id in downloaded_maps):
                        downloaded_maps.add(beatmap_id)

        for modifier, collection in beatmaps_dict.items():
            if collection.num_beatmaps > self.collection_creation_threshold:
                self.collections_db.add_collection(collection)

        with open(f'score_list_{self.today}.json', 'w') as f:
            json.dump(all_scores, f, indent=2)

        with open(f'download_list_{self.today}.txt', 'w') as f:
            for map_id in downloaded_maps:
                print(map_id, file=f)

    def filter_by_acc(self, scores: List[Score]):
        return [score for score in scores if self.acc_range[1] > score.accuracy > self.acc_range[0]]

    def filter_by_pp(self, scores: List[Score]):
        return [score for score in scores if self.pp_range[1] > score.pp > self.pp_range[0]]


if __name__ == "__main__":
    try:
        m = MapDownloader()
        m.search()
    except Exception as e:
        print(e)
        input("Press enter to exit...")
