# ISCC - Specification (Draft)

**International Standard Content Code**

!!! attention

    This document is work in progress!
The latest version of this document can be found at [iscc.codes](http://iscc.codes)

## About this Document

This document is the **first draft** of the open and vendor neutral ISCC 1.0 specification and describes the technical procedures to create and manage ISCC identifiers. It is produced by the [Content Blockchain Project](https://content-blockchain.org) and it should be regarded as the definitive guide to the ISCC standard for technical implementors. The content is determined by its authors in an open consensus process. All participants of the wider media ecosystem are invited to contribute.

## Basic structure of an ISCC

### Components overview

The ISCC identifier is a fixed size sequence of 32 bytes (256 bits) build from multiple self describing 64 bit components: 


| Components:     | Meta-ID             | Content-ID         | Data-ID         | Instance-ID      |
| --------------- | ------------------- | ------------------ | --------------- | ---------------- |
| **Identifies:** | Intangible creation | Content similarity | Data similarity | Data checksum    |
| **Input:**      | Metadata            | Extracted  content | Raw data        | Raw data         |
| **Algorithms:** | Simhash             | Type specific      | CDC, Minhash    | CDC, Merkle tree |
| **Size:**       | 64 bits             | 64 bits            | 64 bits         | 64 bits          |

Each component is guaranteed to fit into a 64 bit unsigned integer value. The printable and human readable representation of each component is is a 13 character [RFC 4648](https://tools.ietf.org/html/rfc4648#section-7) base32hex coded string without padding. The components may be used independently by applications for various purposes but must be combined to a 52 character string (55 with hyphens) for a fully qualified ISCC code. The components must be combined in the fixed order of Meta-ID, Content-ID, Data-ID, Instance-ID and may be seperated by hyphens.

!!! todo

    Describe coded format with prefix, colon, components +- hyphens 

### Component types

Each component has the same basic structure of a 1 byte header and a 7 byte main section. Each component can thus be fit into a 64-bit integer value. The header-byte of each component is subdivided into 2 nibbles (4 bits). The first nibble specifies the component type while the second nibble is component specific.

| Component     | Nibble-1 | Nibble-2                    | Byte |
| ------------- | -------- | --------------------------- | ---- |
| *Meta-ID*     | 0000     | 0000 - ISCC version (0)     | 0x00 |
| *Content-ID*  | 0001     | 0000 - ContentType Text (0) | 0x10 |
| *Data-ID*     | 0010     | 0000 - Reserved             | 0x20 |
| *Instance-ID* | 0011     | 0000 - Reserved             | 0x30 |

Content types



## Meta-ID component

The Meta-ID is built from minimal and generic metadata of the content to be identified. An ISCC generating application must provide a `generate_meta_id` function thats accepts the following input fields:

| Name       | Type    | Required | Description                              |
| ---------- | ------- | -------- | ---------------------------------------- |
| *title*    | unicode | Yes      | The title of an intangible creation.     |
| *creators* | unicode | No       | One or more semicolon separated names of the original creators of the content. |
| *extra*    | unicode | No       | A short statement that distinguishes this intangible creation from another one. |
| version    | integer | No       | ISCC version number. Currently defaults to the only valid value of `1`. May change in the future. |

The `generate_meta_id` function must return a valid base32hex encoded Meta-ID code.

### Generate Meta-ID

An ISCC generating application must follow these steps in given order to produce a stable Meta-ID:

1. Apply Unicode standard [Normalization Form KC (NFKC)](http://www.unicode.org/reports/tr15/#Norm_Forms) separatly to all text input values.
2. Trim each normalized input value to its first 128 characters.
3. Apply [`normalize_text`](#normalize-text) to the trimmed `title` input value.
4. Apply [`normalize_creators`](#normalize-creators) to the trimmed `creators` input value.
5. Apply [`normalize_text`](#normalize-text) to the trimmed `extra` input value.
6. Concatenate the results of step 3, 4 and 5 in ascending order.
7. Create a list of 4 character [n-grams](https://en.wikipedia.org/wiki/N-gram) by sliding character-wise through the result of step 6.
8. Encode each n-gram from step 7 to an utf-8 bytestring and calculate its sha256 digest.
9. Apply `simhash` to the list sha256 digests from step 8.
10. Trim the resulting byte sequence to the first 7 bytes.
11. Prepend the 1 byte component header according to component type and ISCC version (e.g. `0x00`).
12. Encode the resulting 8 byte sequence with base32 (no-padding) and return the result.


## Content-ID component

The Content-ID has multiple subtypes, one for each GMT. The subtype is specified by the first 3 bits of the second nibble of the first byte. The last bit of the first byte is a flag that signifies if the C-ID applies to all GM-Type specific content or just to some part of it.

| Generic Media Type | Nibble-2 Bits 0-3 |
| ------------------ | ----------------- |
| Text               | 000               |
| Image              | 001               |
| Audio              | 010               |

### Content-ID-Text

The Content-ID-Text is build from the extracted plaintext content of an encoded media object. To build a stable C-ID-Text the plain text content must be extracted in a reproducable manner. To make this possible the plaintext content must be extracted with [Apache Tika v1.16](https://tika.apache.org/).

## Data-ID component

The Data-ID is build from the raw encoded data of the content to be identified. An ISCC generating application must provide a `generate_data_id` function that accepts the raw encoded data as input. Generate a Data-ID by this procedure:

1. Apply `chunk_data` to the raw encoded content data
2. For each chunk calculate the sha256 digest
3. Apply `minhash` with 256 permutations to the resulting list of digests
4. Take the lowest bit from each minhash value and concatenate them to a 256 string
5. Trim the resulting byte sequence to the first 7 bytes.
6. Prepend the 1 byte component header (e.g. 0x20). 
7. Encode the resulting 8 byte sequence with base32 (no-padding and return the result

## Instance-ID component

The Instance-ID is built from the raw data file of the content to be identified. An ISCC generating application must provide a `generate_instance_id` function thats accepts the raw data file as input. Generate an Instance-ID by this procedure:

1. Apply `chunk_data` to the raw encoded content data
2. For each chunk calculate its sha256 digest
3. Calculate the merkle root from the list sha256 digests (in order of chunks)
4. Trim the resulting byte sequence to the first 7 bytes.
5. Prepend the 1 byte component header (e.g. 0x30).
6. Encode the resulting 8 byte sequence with base32 (no-padding) and return the result.


## Procedures & Algorithms

### Normalize Text

We define a text normalization function that is specific to our application. It takes unicode text as an input and returns *normalized* unicode text for futher algorithmic processing.  We reference this function by the name `normalize_text` . The  `normalize_text` function performs the following operations in the given order while each step works with the results of the previous operation:

1. Decompose the input text by applying [Unicode Normalization Form D (NFD)](http://www.unicode.org/reports/tr15/#Norm_Forms).
2. Replace each group of one or more consecutive `Separator` characters ([Unicode categories](https://en.wikipedia.org/wiki/Unicode_character_property) Zs, Zl and Zp) with exactly one Unicode `SPACE` character (`U+0020`) .
3. Remove any leading or trailing `Seperator` characters.
4. Remove each character that is not in one of the Unicode categories `Seperator` , `Letter`, `Number` or `Symbol`.
5. Convert all characters to their lower case
6. Re-Compose the text by applying `Unicode Normalization Form C (NFC)`.
7. Return the resulting text

### Normalize Creators

!!! todo

    Specify `normalize_creator` function

### Tokenize Text

!!! todo

    Specify `tokenize_text` function


*[ISCC]: International Standard Content Code

*[M-ID]: Meta-ID Component

*[C-ID]: Content-ID Component

*[D-ID]: Data-ID Component

*[I-ID]: Instance-ID Component

*[GMT]: Generic Media Type

*[character]: A character is defined as one Unicode code point


