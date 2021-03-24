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
import os
from os.path import join
from typing import List, Optional, Dict, Any, Union
from loguru import logger as log
import iscc
import lmdb
import shutil
from humanize import naturalsize
from iscc.schema import Options, ISCC
import msgpack


IsccObj = Union[str, Dict, iscc.Code, ISCC]
Key = Union[int, str]


class Index:
    def __init__(self, name="iscc-db", **options):
        # type: (str, **Any) -> Index
        """Create or open existing index.

        :param str name: Name of index.
        :param str index_root: The root path for databases.
        :param bool index_components: Create inverted index of components -> iscc.
        :param bool index_features: Create inverted index of features -> iscc.
        :param bool index_metadata: Store metadata in index.
        """

        self.opts = Options(**options)

        self.name = name
        self.dbpath = join(self.opts.index_root, self.name)
        log.debug(f"init index storage at {self.dbpath}")
        os.makedirs(self.dbpath, exist_ok=True)
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

    def add(self, iscc_obj, key=None):
        # type: (IsccObj, Optional[Key]) -> Key
        """Add an ISCC to the index.

        The ISCC can be provided as a string or Code object. Alternatively you can pass
        the ISCC wrapped in a schema.ISCC object or conforming dict. This is required
        if granular features should be indexed or if you want to store ISCC metadata
        in the index.

        Optionally you may provide a unique key (str or int) to map entries to your
        external database. If no key is provided the index will create and return
        an autoincremented integer id. Do not mix both aproaches.

        :param IsccObj iscc_obj: ISCC str, Code, schema.ISCC or conforming dict.
        :param Key key: Optional primary key (int or str).
        """
        metadata = None
        features = None

        if isinstance(iscc_obj, str):
            iscc_code = iscc.Code(iscc_obj)
        elif isinstance(iscc_obj, iscc.Code):
            iscc_code = iscc_obj
        elif isinstance(iscc_obj, ISCC):
            iscc_code = iscc.Code(iscc_obj.iscc)
            metadata = iscc_obj.dict(exclude_unset=True)
            features = metadata.get("features")
        elif isinstance(iscc_obj, dict):
            iscc_code = iscc.Code(iscc_obj["iscc"])
            metadata = iscc_obj
            features = metadata.get("features")
        else:
            raise ValueError(
                f"'iscc_obj' must be str or dict with 'iscc' key not {type(iscc_obj)}."
            )

        # Check for duplicate ISCC
        exists = self.get_key(iscc_code)
        if exists is not None:
            return exists

        # Normalize
        components = iscc.decompose(iscc_code)
        iscc_code = iscc.compose(components)

        # Add canonical ISCC to main index
        db = self.db_isccs()
        if key is None:
            key = self.next_key()

        keyb = msgpack.dumps(key)

        self._put(db, keyb, iscc_code.bytes)

        # Add components to components index
        if self.opts.index_components:
            db = self.db_components()
            items = [(code.bytes, keyb) for code in components]
            self.putmulti(db, items)

        # Add feature hashes
        if self.opts.index_features and features is not None:
            for fobj in features:
                # feat -> (pk, pos)
                # itmes -> [(feat, (pk,pos)), ... ]
                items = []
                pos = 0
                for feat, size in zip(fobj["features"], fobj["sizes"]):
                    item = iscc.decode_base64(feat), msgpack.dumps((key, pos))
                    items.append(item)
                    pos += size
                db = self.db_features(kind=fobj["kind"])
                self.putmulti(db, items)

        # Add metadata
        if self.opts.index_metadata and metadata is not None:
            db = self.db_metadata()
            self._put(db, keyb, msgpack.dumps(metadata))

        return key

    def get_key(self, code) -> Optional[int]:
        """Get first internal key for an ISCC if any."""
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
                    return msgpack.loads(idx)

    def next_key(self) -> bytes:
        """Next free autoincrement key"""
        db = self.db_isccs()
        with self.env.begin(db) as txn:
            with txn.cursor(db) as c:
                empty = not c.last()
                key = msgpack.loads(c.key()) + 1 if not empty else 0
        return key

    def _put(self, db, key: bytes, value: bytes, dupdata=True, overwrite=True):
        """Wrap LMDB put in a transaction and autorisize db if required."""
        try:
            with self.env.begin(db, write=True) as txn:
                txn.put(key, value, dupdata=dupdata, overwrite=overwrite)
        except lmdb.MapFullError:
            new_size = self.map_size * 2
            log.info(f"Resizing {self.dbpath} to {naturalsize(new_size)}")
            self.env.set_mapsize(self.map_size * 2)
            with self.env.begin(db, write=True) as txn:
                txn.put(key, value, dupdata=dupdata, overwrite=overwrite)

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

    def get_iscc(self, key: Key) -> iscc.Code:
        """Get ISCC by index key"""
        db = self.db_isccs()
        with self.env.begin(db) as txn:
            iscc_bytes = txn.get(msgpack.dumps(key))
            if iscc_bytes:
                return iscc.Code(iscc_bytes)

    def components(self):
        """Itereates over indexed components."""
        db = self.db_components()
        with self.env.begin(db) as txn:
            with txn.cursor(db) as c:
                for key in c.iternext_nodup():
                    yield key

    def dbs(self) -> List[str]:
        """Return a list of existing sub-databases in the main index."""
        dbnames = []
        with self.env.begin() as txn:
            c = txn.cursor()
            while c.next():
                dbnames.append(c.key())
        return dbnames

    def destory(self):
        """Close and delete index from disk."""
        self.env.close()
        log.debug(f"delete index storage at {self.dbpath}")
        shutil.rmtree(self.dbpath)

    def close(self):
        """Close index."""
        self.env.close()

    def db_isccs(self):
        return self.env.open_db(b"isccs", integerkey=False, create=True)

    def db_components(self):
        return self.env.open_db(
            b"components", dupsort=True, integerdup=True, create=True, dupfixed=True
        )

    def db_features(self, kind):
        return self.env.open_db(
            kind.encode("utf-8"),
            dupsort=True,
            integerkey=True,
            integerdup=False,
            create=True,
            dupfixed=False,
        )

    def db_metadata(self):
        return self.env.open_db(b"metadata", integerkey=True, create=True)

    def _add_component(self, code: bytes, fkey: bytes):
        """Add a component to the index with a pointer to its source ISCC."""
        db = self.db_components()
        self._put(db, code, fkey)

    def __len__(self):
        """Number of indexed ISCCs"""
        db = self.db_isccs()
        with self.env.begin(db) as txn:
            stat = txn.stat(db)
            return stat.get("entries")

    def __contains__(self, item):
        """Check if full iscc code is in index."""
        key = self.get_key(item)
        return False if key is None else True


if __name__ == "__main__":
    idx = Index()
    len(idx)
    idx.destory()
