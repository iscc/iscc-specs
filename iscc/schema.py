# -*- coding: utf-8 -*-
from enum import Enum
import mmap
from io import BufferedReader, BytesIO
from pathlib import Path
from typing import BinaryIO, List, Optional, Union
from pydantic import BaseSettings, BaseModel, Field


Data = Union[bytes, bytearray, memoryview]
Uri = Union[str, Path]
File = Union[BinaryIO, mmap.mmap, BytesIO, BufferedReader]
Readable = Union[Uri, Data, File]


DEFAULT_WINDOW = 7
DEFAULT_OVERLAP = 3
FEATURE_REGEX = "^[-A-Za-z0-9_]{11}"


class Options(BaseSettings):
    """Options for ISCC generation"""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    all_granular: bool = Field(
        False,
        description="Generate granular fingerprints for all code types "
        "(overides individual options).",
    )
    all_preview: bool = Field(
        False,
        description="Generate previews for all code types"
        "(overrides individual options).",
    )

    meta_bits: int = Field(64, description="Length of generated Meta-Code in bits")

    meta_title_from_uri: bool = Field(
        True,
        description="Use normalized filename as title if we have nor explicit title "
        "and also no title from metadata extraction.",
    )

    meta_trim_title: int = Field(
        128, description="Trim title length to this mumber of bytes"
    )
    meta_trim_extra: int = Field(4096, description="Trim extra to this number of bytes")

    meta_ngram_size: int = Field(
        3, description="Number of characters for sliding window over metadata text."
    )

    text_bits: int = Field(
        64, description="Length of generated Content-ID-Text in bits"
    )

    text_ngram_size: int = Field(
        13, description="Number of characters per feature hash (size of sliding window)"
    )

    text_granular: bool = Field(
        False, description="Calculate and return granular text features"
    )

    text_avg_chunk_size: int = Field(
        1024,
        description="Avg number of characters per text chunk for granular fingerprints",
    )

    text_guess_title: bool = Field(
        True,
        description="Use first line from text as title if we don´t have an explicit title",
    )

    image_bits: int = Field(
        64, description="Length of generated Content-ID-Image in bits"
    )

    image_trim: bool = Field(
        False,
        description="Autocrop empty borders of images before Image-Code generation",
    )

    image_preview: bool = Field(False, description="Generate image preview thumbnail")

    image_preview_size: int = Field(
        96, description="Size of larger side of thumbnail in pixels"
    )

    image_preview_quality: int = Field(
        30, description="Image compression setting (0-100)"
    )

    image_exif_transpose: bool = Field(
        True,
        description="Transpose according to EXIF Orientation tag before hashing",
    )

    audio_bits: int = Field(
        64, description="Length of generated Content-ID-Audio in bits"
    )

    audio_granular: bool = Field(
        False, description="Calculate and return granular audio features"
    )

    audio_max_duration: int = Field(
        120,
        description="Maximum seconds of audio to process",
    )

    video_bits: int = Field(
        64, description="Length of generated Content-ID-Video in bits"
    )

    video_fps: int = Field(
        5,
        description="Frames per second to process for video hash (ignored when 0).",
    )

    video_crop: bool = Field(
        True, description="Detect and remove black borders before processing"
    )

    video_granular: bool = Field(False, description="Generate granular features")

    video_scenes: bool = Field(
        True, description="Use scene detection for granular features"
    )

    video_scenes_fs: int = Field(
        2,
        description="Number of frames to skip per processing step for scene detection. "
        "Higher values will increase detection speed and decrease detection"
        " quality.",
    )

    video_scenes_th: int = Field(
        40,
        description="Threshold for scene detection. Higher values detect less scenes.",
    )

    video_scenes_min: int = Field(
        15,
        description="Minimum number of frames per scene.",
    )

    video_scenes_previews: bool = Field(
        False,
        description="Generate and return per scene preview thumbnails when scene "
        "detection is used.",
    )

    video_window: int = Field(
        7, description="Seconds of video per granular feature in rolling window mode"
    )

    video_overlap: int = Field(
        3, description="Seconds of video that overlap in roling window mode"
    )

    video_include_fingerprint: bool = Field(
        False, description="Include raw MPEG-7 Video Signature in output"
    )

    video_preview: bool = Field(
        False, description="Generate 128px video preview thumbnail(s)"
    )

    video_hwaccel: Optional[str] = Field(
        None, description="Use hardware acceleration for video processing"
    )

    data_bits: int = Field(64, description="Length of generated Data-Code in bits")

    data_avg_chunk_size: int = Field(
        1024, description="Average chunk size for data chunking."
    )

    data_granular: bool = Field(False, description="Return granular data features.")

    data_granular_factor: int = Field(
        64, description="Size of granular data chunks time average chunk size"
    )

    instance_bits: int = Field(
        64, description="Length of generated Instance-Code in bits"
    )

    io_chunk_size: int = Field(
        262144, description="Number of bytes per io read operation"
    )


