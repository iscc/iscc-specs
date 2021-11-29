# -*- coding: utf-8 -*-
import operator
from enum import Enum
import mmap
from io import BufferedReader, BytesIO
from pathlib import Path
from typing import BinaryIO, List, Optional, Union
from pydantic import BaseModel, Field, validator, conint, confloat, constr
from iscc.metrics import distance_b64


DEFAULT_WINDOW = 7
DEFAULT_OVERLAP = 3
FEATURE_REGEX = "^[-A-Za-z0-9_]{11}"
IKEY_REGEX = "^[-A-Za-z0-9+/]*={0,2}$"


Data = Union[bytes, bytearray, memoryview]
Uri = Union[str, Path]
File = Union[BinaryIO, mmap.mmap, BytesIO, BufferedReader]
Readable = Union[Uri, Data, File]
PositiveNum = Union[conint(strict=True, ge=0), confloat(strict=True, ge=0.0)]
IndexKey = Union[
    conint(strict=True, ge=0),
    constr(strict=True, min_length=1, max_length=64, regex=IKEY_REGEX),
]


class GMT(str, Enum):
    """Generic Metdia Type"""

    text = "text"
    image = "image"
    audio = "audio"
    video = "video"
    unknown = "unknown"


class FeatureMatch(BaseModel):
    """A single granular feature match result."""

    class Config:
        frozen = True

    key: Optional[IndexKey] = Field(description="Unique key of ISCC entry.")
    matched_iscc: str = Field(description="The matched (candidate) ISCC")
    kind: str = Field(
        description="The kind of feature that has been matched.",
    )
    source_feature: str = Field(description="The original feature that was queried.")
    source_pos: Optional[PositiveNum] = Field(
        description="The position of of the original feature"
    )
    matched_feature: str = Field(description="The feature hash of the matched entry.")
    matched_position: Optional[PositiveNum] = Field(
        description="The position of the feature in the matched content."
    )
    distance: Optional[int] = Field(description="The hamming distance of the match")

    @validator("distance", always=True)
    def calculate_distance(cls, v, values):
        if v is None:
            v = distance_b64(values["source_feature"], values["matched_feature"])
        return v

    def __lt__(self, other):
        """Adds support for deterministic sorting by distance."""
        a = (
            self.distance,
            self.matched_iscc,
            self.matched_position,
            self.matched_feature,
        )
        b = (
            other.distance,
            other.matched_iscc,
            other.matched_position,
            other.matched_feature,
        )
        return operator.lt(a, b)


class IsccMatch(BaseModel):
    """Metrics of a matched ISCC."""

    class Config:
        frozen = True

    key: Optional[IndexKey] = Field(description="Unique key of ISCC entry.")
    matched_iscc: str = Field(description="The ISCC found to match with the query.")
    distance: Optional[int] = Field(description="Hamming distance of the full code")
    mdist: Optional[int] = Field(description="Hamming distance of Meta-Code.")
    cdist: Optional[int] = Field(description="Hamming distance of Content-Code.")
    ddist: Optional[int] = Field(description="Hamming distance of Data-Code.")
    imatch: Optional[bool] = Field(description="Wether Instance-Code is identical.")

    def __lt__(self, other):
        """Adds support for deterministic sorting by distance."""
        a = self.distance, self.matched_iscc
        b = other.distance, other.matched_iscc
        return operator.lt(a, b)


class QueryResult(BaseModel):

    iscc_matches: Optional[List[IsccMatch]] = Field(
        default_factory=list, description="Matched ISCCs with distance metrics"
    )
    feature_matches: Optional[List[FeatureMatch]] = Field(
        default_factory=list, description="ISCCs matched by granular features."
    )


class FeatureType(str, Enum):
    """Type of granular features."""

    text = "text"
    image = "image"
    audio = "audio"
    video = "video"
    data = "data"


