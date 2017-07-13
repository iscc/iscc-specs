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

| Component     | Nibble-1 | Nibble-2     |
| ------------- | -------- | ------------ |
| *Meta-ID*     | 0000     | ISCC version |
| *Content-ID*  | 0001     | Content type |
| *Data-ID*     | 0010     | Reserved     |
| *Instance-ID* | 0011     | Reserved     |

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
12. Encode the resulting 8 byte sequence with base32hex and return the result.

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

*[character]: A character is defined as one Unicode code point


