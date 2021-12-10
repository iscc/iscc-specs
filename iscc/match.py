# -*- coding: utf-8 -*-
"""Basic example for ISCC code matching"""
from operator import itemgetter
from typing import Optional
from typing import Hashable
from bitarray.util import count_xor
from iscc.schema import IsccMatch
import iscc
import iscc_core
from bidict import bidict
from collections import defaultdict
from iscc.wrappers import decompose
import iscc.metrics


__all__ = ["SimpleIndex", "SimpleSplitIndex"]


class SimpleIndex:
    """Brute force nearest neighbour search for full iscc codes."""

    def __init__(self, name: str = "default"):
        self.name = name
        # Maps keys (internal or external) to ISCC codes
        self.isccs = bidict()
        # Mapps similarity components of ISCCs as bitarrays to main index entries.
        self.sim_hashes = defaultdict(set)

    def add(self, code: str, key: Optional[Hashable] = None):
        """Add an ISCC to the index. Returns the key of the new ISCC entry.

        :param code: ISCC code to be added to the index.
        :param key: An optional external key (auto-incremented int if not set).
        """
        norm_code_obj = self.normalize(code)

        # We only support adding new codes with unique keys
        if norm_code_obj.code in self.isccs.inverse:
            raise ValueError(f"{norm_code_obj.code} already in index.")
        if key in self.isccs:
            raise ValueError(f"Entry with key {key} already in index.")

        # Create auto-incremented key if necessary
        if key is None:
            key = len(self.isccs)

        self.isccs[key] = norm_code_obj.code

        # Bitarray of first 3 components
        prefix = norm_code_obj.hash_ba[:192]
        self.sim_hashes[prefix].add(key)

        return key

    def query(self, code: str, k=10, t=128):
        """Return k nearest neighbors below bit-distance threshold t."""
        norm_code_obj = self.normalize(code)
        query_prefix = norm_code_obj.hash_ba[:192]

        distances = {}
        for candidate_prefix in self.sim_hashes.keys():
            distance = count_xor(query_prefix, candidate_prefix)
            if distance <= t:
                distances[candidate_prefix] = distance
        top_k = sorted(distances.items(), key=itemgetter(1))[:k]
        result = []
        for hash_ba, total_dist in top_k:
            for key in self.sim_hashes[hash_ba]:
                candidate = self.isccs[key]
                matchdata = iscc.metrics.compare(norm_code_obj.code, candidate)
                matchdata["key"] = key
                matchdata["matched_iscc"] = candidate
                result.append(IsccMatch(**matchdata))

        return result

    @staticmethod
    def normalize(code):
        return iscc_core.gen_iscc_code_v0([c.code for c in decompose(code)]).code_obj

    def __contains__(self, item):
        return self.normalize(item).code in self.isccs.inverse


class SimpleSplitIndex:
    def __init__(self, name: str = "default"):
        self.name = name
        # Full ISCCs
        self.isccs = bidict()
        # Singular Component Codes
        self.codes = {}

    def add(self, code: str):
        """Add a Full ISCC to the search index and return its ID."""

        # Return index if we already have the ISCC
        norm_code_obj = self.normalize(code)
        if norm_code_obj.code in self:
            return self.isccs.inverse[norm_code_obj.code]

        # Add new ISCC entry
        new_id = len(self.isccs)
        self.isccs[new_id] = norm_code_obj.code

        # Index components
        for component in decompose(norm_code_obj):
            # Create index for component type if we don't have one yet
            if component.type_id not in self.codes:
                self.codes[component.type_id] = defaultdict(list)
            self.codes[component.type_id][component.hash_ba].append(new_id)

        return new_id

    def query(self, code: str, threshold=10):
        query_code = self.normalize(code)
        result = []
        seen = set()
        for comp_code in decompose(query_code):
            index = self.codes.get(comp_code.type_id, {})
            for index_ba in index.keys():
                distance = count_xor(comp_code.hash_ba, index_ba)
                if distance <= threshold:
                    for key in index[index_ba]:
                        candidate = self.isccs[key]
                        if candidate in seen:
                            continue
                        matchdata = iscc.metrics.compare(query_code.code, candidate)
                        matchdata["key"] = key
                        matchdata["matched_iscc"] = candidate
                        result.append(IsccMatch(**matchdata))
                        seen.add(candidate)
        return result

    @staticmethod
    def normalize(code):
        return iscc_core.gen_iscc_code_v0([c.code for c in decompose(code)]).code_obj

    def __contains__(self, item):
        return self.normalize(item).code in self.isccs.inverse
