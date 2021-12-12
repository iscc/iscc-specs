# -*- coding: utf-8 -*-
from os.path import join
from pathlib import Path
from typing import Optional
from iscc_core.options import CoreOptions
from pydantic import Field
from iscc import APP_DIR


class SdkOptions(CoreOptions):
    """Options for ISCC generation"""

    class Config:
        env_file = "iscc-sdk.env"
        env_file_encoding = "utf-8"

    all_granular: Optional[bool] = Field(
        None,
        description="Generate granular fingerprints for all code types "
        "(overides individual options).",
    )

    all_preview: Optional[bool] = Field(
        None,
        description="Generate previews for all code types "
        "(overrides individual options).",
    )

    meta_title_from_uri: bool = Field(
        True,
        description="Use normalized filename as title if we have nor explicit title "
        "and also no title from metadata extraction.",
    )

    text_granular: bool = Field(
        True, description="Calculate and return granular text features"
    )

    text_avg_chunk_size: int = Field(
        1024,
        description="Avg number of characters per text chunk for granular fingerprints",
    )

    text_guess_title: bool = Field(
        True,
        description="Use first line from text as title if we don´t have an explicit title",
    )

    text_store: bool = Field(
        False,
        description="Store extracted paintext (with filename: <datahash>.txt.gz).",
    )

    image_transpose: bool = Field(
        True,
        description="Transpose image according to EXIF Orientation tag",
    )

    image_fill: bool = Field(
        True, description="Add gray background to image if it has alpha transparency"
    )

    image_trim: bool = Field(True, description="Crop empty borders of images")

    image_granular: bool = Field(
        True, description="Calculate and return granular image features"
    )

    image_granular_n: int = Field(32, description="Top-N granular features to retain")

    image_preview: bool = Field(True, description="Generate image preview thumbnail")

    image_preview_size: int = Field(
        96, description="Size of larger side of thumbnail in pixels"
    )

    image_preview_quality: int = Field(
        30, description="Image compression setting (0-100)"
    )

    audio_granular: bool = Field(
        True, description="Calculate and return granular audio features"
    )

    audio_max_duration: int = Field(
        0,
        description="Maximum seconds of audio to process (0 for full fingerprint)",
    )

    video_fps: int = Field(
        5,
        description="Frames per second to process for video hash (ignored when 0).",
    )

    video_crop: bool = Field(
        True, description="Detect and remove black borders before processing"
    )

    video_granular: bool = Field(True, description="Generate granular features")

    video_scenes: bool = Field(
        True, description="Use scene detection for granular features"
    )

    video_scenes_ffmpeg: bool = Field(
        True,
        description="Use ffmpeg built-in scene detection. (Less accurate than "
        "pyscenedetect but at least 2x faster).",
    )

    video_scenes_ffmpeg_th: float = Field(0.4, description="FFMPEG scene cut threshold")

    video_scenes_fs: int = Field(
        2,
        description="Number of frames to skip per processing step "
        "for scene detection with pyscenedetect. Higher values will increase detection "
        "speed and decrease detection quality (PySceneDetect only).",
    )

    video_scenes_th: int = Field(
        40,
        description="Threshold for scene detection. Higher values detect less scenes "
        "(PySceneDetect only).",
    )

    video_scenes_min: int = Field(
        15,
        description="Minimum number of frames per scene. (PySceneDetect only)",
    )

    video_window: int = Field(
        7,
        description="Seconds of video per granular feature if using rolling window mode",
    )

    video_overlap: int = Field(
        3, description="Seconds of video that overlap if using rolling window mode"
    )

    video_include_fingerprint: bool = Field(
        False, description="Include raw MPEG-7 Video Signature in output"
    )

    video_preview: bool = Field(True, description="Generate video preview thumbnail(s)")

    video_hwaccel: Optional[str] = Field(
        None,
        description="Use ffmpeg hardware acceleration for video processing "
        "(use the string `auto` as value to activate).",
    )

    data_granular: bool = Field(False, description="Return granular data features.")

    data_granular_factor: int = Field(
        64, description="Size of granular data chunks time average chunk size"
    )

    index_root: Path = Field(join(APP_DIR, "db"), description="Storage root path")

    index_components: bool = Field(
        True, description="Create inverted index of component to ISCCs"
    )

    index_features: bool = Field(
        False, description="Create inverted index of features to ISCCs"
    )

    index_metadata: bool = Field(False, description="Store metadata in index")


sdk_opts = SdkOptions()
