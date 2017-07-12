# ISCC - Specification (Draft)

**International Standard Content Code**

!!! attention

    This document is work in progress!
The latest version of this document can be found at [iscc.codes](http://iscc.codes)

## About this Document

This document is the **first draft** of the open and vendor neutral ISCC 1.0 specification and describes the technical procedures to create and manage ISCC identifiers. It is produced by the [Content Blockchain Project](https://content-blockchain.org) and it should be regarded as the definitive guide to the ISCC standard. The content is determined by its authors in an open consensus process. All participants of the wider content ecosystem are invited to contribute.

## Basic structure of an ISCC

### Components overview

The ISCC identifier is a fixed size sequence of 32 bytes (256 bits) build from multiple self describing 64 bit components: 


| Components:     | Meta-ID             | Content-ID         | Data-ID         | Instance-ID      |
| --------------- | ------------------- | ------------------ | --------------- | ---------------- |
| **Identifies:** | Intangible creation | Content similarity | Data similarity | Data checksum    |
| **Input:**      | Metadata            | Extracted  content | Raw data        | Raw data         |
| **Algorithms:** | Simhash             | Type specific      | CDC, Minhash    | CDC, Merkle tree |
| **Size:**       | 64 bits             | 64 bits            | 64 bits         | 64 bits          |

Each component is guaranteed to fit into a 64-bit unsigned integer value. The printable and human readable representation of each component is is a 13 character [RFC 4648](https://tools.ietf.org/html/rfc4648#section-7) base32hex coded string without padding. The components may be used independently by applications for various purposes but must be combined to a 52 character string for a fully qualified ISCC code. The components must be combined in the fixed order of Meta-ID, Content-ID, Data-ID, Instance-ID and may be seperated by hyphens. 

### Component types

Each component has the same basic structure of a 1 byte header and a 7 byte main section. Each component can thus be fit into a 64-bit integer value. The header-byte of each component is subdivided into 2 nibbles (4 Bits). The first nibble specifies the component type while the second nibble is component specific.

| Component     | Nibble-1 | Nibble-2     |
| ------------- | -------- | ------------ |
| *Meta-ID*     | 0000     | ISCC version |
| *Content-ID*  | 0001     | Content type |
| *Data-ID*     | 0010     | Reserved     |
| *Instance-ID* | 0011     | Reserved     |

## Meta-ID component

The Meta-ID is built from minimal and generic metadata of the content to be identified. An ISCC generating application must accept the following 3 input fields as UTF-8 encoded bytestring:

| Inputfield | Required | Max chars | Description                              |
| ---------- | -------- | --------- | ---------------------------------------- |
| *title*    | Yes      | 70        | The title of an intangible creation.     |
| *creators* | No       | 70        | One or more semicolon separated names of the original creators of the content. |
| *extra*    | No       | 70        | A short statement that distinguishes this intangible creation from another one. |



*[ISCC]: International Standard Content Code