class Features(BaseModel):
    """Granular feature codes.

    If only a list of features is provided it is assumed that those have been created
    with the default values for 'window' and 'overlap'.

    If sizes are provided it is assumed that we deal with custom segment sizes
    based on content aware chunking.
    """

    kind: FeatureType = Field(description="Type of granular features")
    version: int = Field(description="Version of feature generation algorithm")
    features: List[str] = Field(
        description="Segmentwise 64-bit features (base64url encoded).",
        regex=FEATURE_REGEX,
        min_items=1,
    )
    sizes: Optional[List[PositiveNum]] = Field(
        description="Sizes of segmets used for feature calculation.",
        min_items=1,
    )
    window: Optional[int] = Field(
        DEFAULT_WINDOW,
        description="Window size of feature segments",
    )
    overlap: Optional[int] = Field(
        DEFAULT_OVERLAP,
        description="Overlap size of feature segments",
    )

    # TODO add positions or locations array

    @property
    def type_id(self) -> str:
        """Composite string of type-version used as table name for feature indexing."""
        return f"{self.kind}-{self.version}"


class ISCC(BaseModel):
    class Config:
        extra = "forbid"
        validate_assignment = True

    version: str = Field(
        "0-0-0",
        title="ISCC Schema Version",
        description="Version of ISCC Metadata Schema (SchemaVer).",
        const=True,
    )
    iscc: str = Field(description="ISCC code of the identified digital asset.")

    # Essential Metadata
    title: Optional[str] = Field(
        description="The title or name of the intangible creation manifested by the"
        " identified digital asset"
    )
    extra: Optional[str] = Field(
        description="Descriptive, industry-sector or use-case specific metadata (used "
        "as immutable input for Meta-Code generation). Any text string "
        "(including json or json-ld) indicative of the identity of the "
        "referent may be used."
    )

    # binary: bool = Field(description="Extra metadata was supplied in binary format.")

    # File Properties
    filename: Optional[str] = Field(
        description="Filename of the referenced digital asset (automatically used as "
        "fallback if no seed_title element is specified)"
    )
    filesize: Optional[int] = Field(description="File size of media asset in bytes.")
    mediatype: Optional[str] = Field(description="IANA Media Type (MIME type)")

    # Cryptographic hashes
    tophash: Optional[str] = Field(
        title="tophash",
        description="Blake3 hash over concatenation of metahash and datahash",
    )
    metahash: Optional[str] = Field(
        title="metahash", description="Blake3 hash of metadata."
    )
    datahash: Optional[str] = Field(
        title="datahash", description="Blake3 hash of media file."
    )

    gmt: GMT = Field(GMT.unknown, description="Generic Media Type")

    # Audio Visual Media
    duration: Optional[float] = Field(
        description="Duration of audio-visual media in secondes."
    )
    fps: Optional[float] = Field(description="Frames per second of video assets.")
    width: Optional[int] = Field(description="Width of visual media in pixels.")
    height: Optional[int] = Field(description="Height of visual media in pixels.")

    # Textual Media
    characters: Optional[int] = Field(
        description="Number of text characters (code points after Unicode "
        "normalization) (GMT Text only)."
    )

    language: Optional[Union[str, List[str]]] = Field(
        description="Language(s) of content (BCP-47) in weighted order."
    )

    # Granular Features
    features: Optional[List[Features]] = Field(
        description="Standardized fingerprints for granular content "
        "recognition and matching purposes."
    )

    # Presentational Metadata
    preview: Optional[str] = Field(description="Uri of media asset preview.")

    # Todo: fingerprint should be a repeatable complex object (maybe part of features)
    fingerprint: Optional[str] = Field(
        description="Base64 encoded original raw fingerprint (MPEG-7, Chromaprint) "
        "from which features and/or codes have been derived."
    )


if __name__ == "__main__":
    """Save ISCC JSON schema"""
    from os.path import abspath, dirname, join

    HERE = dirname(abspath(__file__))
    SCHEMA_PATH = join(HERE, "iscc.json")
    schema = ISCC.schema_json()
    with open(SCHEMA_PATH, "wt", encoding="UTF-8") as outf:
        outf.write(ISCC.schema_json(indent=2))
