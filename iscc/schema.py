# -*- coding: utf-8 -*-
from typing import List, Optional
from pydantic import BaseModel, Field

DEFAULT_WINDOW = 7
DEFAULT_OVERLAP = 3
FEATURE_REGEX = "^[-A-Za-z0-9_]{11}"


class Features(BaseModel):
    """Granular feature codes.

    If only a list of features is provided it is assumed that those have been created
    with the default values for 'window' and 'overlap'.

    If sizes are provided it is assumed that we deal with custom segment sizes
    based on content aware chunking.
    """

    features: List[str] = Field(
        description="Segmentwise 64-bit features (base64url encoded).",
        regex=FEATURE_REGEX,
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
    sizes: Optional[List[int]] = Field(
        description="Sizes of segmets used for feature calculation",
        min_items=1,
    )


class ISCC(BaseModel):
    version: int = Field(0, description="ISCC Schema Version")
    iscc: str = Field(description="ISCC code of the identified digital asset.")
    title: Optional[str] = Field(
        description="The title or name of the intangible creation manifested by the"
        " identified digital asset"
    )
    extra: Optional[str] = Field(
        description="Descriptive, industry-sector or use-case specific metadata (used "
        "as immutable input for Meta-Code generation). Any text string "
        "(structured or unstructured) indicative of the identity of the "
        "referent may be used."
    )
    filename: Optional[str] = Field(
        description="Filename of the referenced digital asset (automatically used as "
        "fallback if no seed_title element is specified)"
    )

    identifier: Optional[str] = Field(
        description="Other identifier(s) such as those defined by ISO/TC 46/SC 9 "
        "referencing the work, product or other abstraction of which the "
        "referenced digital asset is a full or partial manifestation "
        "(automatically used as fallback if no extra element is specified)."
    )
    language: Optional[List[str]] = Field(
        description="Language(s) of textual content (BCP-47) in weighted order "
        "(GMT Text only)."
    )
    characters: Optional[int] = Field(
        description="Number of text characters (code points after Unicode "
        "normalization) (GMT Text only)."
    )
    features: Optional[Features] = Field(
        description="GMT-specific standardized fingerprint for granular content "
        "recognition and matching purposes."
    )


if __name__ == "__main__":
    """Save ISCC JSON schema"""
    from os.path import abspath, dirname, join

    HERE = dirname(abspath(__file__))
    SCHEMA_PATH = join(HERE, "iscc.json")
    schema = ISCC.schema_json()
    with open(SCHEMA_PATH, "wt", encoding="UTF-8") as outf:
        outf.write(ISCC.schema_json(indent=2))