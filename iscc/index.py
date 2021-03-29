# -*- coding: utf-8 -*-
"""Persistent inverted index for ISCC components and granular features.

ISCCs are stored in their raw-bytes representation. All other keys and values are
serialized to bytes with MessagePack.

We use LMDB `dupsort` to store multiple values per key and `set_range` to iterate
compatible (matchable) components by prefix. Features are indexed in separate
sub-databases per feature-type and version.


Database Structure:

    isccs:
        key -> iscc

    components:
        component -> key1..keyx

    features-<type>-<version>:
        feature .>  (key1, pos1)..(key1, pos1)

    metadata:
        key -> metadata

The `components` inverted index can be rebuild from the `isccs`-table.
The `features` inverted indexes can be rebuild from the `metadata`-table if available.
"""
import os
from os.path import join
from typing import List, Optional, Dict, Any, Tuple, Union, Set, Generator
from loguru import logger as log
import iscc
import lmdb
import shutil
from humanize import naturalsize
from iscc.schema import FeatureMatch, IsccMatch, QueryResult, Options, ISCC
import msgpack


IsccObj = Union[str, Dict, iscc.Code, ISCC]
Key = Union[int, str, bytes]


class Index:
    def __init__(self, name="iscc-db", readonly=False, **options):
        # type: (str, bool, **Any) -> Index
        """Open a named index or create a new one with `name`.

        A given index can only have one concurrent writer. Multiple readers are
        allowed (open with readonly=True).

        name (str): Name of the index (default iscc-db).
        index_root (str): The root path for index databases (default APP_DIR).
        index_components (bool): Create inverted index of components (default True).
        index_features (bool): Create inverted index of features (default False).
        index_metadata (bool): Store metadata in index (default False).
        """

        self.opts = Options(**options)

        self.name = name
        self.dbpath = join(self.opts.index_root, self.name)
        log.debug(f"init index storage at {self.dbpath}")
        os.makedirs(self.dbpath, exist_ok=True)
        self.env = lmdb.open(
            path=self.dbpath,
            map_size=2 ** 20,
            readonly=readonly,
            max_dbs=24,
        )

    def add(self, iscc_obj, key=None):
        # type: (IsccObj, Optional[Key]) -> Key
        """Add an ISCC to the index.

        iscc_obj: ISCC str, Code, schema.ISCC or conforming dict.
        key: Optional primary key (int or str).

        The ISCC can be provided as a string or Code object. Alternatively you can pass
        the ISCC wrapped in a schema.ISCC object or conforming dict. This is required
        if granular features should be indexed or if you want to store ISCC metadata
        in the index.

        Optionally you may provide a unique key (str or int) to map entries to your
        external database. If no key is provided the index will create and return
        an autoincremented integer id. Do not mix both aproaches.
        """

        iscc_code, features, metadata = self._parse_iscc_obj(iscc_obj)

        # Check for duplicate ISCC
        exists = self.get_key(iscc_code)
        if exists is not None:
            return exists

        # Normalize
        components = iscc.decompose(iscc_code)
        iscc_code = iscc.compose(components)

        # Add canonical ISCC to main index
        db = self._db_isccs()
        if key is None:
            key = self._next_key()

        keyb = msgpack.dumps(key)

        self._put(db, keyb, iscc_code.bytes)

        # Add components to components index
        if self.opts.index_components:
            for code in components:
                self._add_component(code.bytes, keyb)

        # Add feature hashes
        if self.opts.index_features and features is not None:
            for fobj in features:
                pos = 0
                for feat, size in zip(fobj["features"], fobj["sizes"]):
                    self._add_feature(fobj["kind"], iscc.decode_base64(feat), keyb, pos)
                    pos += size

        # Add metadata
        if self.opts.index_metadata and metadata is not None:
            db = self._db_metadata()
            self._put(db, keyb, msgpack.dumps(metadata))

        return key

    def query(self, iscc_obj, k=10, ct=10, ft=4):
        # type: (IsccObj, int, int, int) -> QueryResult
        """Find nearest neighbours for ISCCs.

        Query strategy:
            We first match ISCCs by per-component similarity with a threshold of
            of maximum `ct` bits of hamming distance. IsccMatch results are sorted
            by distance (lowest distance first) and the top-`k` results are returned.

            Additionally granular features are also matched with a maximum threshold
            of `ft` bits if features are indexed and included in the query-`IsccObj`.
            The top-`k` `FeatureMatch` results are sorted by distance and will not
            include ISCCs that have already been matched by the previous component
            matching.
        """

        source_iscc, features, metadata = self._parse_iscc_obj(iscc_obj)
        iscc_matches = set()
        seen_fkeys = set()

        # Collect ISCC component level matches
        for comp_obj in reversed(iscc.decompose(source_iscc)):
            for fkey in self.match_component(comp_obj, ct=ct):
                if fkey not in seen_fkeys:
                    iscc_matches.add(self._build_match(source_iscc, fkey))
                    seen_fkeys.add(fkey)

        # Collect ISCC feature level matches
        feature_matches = set()
        for feat_obj in features:
            kind = feat_obj["kind"]
            for src_feat in feat_obj["features"]:
                for fm in self.match_feature(kind, src_feat, ft=ft, ignore=seen_fkeys):
                    feature_matches.add(fm)

        return QueryResult(
            iscc_matches=sorted(iscc_matches)[:k],
            feature_matches=sorted(feature_matches)[:k],
        )

    def match_component(self, code, ct=0):
        # type: (iscc.Code, int) -> List[bytes]
        """
        Match ISCCs (fkeys) by given commponent with threshold `ct` (max distance).
        """
        db = self._db_components()

        if code.maintype == iscc.MT.INSTANCE or ct == 0:
            # Simple get if instance code or threshold is 0
            return self._get_values(db, code.bytes)
        else:
            # TODO: pluck ANNS search here if available
            # Scan for nearest neighbors
            fkeys = set()
            prefix = code.header_bytes
            with self.env.begin(db) as txn:
                with txn.cursor(db) as c:
                    c.set_range(prefix)
                    for k in c.iternext_nodup(keys=True, values=False):
                        if not k.startswith(prefix):
                            break
                        candidate = iscc.Code(k)
                        distance = iscc.distance_ba(code.hash_ba, candidate.hash_ba)
                        if distance > ct:
                            continue
                        c2 = txn.cursor(db)
                        c2.set_key(k)
                        for v in c2.iternext_dup(keys=False, values=True):
                            fkeys.add(v)
                        c2.close()
            return list(fkeys)

    def match_feature(self, kind, feature, ft=0, ignore=None):
        # type: (str, Union[str,bytes], int, Set[bytes]) -> List[FeatureMatch]
        """
        Match ISCCs by a given feature with feature threshold `ft` (max distance).
        Ignore matches for fkeys in `ignore`.
        """

        if isinstance(feature, str):
            feature_raw, feature_str = iscc.decode_base64(feature), feature
        elif isinstance(feature, bytes):
            feature_raw, feature_str = feature, iscc.encode_base64(feature)
        else:
            raise ValueError(f"feature must be str or bytes, not {type(feature)}")

        ignore = ignore or set()

        matches = set()

        if ft == 0:
            # Simple lookup with zero threshold
            lookup = self._get_feature(kind, feature_raw)
            for fkey, match_pos in lookup:
                if fkey in ignore:
                    continue
                fm = FeatureMatch(
                    matched_iscc=self.get_iscc(fkey).code,
                    kind=kind,
                    source_feature=feature_str,
                    matched_feature=feature_str,
                    matched_position=match_pos,
                )
                matches.add(fm)
        else:
            # TODO: pluck ANNS search here if available
            # Fallback full scan with non-zero threshold an no ANNS index
            db = self._db_features(kind)
            with self.env.begin(db) as txn:
                with txn.cursor(db) as c:
                    while c.next_nodup():
                        candidate_feature = c.key()
                        distance = iscc.distance_bytes(feature_raw, candidate_feature)
                        if distance > ft:
                            continue
                        for value in c.iternext_dup(keys=False, values=True):
                            fkey, matched_position = msgpack.loads(value)
                            if fkey in ignore:
                                continue
                            fm = FeatureMatch(
                                matched_iscc=self.get_iscc(fkey).code,
                                kind=kind,
                                source_feature=feature_str,
                                matched_feature=iscc.encode_base64(candidate_feature),
                                matched_position=matched_position,
                            )
                            matches.add(fm)

        return sorted(matches)

    def get_key(self, code) -> Optional[int]:
        """Get first internal key for an ISCC if any."""
        # Find per component matches
        components = iscc.decompose(code)
        db = self._db_components()
        idxs = []
        with self.env.begin(db=db) as txn:
            for code in components:
                idx = txn.get(code.bytes)
                if idx is not None:
                    idxs.append(idx)
        # Check if any of the full code entries is an exact match
        full_code_bytes = iscc.compose(components).bytes
        db = self._db_isccs()
        with self.env.begin(db=db) as txn:
            for idx in idxs:
                if txn.get(idx) == full_code_bytes:
                    return msgpack.loads(idx)

    def get_iscc(self, key):
        # type: (Key) -> iscc.Code
        """Get ISCC by index key"""
        if not isinstance(key, bytes):
            key = msgpack.dumps(key)
        db = self._db_isccs()
        with self.env.begin(db) as txn:
            iscc_bytes = txn.get(key)
            if iscc_bytes:
                return iscc.Code(iscc_bytes)

    def get_metadata(self, key):
        # type: (Key) -> iscc.ISCC
        """Get ISCC metadata by index key"""
        if not isinstance(key, bytes):
            key = msgpack.dumps(key)
        db = self._db_metadata()
        with self.env.begin(db) as txn:
            iscc_bytes = txn.get(key)
            if iscc_bytes:
                return msgpack.loads(iscc_bytes)

    def iter_isccs(self) -> Generator[bytes, None, None]:
        """Iterates over all indexed ISCC codes in insertion order."""
        db = self._db_isccs()
        with self.env.begin(db) as txn:
            with txn.cursor(db) as c:
                while c.next():
                    yield c.value()

    def iter_components(self) -> Generator[bytes, None, None]:
        """Itereates over all indexed components in lexicographic order."""
        db = self._db_components()
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

    @property
    def map_size(self) -> int:
        return self.env.info()["map_size"]

    def _db_isccs(self) -> lmdb._Database:
        return self.env.open_db(b"isccs", integerkey=False, create=True)

    def _db_components(self) -> lmdb._Database:
        """Return componets database."""
        return self.env.open_db(
            b"components",
            dupsort=True,  # Duplicate keys allowed
            create=True,  # Create table if required
            integerkey=False,  # Keys are component raw bytes
            integerdup=False,  # Values are raw byte foreign keys to iscc table
            dupfixed=False,  # Variable length values
        )

    def _db_features(self, kind: str) -> lmdb._Database:
        return self.env.open_db(
            kind.encode("utf-8"),
            dupsort=True,  # Duplicate keys allowed
            create=True,  # Create table if required
            integerkey=False,  # Keys are raw byte feature hashes
            integerdup=False,  # Values are msgpack serialized tuples (fkey, size)
            dupfixed=False,  # Variable length values
        )

    def _db_metadata(self) -> lmdb._Database:
        return self.env.open_db(b"metadata", integerkey=False, create=True)

    def _add_component(self, code: bytes, fkey: bytes) -> bool:
        """
        Add a component to the index with a pointer to its source ISCC.
        A single component can point to multipe ISCC entries in the main table.
        """
        db = self._db_components()
        return self._put(db, code, fkey, dupdata=True, overwrite=True)

    def _add_feature(self, kind, feature, fkey, position):
        # type: (str, bytes, bytes, Union[int, float]) -> bool
        """Add a feature to the index with a pointer to its source ISCC and position.
        A single feature can point to multiple ISCC entries at multiple positions.
        """
        db = self._db_features(kind)
        value = msgpack.packb((fkey, position))
        return self._put(db, feature, value, dupdata=True, overwrite=True)

    def _get_values(self, db, key):
        # type: (lmdb._Database, bytes) -> List[bytes]
        """Collect all values for a given `key` from LMDB dupsort database."""
        values = []
        with self.env.begin(db) as txn:
            with txn.cursor(db) as c:
                value = c.get(key)
                if value is None:
                    return []
                values.append(value)
                while c.next_dup():
                    values.append(c.value())
        return values

    def _get_feature(self, kind, feature):
        # type: (str, bytes) -> List[Tuple[bytes, Union[int, float]]]
        """Get a list of (fkey, position) results for a given feature"""
        db = self._db_features(kind)
        results = []
        with self.env.begin() as txn:
            with txn.cursor(db) as c:
                r = c.get(feature)
                if r is None:
                    return []
                results.append(msgpack.unpackb(r, use_list=False))
                while c.next_dup():
                    results.append(msgpack.unpackb(c.value(), use_list=False))
        return results

    def _next_key(self) -> bytes:
        """Next free autoincrement key"""
        db = self._db_isccs()
        with self.env.begin(db) as txn:
            with txn.cursor(db) as c:
                empty = not c.last()
                key = msgpack.loads(c.key()) + 1 if not empty else 0
        return key

    def _put(self, db, key: bytes, value: bytes, dupdata=True, overwrite=True) -> bool:
        """Wrap LMDB put in a transaction and auto-resize db if required."""
        try:
            with self.env.begin(db, write=True) as txn:
                return txn.put(key, value, dupdata=dupdata, overwrite=overwrite)
        except lmdb.MapFullError:
            new_size = self.map_size * 2
            log.info(f"Resizing {self.dbpath} to {naturalsize(new_size)}")
            self.env.set_mapsize(self.map_size * 2)
            with self.env.begin(db, write=True) as txn:
                return txn.put(key, value, dupdata=dupdata, overwrite=overwrite)

    def _putmulti(self, db, items, dupdata=True, overwrite=True) -> Tuple[int, int]:
        """Wrap LMDB putmulti in a transaction and auto-resize db if required."""
        try:
            with self.env.begin(db, write=True) as txn:
                with txn.cursor(db) as c:
                    return c.putmulti(items, dupdata=dupdata, overwrite=overwrite)
        except lmdb.MapFullError:
            new_size = self.map_size * 2
            log.info(f"Resizing {self.dbpath} to {naturalsize(new_size)}")
            self.env.set_mapsize(self.map_size * 2)
            with self.env.begin(db, write=True) as txn:
                with txn.cursor(db) as c:
                    return c.putmulti(items, dupdata=dupdata, overwrite=overwrite)

    def _build_match(self, source_iscc, matched_key):
        # type: (iscc.Code, bytes) -> IsccMatch
        """Build IsccMatch for source_iscc and iscc of a matched foreign key."""
        matched_iscc: iscc.Code = self.get_iscc(matched_key)
        matchdata = iscc.compare(source_iscc, matched_iscc)
        matchdata["matched_iscc"] = matched_iscc.code
        matchdata["key"] = msgpack.loads(matched_key)
        matchdata["distance"] = iscc.distance_ba(
            source_iscc.hash_ba, matched_iscc.hash_ba
        )
        return IsccMatch(**matchdata)

    @staticmethod
    def _parse_iscc_obj(iscc_obj):
        # type: (IsccObj) -> Tuple[iscc.Code, List[dict], Optional[dict]]
        """Unpack different types of ISCC inputs."""

        metadata = None
        features = []

        if isinstance(iscc_obj, str):
            iscc_code = iscc.Code(iscc_obj)
        elif isinstance(iscc_obj, iscc.Code):
            iscc_code = iscc_obj
        elif isinstance(iscc_obj, ISCC):
            iscc_code = iscc.Code(iscc_obj.iscc)
            metadata = iscc_obj.dict(exclude_unset=True)
            features = metadata.get("features", [])
        elif isinstance(iscc_obj, dict):
            iscc_code = iscc.Code(iscc_obj["iscc"])
            metadata = iscc_obj
            features = metadata.get("features", [])
        else:
            raise ValueError(
                f"'iscc_obj' must be one of {IsccObj} not {type(iscc_obj)}."
            )
        return iscc_code, features, metadata

    def _dump(self):
        """Dump DB to console"""
        for idx, value in enumerate(self.iter_isccs()):
            print("ISCC", idx, iscc.Code(value).code)
        if self.opts.index_components:
            db = self._db_components()
            with self.env.begin(db) as txn:
                with txn.cursor(db) as c:
                    c.first()
                    for k in c.iternext_nodup():
                        print("COMPONENT", iscc.Code(k), end=" ")
                        c2 = txn.cursor(db)
                        c2.set_key(k)
                        for v in c2.iternext_dup(keys=False, values=True):
                            print(msgpack.loads(v), end=" ")
                        print()
        if self.opts.index_features:
            kinds = ["text", "image", "audio", "video", "data"]
            for kind in kinds:
                try:
                    db = self._db_features(kind)
                except lmdb.ReadonlyError:
                    continue
                with self.env.begin(db) as txn:
                    with txn.cursor(db) as c:
                        c.first()
                        for k in c.iternext_nodup():
                            print(kind.upper(), end=" ")
                            print(iscc.encode_base64(k), end=" ")
                            c2 = txn.cursor(db)
                            c2.set_key(k)
                            for v in c2.iternext_dup(keys=False, values=True):
                                fkey, pos = msgpack.loads(v)
                                value = [msgpack.loads(fkey), round(pos, 3)]
                                print(value, end=" ")
                            print()
        if self.opts.index_metadata:
            db = self._db_metadata()
            with self.env.begin(db) as txn:
                for k, v in txn.cursor(db):
                    print("METADATA", msgpack.loads(k), msgpack.loads(v))

    def __len__(self):
        """Number of indexed ISCCs"""
        db = self._db_isccs()
        with self.env.begin(db) as txn:
            stat = txn.stat(db)
            return stat.get("entries")

    def __contains__(self, item):
        """Check if full iscc code is in index."""
        key = self.get_key(item)
        return False if key is None else True
