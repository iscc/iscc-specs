# -*- coding: utf-8 -*-
"""Basic example for ISCC code matching"""
from enum import Enum
from bitarray.util import count_xor
from dataclasses import dataclass
import iscc
from bidict import bidict
from collections import defaultdict


__all__ = ["SimpleIndex"]


@dataclass
class Match:
    ident: int
    iscc: str
    type: str
    distance: int


class SimpleIndex:
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
        for component in iscc.decompose(norm_code_obj):
            # Create index for component type if we don't have one yet
            if component.type_id not in self.codes:
                self.codes[component.type_id] = defaultdict(list)
            self.codes[component.type_id][component.hash_ba].append(new_id)

        return new_id

    def query(self, code: str, threshold=10):
        query_code = self.normalize(code)
        result = []
        seen = set()
        for comp_code in iscc.decompose(query_code):
            index = self.codes.get(comp_code.type_id, {})
            for index_ba in index.keys():
                distance = count_xor(comp_code.hash_ba, index_ba)
                if distance <= threshold:
                    if comp_code.maintype != iscc.MT.INSTANCE or distance == 0:
                        for ident in index[index_ba]:
                            full_code = self.isccs[ident]
                            if full_code not in seen:
                                result.append(
                                    Match(
                                        ident=ident,
                                        iscc=self.isccs[ident],
                                        type=comp_code.type_id,
                                        distance=distance,
                                    )
                                )
                                seen.add(full_code)
        return result

    @staticmethod
    def normalize(code):
        return iscc.compose(iscc.decompose(code))

    def __contains__(self, item):
        return self.normalize(item).code in self.isccs.inverse
