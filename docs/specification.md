title: ISCC - Specification
description: Draft Specification of International Standard Content Codes
authors: Titusz Pan

# ISCC - Specification v0.9.4

!!! attention

    This document is a work in progress draft! It may be updated, replaced, or obsoleted by other documents at any time. This document MUST not be used as reference material or cited other than as "work in progress".

## Abstract

The **International Standard Content Code (ISCC)**, is an open and decentralized digital media identifier. An ISCC can be created from digital content and its basic metadata by anybody who follows the procedures of the ISCC specification or by using open source software that supports ISCC creation [conforming to the ISCC specification](#conformance-testing).

## Note to Readers

For public discussion of issues for this draft please use the Github issue tracker: <https://github.com/coblo/iscc-specs/issues>.

The latest published version of this draft can be found at <http://iscc.codes/specification/>. 

Public review, discussion and contributions are welcome.

## About this Document

This document proposes an open and vendor neutral ISCC standard and describes the technical procedures to create and manage ISCC identifiers. The first version of this document is produced by the [Content Blockchain Project](https://content-blockchain.org) as a prototype and received funding from the [Google Digital News Initiative (DNI)](https://digitalnewsinitiative.com/dni-projects/content-blockchain-project/). The content of this document is determined by its authors in an open and public consensus process.

## Conventions and Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://tools.ietf.org/html/rfc2119) [RFC2119].

## Definitions

Basic Metadata:
: 	Minimal set of required metadata about the digital media object that is identified by an ISCC.

Character:
:	Throughout this specification a **character** is meant to be interpreted as one Unicode code point. This also means that due to the structure of Unicode a character is not necessarily a full glyph but might be a combining accent or similar.

Digital Media Object:
:	A blob of raw bytes with some media type specific encoding.

Extended Metadata:
:	Metadata that is not encoded within the ISCC but may be supplied together with the ISCC.


Generic Media Type:
:	A basic content type such as plain text in a normalized and *generic* ([UTF-8](https://en.wikipedia.org/wiki/UTF-8)) encoding format.

ISCC:
:	International Standard Content Code

ISCC Code:
:	The printable text encoded representation of an ISCC

ISCC Digest:
:	The raw binary data of an ISCC

## Introduction

An ISCC permanently identifies the content of a given digital media object at multiple levels of *granularity*. It is algorithmically generated from basic metadata and the contents of the digital media object which it identifies. It is designed for being registered and stored on a public and decentralized blockchain. An ISCC for a media object can be created and registered by the content author, a publisher, a service provider or anybody else. By itself the ISCC and its basic registration on a blockchain does not make any statement or claim about authorship or ownership of the identified content.

## ISCC Structure

The ISCC Digest is a fixed size sequence of 36 bytes (288 bits) assembled from multiple sub-components. The printable ISCC Code is a 52 character encoded string representation of an ISCC Digest. This is a high-level overview of the ISCC creation process:

![iscc-creation-process](images/iscc-creation-process.svg)

### ISCC Components

The ISCC Digest is built from multiple self-describing 72-bit components:


| Components:     | Meta-ID             | Content-ID         | Data-ID           | Instance-ID    |
| :-------------- | :------------------ | :----------------- | :---------------- | :------------- |
| **Context:**    | Intangible creation | Content similarity | Data similarity   | Data checksum  |
| **Input:**      | Metadata            | Extracted  content | Raw data          | Raw data       |
| **Algorithms:** | Similarity Hash     | Type specific      | CDC, Minimum Hash | CDC, Hash Tree |
| **Size:**       | 72 bits             | 72 bits            | 72 bits           | 72 bits        |

These components MAY be used independently by applications for various purposes but MUST be combined into a case-sensitive 52 character [base58-iscc](#base58-iscc-encoding) encoded string (55 with hyphens) for a fully qualified ISCC Code. The components MUST be combined in the fixed order of Meta-ID, Content-ID, Data-ID, Instance-ID and MAY be separated by hyphens.

!!! example "Pritable ISCC Code"
    ISCC: 11cS7Y9NjD6DX-1DVcUdv5ewjDQ-1Qhwz8x54CShu-1d8uCbWCNbGWg

#### Component Types

Each component has the same basic structure of a **1-byte header** and a **8-byte body** section. 

The 1-byte header of each component is subdivided into 2 nibbles (4 bits). The first nibble specifies the component type while the second nibble is component specific.

The header only needs to be carried in the encoded representation. As similarity searches accross different components are of little use, the type information contained in the header of each component can be safely ignored after an ISCC has been decomposed and internaly typed by an application. 

The body section of each component is always 8-bytes and can thus be fit into a 64-bit integer for efficient data processing. 

| Component              | Nibble-1 | Nibble-2                        | Byte |
| :--------------------- | :------- | :------------------------------ | :--- |
| *Meta-ID*              | 0000     | 0000 - ISCC version (0)         | 0x00 |
| *Content-ID*-Text      | 0001     | 0000 - Content Type Text        | 0x10 |
| *Content-ID-Text PCF*  | 0001     | 0001 - Content Type Text  + PCF | 0x11 |
| *Content-ID-Image*     | 0001     | 0010 - Content Type Image       | 0x12 |
| *Content-ID-Image PCF* | 0001     | 0011 - Content Type Image + PCF | 0x13 |
| *Content-ID-Audio*     | 0001     | 0100 - Content Type Audio       | 0x14 |
| *Content-ID-Audio PCF* | 0001     | 0101 - Content Type Audio + PCF | 0x15 |
| *Data-ID*              | 0010     | 0000 - Reserved                 | 0x20 |
| *Instance-ID*          | 0011     | 0000 - Reserved                 | 0x30 |

#### Meta-ID Component

The Meta-ID component starts with a 1-byte header `00000000`. The first nibble `0000` indicates that this is a Meta-ID component type. The second nibble `0000` indicates that it belongs to an ISCC of version 1. All subsequent components are expected to follow the specification of a version 1 ISCC.

The Meta-ID body is built from a 64-bit `similarity_hash` over 4-character n-grams of the basic metadata of the content to be identified.  The basic metadata supplied to the META-ID generating function is assumed to be UTF-8 encoded. Errors that occur during the decoding of such a bytestring input to a native Unicode MUST terminate the process and must not be silenced. An ISCC generating application MUST provide a `meta_id` function that accepts minimal and generic metadata and returns a [Base58-ISCC encoded](#base58-iscc-encoding) Meta-ID component and trimmed metadata.

| Name    | Type    | Required | Description                                                  |
| :------ | :------ | :------- | :----------------------------------------------------------- |
| title   | text    | Yes      | The title of an intangible creation.                         |
| extra   | text    | No       | An optional short statement that distinguishes this intangible creation from another one for the purpose of Meta-ID uniqueness. (default: empty string) |
| version | integer | No       | ISCC version number. (default: 0)                            |

!!! note

    The basic metadata inputs are intentionally simple and generic. We abstain from more specific metadata for Meta-ID generation in favor of compatibility accross industries. Imagine a *creators* input-field for metadata. Who would you list as the creators of a movie? The directors, writers the main actors? Would you list some of them or if not how do you decide whom you will list. All disambiguation of similar title data can be acomplished with the extra-field. Industry- and application-specific metadata requirements can be supplied as extended metadata with ISCC registration.

##### Generate Meta-ID

An ISCC generating application must follow these steps in the given order to produce a stable Meta-ID:

1. Apply Unicode standard [Normalization Form KC (NFKC)](http://www.unicode.org/reports/tr15/#Norm_Forms) separately to the  `title` and `extra` inputs.
2. Trim `title` and `extra`, such that their UTF-8 encoded byte representation does not exceed 128-bytes each. *The results of this step MUST be supplied as basic metadata for ISCC registration.*
3. Concatenate trimmed`title` and `extra` from using a space ( `\u0020`) as a seperator.
4. Apply [`normalize_text`](#normalize-text) to the results of step 3.
5. Create a list of 4 character [n-grams](https://en.wikipedia.org/wiki/N-gram) by sliding character-wise through the result of step 4.
6. Encode each n-gram from step 5 to an UTF-8 bytestring and calculate its [xxHash64](http://cyan4973.github.io/xxHash/) digest.
7. Apply [`similarity_hash`](#similarity-hash) to the list of digests from step 6.
8. Prepend the 1-byte component header according to component type and ISCC version (e.g. `0x00`) to the results of step 7.
9. Encode the resulting 9 byte sequence with [Base58-ISCC Encoding](#base58-iscc-encoding)
10. Return encoded Meta-ID, trimmed `title` and trimmed `extra` data.


!!! warning "Text trimming"
    When trimming text be sure to trim the byte-length of the UTF-8 encoded version and not the number of characters. The trim point MUST be such, that it does not cut into multibyte characters. Characters might have different UTF-8 byte-length. For example `ü` is 2-bytes, `驩` is 3-bytes and `𠜎` is 4-bytes. So the trimmed version of a string with 128 `驩`-characters will result in a 42-character string with a 126-byte UTF-8 encoded length. This is necessary because the results of this operation will be stored as basic metadata with strict byte size limits on the blockchain. 

!!! tip "Pre-normalization"
    Applications that perform automated data-ingestion SHOULD apply a custimized preliminary normalization to title data tailored to the dataset. Depending on catalog data removing pairs of brackets [], (), {}, and text inbetween them or cutting all text after the first occurence of a semicolon (;) or colon (:) can vastly improve de-duplication. 

##### Dealing with Meta-ID collisions

Ideally we want multiple ISCCs that identify different manifestations of the *same intangible creation* to be automatically grouped by an identical leading Meta-ID component. We call such a natural grouping an **intended component collision**. Metadata, captured and edited by humans, is notoriously unreliable. By using normalization and a similarity hash on the metadata we account for some of this variation while keeping the Meta-ID component somewhat stable. 

Auto-generated Meta-IDs components are **expected** to miss some intended collisions. An application SHOULD check for such **missed intended component collisions** before registering a new Meta-ID with the *canonical registry* of ISCCs by conducting a similarity search and asking for user feedback.

But what about **unintended component collisions**? Such collisions might happen because two *different intangible creations* have very similar or even identical metadata. But they might also happen simply by chance. With 2^56 possibile Meta-ID components the probability of random collisions rises in an S-cuved shape with the number of deployed ISCCs (see: [Hash Collision Probabilities](http://preshing.com/20110504/hash-collision-probabilities/)).  We should keep in mind that, the Meta-ID component is only one part of a fully qualified ISCC Code. Unintended collisions of the Meta-ID component are generally deemed as **acceptable and expected**. 

If for any reason an application wants to avoid unintended collisions with pre-existing Meta-ID components it may utilze the `extra`-field. An application MUST first generate a Meta-ID without asking the user for input to the `extra`-field and then first check for collisions with the *canonical registry* of ISCCs. After it finds a collision with a pre-existing Meta-ID it may display the metadata of the colliding entry and interact with the user to determine if it indeed is an unintended collision. Only if the user indicates an unintended collision, may the application ask for a disambiguation that is than added as an ammendment to the metadata via the `extra`-field to create a different Meta-ID component. The application may repeat the pre-existence check until it finds no collision or a user intended collision. The application MUST NOT supply autogenerated input to the `extra`-field.

It is our opinion that the concept of **intended collisions** of Meta-ID components is generally usefull concept and a net positive. But one must be aware that this characteristic also has its pitfalls. It is by no means an attempt to provide an unambigous - agreed upon - definition of *"identical intangible creations"*.

#### Content-ID Component

The Content-ID component has multiple subtypes. The subtypes correspond with the **Generic Media Types (GMT)**. A fully qualified ISCC can only have a Content-ID component of one specific GMT, but there may be multiple ISCCs with different Content-ID types per digital media object.

A Content-ID is generated in two broad steps. In the first step, we extract and convert content from a rich media type to a normalized GMT. In the second step, we use a GMT-specific process to generate the Content-ID component of an ISCC. 

##### Generic Media Types

The  Content-ID type is signaled by the first 3 bits of the second nibble of the first byte of the Content-ID:

| Conent-ID Type | Nibble-2 Bits 0-3 | Description                                        |
| :------------- | :---------------- | -------------------------------------------------- |
| text           | 000               | Generated from extracted and normalized plain-text |
| image          | 001               | Generated from normalized gray-scale pixel data    |
| *audio*        | *010*             | To be defined in later version of specification    |
| *video*        | *011*             | To be defined in later version of specification    |
| *mixed*        | *100*             | To be defined in later version of specification    |
|                | 101, 110, 111     | Reserved for future versions of specification      |

##### Content-ID-Text

The Content-ID-Text is built from the extracted plain-text content of an encoded media object. To build a stable Content-ID-Text the plain-text content must first be extracted from the digital media object. It should be extracted in a way that is reproducible. There are many different text document formats out in the wilde and extracting plain-text from all of them is anything but a trivial task. While text-extraction is out of scope for this specification it is RECOMMENDED, that plain-text content SHOULD be extracted with the open-source [Apache Tika v1.17](https://tika.apache.org/) toolkit, if a generic reproducibility of the Content-ID-Text component is desired. 

An ISCC generating application MUST provide a `content_id(text, partial=False)` function that accepts UTF-8 encoded plain text and a boolean indicating the [partial content flag](#partial-content-flag-pcf) as input and returns a Content-ID with GMT type `text`. The procedure to create a Content-ID-Text is as follows:

1. Apply Unicode standard [Normalization Form KC (NFKC)](http://www.unicode.org/reports/tr15/#Norm_Forms) to the text input.
2. Apply [`normalize_text`](#normalize-text) to the text input.
3. Split the normalized text into a list of words at whitespace boundaries.
4. Create a list of 5 word shingles by sliding word-wise through the list of words.
5. Create  a list of 32-bit unsigned integer features by applying [xxHash32](http://cyan4973.github.io/xxHash/) to shingles from step 4.
6. Apply `minimum_hash` to the list of features from step 5.
7. Collect the least significant bits from the 128 MinHash features from step 6.
8. Create two 64-bit digests from the first and second half of the collected bits.
9. Apply [`similarity_hash`](#similarity-hash) to the digests returned from step 8.
10. Prepend the 1-byte component header (`0x10` full content or `0x11` partial content).
11. Encode and return the resulting 9-byte sequence with [Base58-ISCC Encoding](#base58-iscc-encoding).

##### Content-ID-Image

For the Content-ID-Image we are opting for a DCT-based perceptual image hash instead of a more sophisticated keypoint detection based method. In view of the generic deployabiility of the ISCC we chose an algorithm that has moderate computation requirements and is easy to implement while still being robust against most common minor image manipulations. 

An ISCC generating application MUST provide a `content_id_image(image, partial=False)` function that accepts a local file path to an image and returns a Content-ID with GMT type `image`. The procedure to create a Content-ID-Image is as follows:

1. Convert image to greyscale
2. Resize the image to 32x32 pixels using [bicubic interpolation](https://en.wikipedia.org/wiki/Bicubic_interpolation)
3. Create a 32x32 two-dimensional array of 8-bit greyscale values from the image data
4. Perform a discrete cosine transform per row
5. Perform a DCT per column on the resulting matrix from step 4.
5. Extract upper left 8x8 corner of array from step 4 as a flat list
6. Calculate the median of the results from step 5
7. Create a 64-bit digest by iterating over the values of step 5 and setting a  `1`- for values above median and `0` for values below or equal to median.
9. Prepend the 1-byte component header (`0x12` full content or `0x13` partial content)
10. Encode and return the resulting 9-byte sequence with [Base58-ISCC Encoding](#base58-iscc-encoding)

!!! note "Image Data Input"
    The `content_id_image` function may optionally accept the raw byte data of an encoded image or an internal native image object as input for convenience.

##### Partial Content Flag (PCF)

The last bit of the header byte is the "Partial Content Flag". It designates if the Content-ID applies to the full content or just some part of it. The PCF MUST be set as a `0`-bit (**full GMT-specific content**) by default. Setting the PCF to `1` enables applications to create multiple ISCCs for partial extracts of one and the same digital file. The exact semantics of *partial content* are outside of the scope of this specification. Applications that plan to support partial Content-IDs SHOULD clearly define their semantics. For example, an application might create separate ISCC for the text contents of multiple articles of a magazine issue. In such a scenario
the Meta-, Data-, and Instance-IDs are the compound key for the magazine issue, while the Content-ID-Text component distinguishes the different articles of the issue. The different Content-ID-Text components would automatically be "bound" together by the other 3 components.

#### Data-ID Component

For the Data-ID that should encode data similarty we use content defined chunking algorithm that provides some shift resistance and calculate the MinHash from those chunks. To accomodate for small files the first 100 chunks have a ~140-byte size target while the remaining chunks target ~ 6kb in size.

The Data-ID is built from the raw encoded data of the content to be identified. An ISCC generating application MUST provide a `data_id` function that accepts the raw encoded data as input. 

##### Generate Data-ID

1. Apply `chunk_data` to the raw encoded content data.
2. For each chunk calculate the xxHash32 integer hash.
3. Apply `minimum_hash` to the resulting list of 32-bit unsigned integers.
4. Collect the least significant bits from the 128 MinHash features.
5. Create two 64-bit digests from the first and second half of the collected bits.
6. Apply `similarity_hash` to the results of step 5.
7. Prepend the 1-byte component header (e.g. 0x20).
8. Encode and return the resulting 9-byte sequence with [Base58-ISCC Encoding](#base58-iscc-encoding).

#### Instance-ID Component

The Instance-ID is built from the raw data of the media object to be identified and serves as checksum for the media object. The raw data of the media object is split into 64-kB data-chunks. Then we build a hash-tree from those chunks and use the truncated top-hash (merkle root) as component body of the Instance-ID.

To guard against length-extension attacks and second pre-image attacks we use double sha256 for hashing. We also prefix the hash input data with a `0x00`-byte for the leaf nodes hashes and with a `0x01`-byte for the  internal node hashes. While the Instance-ID itself is a non-cryptographic checksum, the full top-hash may be supplied in the extended metadata of an ISCC secure integrity verification is required.

![iscc-creation-instance-id](images/iscc-creation-instance-id.svg)

An ISCC generating application MUST provide a `instance_id` function that accepts the raw data file as input and returns an encoded Instance-ID and a full hex-encoded 256-bit top-hash. 

##### Generate Instance-ID

1. Split the raw bytes of the encoded media object into 64-kB chunks.
2. For each chunk calculate the sha256d of the concatenation of a `0x00`-byte and the chunk bytes. We call the resulting values *leaf node hashes* (LNH).
3. Calculate the next level of the hash tree by applying sha256d to the concatenation of a `0x01`-byte and adjacent pairs of LNH values. If the length of the list of LNH values is uneven concatenate the last LNH value with itself. We call the resulting values *internal node hashes* (INH).
4. Recursively apply `0x01`-prefixed pairwise hashing to the results of  step 3 until the process yields only one hash value. We call this value the top-hash.
5. Trim the resulting *top hash* to the first 8 bytes.
6. Prepend the 1-byte component header (e.g. `0x30`).
7. Encode resulting 9-byte sequence with [Base58-ISCC Encoding](#base58-iscc-encoding) to an Instance-ID Code
8. Hex-Encode the *top hash* 
9. Return the Intance-ID and the hex-encoded top-hash

Applications may carry, store, and process the leaf node hashes or even the full hash-tree for advanced streaming data identification or partial data integrity verification.

## ISCC Metadata

As a generic content identifier the ISCC makes minimal assumptions about metadata that must or should be supplied together with an ISCC. The RECOMMENDED data-interchange format for ISCC metadata is [JSON](https://www.json.org/). We distingquish between **Basic Metadata** and **Extended Metadata**:

### Basic Metadata

Basic metadata for an ISCC is metadata that is explicitly defined by this specification. The following table enumarates basic metadata fields for use in the top-level of the JSON metadata object:

| Name    | Type       | Required | Description                                                  |
| ------- | ---------- | -------- | ------------------------------------------------------------ |
| version | integer    | No       | Version of ISCC Specification. Assumed to be 1 if omitted.   |
| title   | text       | Yes      | The title of an intangible creation identified by the ISCC. The normalized and trimmed UTF-8 encoded text MUST not exceed 128 Bytes. The result of processing `title` and `extra` data with the `meta_id` function MUST  match the Meta-ID component of the ISCC. |
| extra   | text       | No       | An optional short statement that distinguishes this intangible creation from another one for the purpose of Meta-ID uniqueness. |
| hash    | text (hex) | No       | The full hex-encoded top-hash (merkle root) retuned by the `instance_id`  function. |
| meta    | array      | No       | A list of one or more **extended metadata** entries. Must include at least one entry if specified. |

!!! attention
    Depending on adoption and real world use, future versions of this specification may define new basic metadata fields. Applications MAY add custom fields at the top level of the JSON object but MUST prefix those fields with an underscore to avoid collisions with future extensions of this specification.

### Extended Metadata

Extended metadata for an ISCC is metadata that is not explixitly defined by this specification. All such metadata SHOULD be supplied as JSON objects within the top-level `meta`array field. This allows for a flexible and extendable way to supply additional industry specific metadata about the identified content. 

Extended metadata entries MUST be wrapped in JSON object of the following structure:

| Name      | Description                                                  |
| --------- | ------------------------------------------------------------ |
| schema    | The `schema`-field may indicate a well known metadata schema (such as Dublin Core, IPTC, ID3v2, ONIX) that is used. RECOMMENDED `schema`: "[schema.org](http://schema.org/)" |
| mediatype | The `mediatype`-field specifies an [IANA Media Type](https://www.iana.org/assignments/media-types/media-types.xhtml). RECOMMENDED `mediatype`: "application/ld+json" |
| url       | An URL that is expected to host the metadata with the indicated `schema` and `mediatype`. This field is only required if the `data`-field is omitted. |
| data      | The `data`-field holds the metadata conforming to the indicated `schema` and `mediatype.` It is only required if the`url` field is omitted. |

## ISCC Registration

The ISCC is a decentralized identifier. ISCCs can be generated by anybody who is in posession of the content. There is also no central authority for the registration of ISCC identifiers or even certification of content authorship.

As an open system the ISCC allows any person or organization to offer ISCC registration services as they see fit and without the need to ask anyone for permission. This also presumes that no person or organization may claim exclusive authority about ISCC registration. 

Nevertheless a well known open and public registry for canonical discoverability of ISCC identified content is of great value. For this reason it is RECOMMENDED to register your ISCC identifiers on the open `iscc` data-stream of the [Content Blockchain](https://content-blockchain.org/). For details please refer to the [ISCC-Stream specification](https://coblo.github.io/cips/cip-0003-iscc/) of the Content Blockchain.

## ISCC URI Scheme

The purpose of the ISCC URI scheme based on [RFC 3986](https://www.ietf.org/rfc/rfc3986.txt) is to enable users to easily discover information like metadata or license offerings about a ISCC marked content by simply clicking a link on a webpage or by scanning a QR-Code. 

The scheme name is `iscc`. The path component MUST be a fully qualified ISCC Code without hyphens. An optional `stream` query key MAY indicate the blockchain stream information source. If the `stream` query key is omitted applications SHOULD return information from the open [ISCC Stream](https://coblo.github.io/cips/cip-0003-iscc/).

The scheme name component ("iscc:") is case-insensitive. Applications MUST accept any combination of uppercase and lowercase leters in the scheme name. All other URI components are case-sensitive.

Applications MAY register themselves as handler for the "iscc:" URI scheme if no other handler is already registered. If another handler is already registered an application MAY ask the user to change it on the first run of the application.

### URI Syntax

`<foo>` means placeholder, `[bar]` means optional.

```
iscc:<fq-iscc-code>[?stream=<name>]
```

### URI Example

```
iscc:11TcMGvUSzqoM1CqVA3ykFawyh1R1sH4Bz8A1of1d2Ju4VjWt26S?stream=smart-license
```



## Procedures & Algorithms

### Base58-ISCC Encoding

The ISCC uses a custom per-component data encoding that is based on the [zbase62](https://github.com/simplegeo/zbase62) encoding by [Zooko Wilcox-O'Hearn](https://en.wikipedia.org/wiki/Zooko_Wilcox-O%27Hearn). The encoding does not require padding and will always yield component codes of 13 characters length for our 72-bit digests. The predictable size of the encoding is a property that allows for easy composition and decomposition of components without having to rely on a delimiter (hyphen) in the ISCC code representation. Colliding body segments of the digest are preserved by encoding the header and body separately. The symbol table also minimizes transcription and OCR errors by omitting the easily confused characters `'O', '0', 'I', 'l'`.

#### encode(digest)

The `encode` function accepts a 9-byte **ISCC Component Digest** and returns the Base58-ISCC encoded  alphanumeric string of 13 characters which we call the **ISCC-Component Code**.

#### decode(code)

the `decode` function accepts a 13-character **ISCC-Component Code** and returns the corresponding 9-byte **ISCC-Component Digest**.

### Normalize Text

We define a text normalization function that is specific to our application. It takes unicode text as an input and returns *normalized* Unicode text for further algorithmic processing. We reference this function by the name `normalize_text`. The `normalize_text` function performs the following operations in the given order while each step works with the results of the previous operation:

1. Decompose the input text by applying [Unicode Normalization Form D (NFD)](http://www.unicode.org/reports/tr15/#Norm_Forms).
2. Replace each group of one or more consecutive `Separator` characters ([Unicode categories](https://en.wikipedia.org/wiki/Unicode_character_property) Zs, Zl and Zp) with exactly one Unicode `SPACE` character (`U+0020`) .
3. Remove any leading or trailing `Separator` characters.
4. Remove each character that is not in one of the Unicode categories `Separator` , `Letter`, `Number` or `Symbol`.
5. Convert all characters to lower case.
6. Re-Compose the text by applying `Unicode Normalization Form C (NFC)`.
7. Return the resulting text.

### Similarity Hash

The `similarity_hash` function takes a sequence of hash digests (raw 8-bit bytes) which represent a set of features. Each of the digests MUST be of equal size. The function returns a new hash digest (raw 8-bit bytes) of the same size. For each bit in the input hashes calulate the number of hashes with that bit set and substract the the count of hashes where it is not set. For the output hash set the same bit position to `0` if the count is negative or `1` if it is zero or positive. The resulting hash digest will retain similarity for similar sets of input hashes. See also  [[Charikar2002]][#Charikar2002].

#### Diagram (SH)

![iscc-similarity-hash](images/iscc-similarity-hash.svg)

### Minimum Hash

The `minimum_hash` function takes an arbitrary sized set of 32-bit integer features and reduces it to a fixed size vector of 128 features such that it preserves similarity with other sets. It is based on the MinHash implementation of the [datasketch](https://ekzhu.github.io/datasketch/) library by [Eric Zhu](https://github.com/ekzhu).

## Conformance Testing

An application that claims ISCC conformance MUST pass the ISCC conformance test suite. The test suite is available as json data in our [Github Repository](https://raw.githubusercontent.com/coblo/iscc-specs/master/tests/test_data.json). Testdata is stuctured as follows:

```json
{
    "<function_name>": {
        "<test_name>": {
            "inputs": ["<func_input_value1>", "<func_input_value2>"],
            "outputs": ["<func_output_value1>", "<func_output_value2>"]
        }
    }
}
```

*[CDC]: Content defined chunking

*[ISCC Code]: Base58-ISCC encoded string representation of an ISCC

*[ISCC Digest]: Raw binary data of an ISCC

*[ISCC ID]: Integer representation of an ISCC

*[ISCC]: International Standard Content Code

*[M-ID]: Meta-ID Component

*[C-ID]: Content-ID Component

*[D-ID]: Data-ID Component

*[I-ID]: Instance-ID Component

*[GMT]: Generic Media Type

*[PCF]: Partial Content Flag

*[LNH]: Leaf Node Hash - A hash of a data-chunk.

*[INH]: Internal Node Hash - A hash of concatenated hashes in a hash-tree.

*[character]: A character is defined as one Unicode code point

*[sha256d]: Double SHA256

[#Charikar2002]:  http://dx.doi.org/10.1145/509907.509965 "Charikar, M.S., 2002, May. Similarity estimation techniques from rounding algorithms. In Proceedings of the thiry-fourth annual ACM symposium on Theory of computing (pp. 380-388). ACM."
