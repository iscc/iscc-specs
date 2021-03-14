# -*- coding: utf-8 -*-
"""Persistent inverted index for ISCCs, components and granular features.

Subdatabases
1.  iscc_none_v0_256
----------------------------
2.  meta_code_v0_64
3.  content_text_v0_64
4.  content_image_v0_64
4.  content audio_v0_64
5.  content video_v0_64
6.  data_code_v0_64
8.  instance_code_v0_64
----------------------------
9.  feat_text_v0_64
10. feat_image_v0_64
11. feat_audio_v0_64
12. feat_video_v0_64
----------------------------
13. metdata
"""
from os.path import join
from typing import List, Optional, Dict
from loguru import logger as log
import iscc
import lmdb
import struct
import shutil
from humanize import naturalsize


pack = lambda n: struct.pack("I", n)
unpack = lambda b: struct.unpack("I", b)[0]


class Index:
    def __init__(self, name="iscc-db", **options):
        """Create or open existing index.

        :param str name: Name of index.
        :param bool index_components: Create inverted index of components -> iscc
        :param bool index_features: Create inverted index of features -> iscc
        :param bool store_metadata: Store metadata in index.
        """

        self.name = name
        self.dbpath = join(iscc.APP_DIR, self.name)
        log.info(f"init storage at {self.dbpath}")
        self.env = lmdb.open(
            path=self.dbpath,
            map_size=2 ** 20,
            max_dbs=24,
            metasync=False,
            sync=False,
            readahead=False,
            writemap=False,
            meminit=False,
            map_async=True,
        )

    @property
    def map_size(self) -> int:
        return self.env.info()["map_size"]

    def add(self, code, features=None):
        # type: (str, Optional[List[Dict]]) -> int
        """Add an ISCC to the index."""

        # Check for duplicate
        exists = self.get_id(code)
        if exists is not None:
            return exists

        # Normalize
        components = iscc.decompose(code)
        iscc_obj = iscc.compose(components)

        # Add full code sequence to main index
        db = self.db_isccs()
        mainkey = self.next_key()
        self.put(db, mainkey, iscc_obj.bytes)

        # Add components to components index
        db = self.db_components()
        items = [(code.bytes, mainkey) for code in components]
        self.putmulti(db, items)

        # Add feature hashes
        features = [] if features is None else features
        for fobj in features:
            db = self.db_features(kind=fobj["kind"])
            items = [(iscc.decode_base64(f), mainkey) for f in fobj["features"]]
            self.putmulti(db, items)

        return unpack(mainkey)

    def get_id(self, code) -> Optional[int]:
        """Get internal ID of for ISCC"""
        # Find per component matches
        components = iscc.decompose(code)
        db = self.db_components()
        idxs = []
        with self.env.begin(db=db) as txn:
            for code in components:
                idx = txn.get(code.bytes)
                if idx is not None:
                    idxs.append(idx)
        # Check if any of the full code entries is an exact match
        full_code_bytes = iscc.compose(components).bytes
        db = self.db_isccs()
        with self.env.begin(db=db) as txn:
            for idx in idxs:
                if txn.get(idx) == full_code_bytes:
                    return unpack(idx)

    def add_component(self, code, pk):
        # type: (iscc.Code, bytes) -> None
        db = self.db(code.type_id.encode("ascii"))
        self.put(db, code.hash_bytes, pk)

    def next_key(self) -> bytes:
        """Next free autoincrement id as 4-byte key"""
        db = self.db_isccs()
        with self.env.begin(db) as txn:
            with txn.cursor(db) as c:
                empty = not c.last()
                idx = unpack(c.key()) + 1 if not empty else 0
        return pack(idx)

    def put(self, db, key: bytes, value: bytes):
        try:
            with self.env.begin(db, write=True) as txn:
                txn.put(key, value)
        except lmdb.MapFullError:
            new_size = self.map_size * 2
            log.info(f"Resizing {self.dbpath} to {naturalsize(new_size)}")
            self.env.set_mapsize(self.map_size * 2)
            with self.env.begin(db, write=True) as txn:
                txn.put(key, value)

    def putmulti(self, db, items, dupdata=True, overwrite=True):
        try:
            with self.env.begin(db, write=True) as txn:
                with txn.cursor(db) as c:
                    c.putmulti(items, dupdata=dupdata, overwrite=overwrite)
        except lmdb.MapFullError:
            new_size = self.map_size * 2
            log.info(f"Resizing {self.dbpath} to {naturalsize(new_size)}")
            self.env.set_mapsize(self.map_size * 2)
            with self.env.begin(db, write=True) as txn:
                with txn.cursor(db) as c:
                    c.putmulti(items, dupdata=dupdata, overwrite=overwrite)

    def isccs(self):
        """Iterates over indexed ISCC codes in insertion order."""
        db = self.db_isccs()
        with self.env.begin(db) as txn:
            with txn.cursor(db) as c:
                while c.next():
                    yield c.value()

    def iscc(self, idx: int) -> bytes:
        """Get ISCC by index id"""
        db = self.db_isccs()
        with self.env.begin(db) as txn:
            return txn.get(pack(idx))

    def components(self):
        """Itereates over indexed components."""
        db = self.db_components()
        with self.env.begin(db) as txn:
            with txn.cursor(db) as c:
                for key in c.iternext_nodup():
                    yield key

    def dbs(self) -> List[str]:
        """Return a list of existing sub-databases in the index."""
        dbnames = []
        with self.env.begin() as txn:
            c = txn.cursor()
            while c.next():
                dbnames.append(c.key())
        return dbnames

    def destory(self):
        """Close and delete index from disk."""
        self.env.close()
        shutil.rmtree(self.dbpath)

    def close(self):
        """Close index."""
        self.env.close()

    def db_isccs(self):
        return self.env.open_db(b"isccs", integerkey=True, create=True)

    def db_components(self):
        return self.env.open_db(
            b"components", dupsort=True, integerdup=True, create=True, dupfixed=True
        )

    def db_features(self, kind):
        return self.env.open_db(
            kind.encode("utf-8"),
            dupsort=True,
            integerkey=True,
            integerdup=True,
            create=True,
            dupfixed=True,
        )

    def __len__(self):
        """Number of indexed ISCCs"""
        db = self.db_isccs()
        with self.env.begin(db) as txn:
            stat = txn.stat(db)
            return stat.get("entries")

    def __contains__(self, item):
        """Check if full iscc code is in index."""
        id_ = self.get_id(item)
        return False if id_ is None else True


if __name__ == "__main__":
    idx = Index()
    len(idx)
