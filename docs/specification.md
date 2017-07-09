# ISCC - Specification (Draft)

**International Standard Content Code**

!!! attention

    This document is work in progress!
The latest version of this document can be found at [iscc.codes](http://iscc.codes)

## Abstract
ISCC is an identifier for digital content, that can be created by anybody from minimal metadata and the content itself. The ISCC specification defines and describes the technical procedures needed to create ISCC identifiers.

## Status of this Document

This document is the **first draft** of the open and vendor neutral ISCC 1.0 specification. The content of this document is determined by its authors in an open consensus process. All participants of the wider content ecosystem are invited to contribute.

## Identifier Format
The ISCC identifier is build from multiple 64-bit components:

| Components:     | Meta-ID             | Content-ID         | Data-ID         | Instance-ID    |
| --------------- | ------------------- | ------------------ | --------------- | -------------- |
| **Identifies:** | Intangible creation | Content similarity | Data similarity | Data integirty |
| **Required:**   | Yes                 | No                 | Yes             | Yes            |
| **Input:**      | Metadata            | Extracted  content | Raw data        | Raw data       |
| **Size:**       | 64 Bits             | 64 Bits            | 64 Bits         | 64 Bits        |


*[ISCC]: International Standard Content Code