class GMT(str, Enum):
    """Generic Metdia Type"""

    text = "text"
    image = "image"
    audio = "audio"
    video = "video"
    unknown = "unknown"


class IsccMatch(BaseModel):
    """Metics of comparing two ISCCs"""

    iscc: str = Field(description="The ISCC found to match with a query.")
    key: Optional[Union[str, int]] = Field(description="An optional external key.")
    mdist: Optional[int] = Field(description="Hamming distance of Meta-Code.")
    cdist: Optional[int] = Field(description="Hamming distance of Content-Code.")
    ddist: Optional[int] = Field(description="Hamming distance of Data-Code.")
    imatch: Optional[bool] = Field(description="Wether Instance-Code is identical.")


class FeatureType(str, Enum):
    """Type of granular features."""

    text = "text"
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

    kind: Optional[FeatureType] = Field(description="Type of granular features")
    features: List[str] = Field(
        description="Segmentwise 64-bit features (base64url encoded).",
        regex=FEATURE_REGEX,
        min_items=1,
    )
    sizes: Optional[List[float]] = Field(
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


class TextCode(BaseModel):
    code: str = Field(
        ...,
        title="Text-Code",
        description="Content-Code Text in standard representation.",
    )

    title: Optional[str] = Field(description="The title of the text.")

    characters: Optional[int] = Field(
        description="Number of text characters (code points after Unicode "
        "normalization) (GMT Text only)."
    )

    language: Optional[str] = Field(description="Main language of content (BCP-47)")

    features: Optional[List[str]] = Field(description="List of hashes per text chunk")

    sizes: Optional[List[int]] = Field(description="Sizes of text chunks in characters")


class ImageCode(BaseModel):

    code: str = Field(
        ...,
        title="Image-Code",
        description="Content-Code Image in standard representation.",
    )

    title: Optional[str] = Field(description="The title of the image.")

    width: Optional[int] = Field(description="Width of original image in pixels.")
    height: Optional[int] = Field(description="Height of original image in pixels.")
    preview: Optional[str] = Field(description="Data-Uri of image preview thumbnail.")


class DataCode(BaseModel):
    code: str = Field(
        ..., title="Instance-Code", description="Data-Code in standard representation."
    )
    features: Optional[List[str]] = Field(description="List of hashes per datachunk")
    sizes: Optional[List[int]] = Field(description="Sizes of datachunks")


class InstanceCode(BaseModel):
    code: str = Field(..., description="Instance-Code in standard representation.")
    datahash: str = Field(description="Blake3 hash of resource (as hex-string).")
    filesize: int = Field(description="File size in bytes.")


if __name__ == "__main__":
    """Save ISCC JSON schema"""
    from os.path import abspath, dirname, join

    HERE = dirname(abspath(__file__))
    SCHEMA_PATH = join(HERE, "iscc.json")
    schema = ISCC.schema_json()
    with open(SCHEMA_PATH, "wt", encoding="UTF-8") as outf:
        outf.write(ISCC.schema_json(indent=2))
