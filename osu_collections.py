import struct
from typing import List, BinaryIO

from osu_db import ByteInt, osuString


class Collection:
    def __init__(self):
        self.name = ''
        self.num_beatmaps = 0
        self.beatmap_hashes = []

    @classmethod
    def from_fileptr(cls, fileptr: BinaryIO):
        collection = cls()
        collection.name = osuString(fileptr)
        collection.num_beatmaps = ByteInt(fileptr.read(4))
        collection.beatmap_hashes = [osuString(fileptr) for _ in range(collection.num_beatmaps)]
        return collection

    @classmethod
    def from_values(cls, name: str, beatmap_hashes: List[str]):
        collection = cls()
        collection.name = name
        collection.num_beatmaps = len(beatmap_hashes)
        collection.beatmap_hashes = beatmap_hashes
        return collection

    def write_self(self, fileptr: BinaryIO):
        osuString.write_string(self.name, fileptr)
        fileptr.write(struct.pack("<I", self.num_beatmaps))
        for md5_hash in self.beatmap_hashes:
            osuString.write_string(md5_hash, fileptr)

    def add_beatmap(self, beatmap_hash):
        if not beatmap_hash in self.beatmap_hashes:
            self.num_beatmaps += 1
            self.beatmap_hashes.append(beatmap_hash)


class CollectionDB:
    def __init__(self, collection_path):
        self.collection_path = collection_path
        with open(collection_path, 'rb') as f:
            self.version = ByteInt(f.read(4))
            self.collection_num = ByteInt(f.read(4))
            self.collections = [Collection.from_fileptr(f) for _ in range(self.collection_num)]

    def add_collection(self, collection: Collection):
        self.collection_num += 1
        with open(self.collection_path, 'r+b') as fh:
            fh.seek(4)
            fh.write(struct.pack("<I", self.collection_num))

        with open(self.collection_path, 'ab') as f:
            collection.write_self(f)
