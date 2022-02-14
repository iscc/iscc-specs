title: ISCC - Specification
description: Specification of International Standard Content Codes
authors: Titusz Pan

# ISCC - Specification v1.0.0

## Abstract

The **International Standard Content Code (ISCC)**, is an open and decentralized digital media identifier. An ISCC can be created from digital content and its basic metadata by anybody who follows the procedures of the ISCC specification or by using open source software that supports ISCC creation [conforming to the ISCC specification](#conformance-testing).

## Note to Readers

For public discussion of issues for this specification please use the Github issue tracker: <https://github.com/coblo/iscc-specs/issues>.

The latest published version of this specification can be found at <http://iscc.codes/specification/>.

Public review, discussion and contributions are welcome.

## About this Document

This document proposes an open and vendor neutral ISCC standard and describes the technical procedures to create and manage ISCC identifiers. The first version of this document is produced as a prototype by the [Content Blockchain Project](https://content-blockchain.org) and received funding from the [Google Digital News Initiative (DNI)](https://digitalnewsinitiative.com/dni-projects/content-blockchain-project/). The content of this document is determined by its authors in an open and public consensus process.

## Conventions and Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [[RFC 2119]](https://tools.ietf.org/html/rfc2119).

## Definitions

Basic Metadata:
: 	Minimal set of metadata about the content that is identified by an ISCC. This metadata may impact the derived Meta-Code Component

Character:
:    Throughout this specification a **character** is meant to be interpreted as one Unicode code point. This also means that due to the structure of Unicode a character is not necessarily a full glyph but might be a combining accent or similar.

Digital Media Object:
:    A blob of raw bytes with some media type specific encoding.

Extended Metadata:
:    Metadata that is not encoded within the ISCC Meta-Code but may be supplied together with the ISCC.

Generic Media Type:
:    A basic content type such as plain text in a normalized and *generic* ([UTF-8](https://en.wikipedia.org/wiki/UTF-8)) encoding format.

ISCC:
:    International Standard Content Code

ISCC Code:
:    The printable text encoded representation of an ISCC

ISCC Digest:
:    The raw binary data of an ISCC

## Introduction

An ISCC permanently identifies content at multiple levels of *granularity*. It is algorithmically generated from basic metadata and the contents of a digital media object. It is designed for being registered and stored on a public and decentralized blockchain. An ISCC for a media object can be created and registered by the content author, a publisher, a service provider or anybody else. By itself the ISCC and its basic registration on a blockchain does not make any statement or claim about authorship or ownership of the identified content.

## ISCC Structure

A **Fully Qualified ISCC Digest** is a fixed size sequence of **36 bytes (288 bits)** assembled from multiple sub-components. The **Fully Qualified  ISCC Code** is a **52 character** encoded printable string representation of a complete ISCC Digest. This is a high-level overview of the ISCC creation process:

![iscc-creation-process](images/iscc-creation-process.svg)

## ISCC Components

The ISCC Digest is built from multiple self-describing 72-bit components:


| Components:     | Meta-Code             | Content-Code         | Data-Code           | Instance-Code    |
| :-------------- | :------------------ | :----------------- | :---------------- | :------------- |
| **Context:**    | Intangible creation | Content similarity | Data similarity   | Data checksum  |
| **Input:**      | Metadata            | Extracted  content | Raw data          | Raw data       |
| **Algorithms:** | Similarity Hash     | Type specific      | CDC, Minimum Hash | CDC, Hash Tree |
| **Size:**       | 72 bits             | 72 bits            | 72 bits           | 72 bits        |

ISCC components MAY be used separately or in combination by applications for various purposes. Individual components MUST be presented as 13-character [base58-iscc](#base58-iscc) encoded strings to end users and MAY be prefixed with their component name.

!!! example "Single component ISCC-Code (13 characters)"

    **Meta-Code**: CCDFPFc87MhdT

Combinations of components MUST include the Meta-Code component and MUST be ordered as **Meta-Code**, **Content-Code**, **Data-Code**, and **Instance-Code**. Individual components MAY be skipped and SHOULD be separated with hyphens. A combination of components SHOULD be prefixed with "ISCC".

!!! example "Combination of ISCC-Code components"

    **ISCC**: CCPktvj3dVoVa-CTPCWTpGPMaLZ-CDL6QsUZdZzog

A **Fully Qualified ISCC Code** is an ordered sequence of Meta-Code, Content-Code, Data-Code, and Instance-Code codes. It SHOULD be prefixed with ISCC and MAY be separated by hyphens.

!!! example "Fully Qualified ISCC-Code (52 characters)"

    **ISCC**: CCDFPFc87MhdTCTWAGYJ9HZGj1CDhydSjutScgECR4GZ8SW5a7uc

!!! example "Fully Qualified ISCC-Code with hyphens (55 characters)"

    **ISCC**: CCDFPFc87MhdT-CTWAGYJ9HZGj1-CDhydSjutScgE-CR4GZ8SW5a7uc

### Component Types

Each component has the same basic structure of a **1-byte header** and a **8-byte body** section.

The 1-byte header of each component is subdivided into 2 nibbles (4 bits). The first nibble specifies the component type while the second nibble is component specific.

The header only needs to be carried in the encoded representation. As similarity searches across different components are of little use, the type information contained in the header of each component can be safely ignored after an ISCC has been decomposed and internally typed by an application.

#### List of Component Headers

| Component                | Nibble-1 | Nibble-2                        | Byte | Code |
| :----------------------- | :------- | :------------------------------ | :--- | ---- |
| **Meta-Code**              | 0000     | 0000 - ISCC version 1           | 0x00 | CC   |
| **Content-Code-Text**      | 0001     | 0000 - Content Type Text        | 0x10 | CT   |
| **Content-Code-Text PCF**  | 0001     | 0001 - Content Type Text  + PCF | 0x11 | Ct   |
| **Content-Code-Image**     | 0001     | 0010 - Content Type Image       | 0x12 | CY   |
| **Content-Code-Image PCF** | 0001     | 0011 - Content Type Image + PCF | 0x13 | Ci   |
| *Content-Code-Audio*       | 0001     | 0100 - Content Type Audio       | 0x14 | CA   |
| *Content-Code-Audio PCF*   | 0001     | 0101 - Content Type Audio + PCF | 0x15 | Ca   |
| *Content-Code-Video*       | 0001     | 0110 - Content Type Video       | 0x16 | CV   |
| *Content-Code-Video PCF*   | 0001     | 0111 - Content Type Video + PCF | 0x17 | Cv   |
| **Content-Code-Mixed**     | 0001     | 1000 - Content Type Mixed       | 0x18 | CM   |
| **Content-Code Mixed PCF** | 0001     | 1001 - Content Type Mixed + PCF | 0x19 | Cm   |
| **Data-Code**              | 0010     | 0000 - Reserved                 | 0x20 | CD   |
| **Instance-Code**          | 0011     | 0000 - Reserved                 | 0x30 | CR   |

The body section of each component is specific to the component and always 8-bytes and can thus be fit into a 64-bit integer for efficient data processing. The following sections give an overview of how the different components work and how they are generated.

### Meta-Code Component

The Meta-Code component starts with a 1-byte header `00000000`. The first nibble `0000` indicates that this is a Meta-Code component type. The second nibble `0000` indicates that it belongs to an ISCC of version 1. All subsequent components are expected to follow the specification of a version 1 ISCC.

The Meta-Code body is built from a 64-bit `similarity_hash` over 4-character n-grams of the basic metadata of the content to be identified.  The basic metadata supplied to the Meta-Code generating function is assumed to be UTF-8 encoded. Errors that occur during the decoding of such a bytestring input to a native Unicode MUST terminate the process and must not be silenced. An ISCC generating application MUST provide a `meta_id` function that accepts minimal and generic metadata and returns a [Base58-ISCC encoded](#base58-iscc) Meta-Code component and trimmed metadata.

#### Inputs to Meta-Code function

| Name    | Type    | Required | Description                                                  |
| :------ | :------ | :------- | :----------------------------------------------------------- |
| title   | text    | Yes      | The title of an intangible creation.                         |
| extra   | text    | No       | An optional short statement that distinguishes this intangible creation from another one for the purpose of Meta-Code uniqueness. (default: empty string) |
| version | integer | No       | ISCC version number. (default: 0)                            |

!!! note

    The basic metadata inputs are intentionally simple and generic. We abstain from more specific metadata for Meta-Code generation in favor of compatibility across industries. Imagine a *creators* input-field for metadata. Who would you list as the creators of a movie? The directors, writers the main actors? Would you list some of them or if not how do you decide whom you will list. All disambiguation of similar title data can be accomplished with the extra-field. Industry- and application-specific metadata requirements can be supplied as extended metadata with ISCC registration.

#### Generate Meta-Code

An ISCC generating application must follow these steps in the given order to produce a stable Meta-Code:

1. Verify the requested ISCC version is supported by your implementation.
2. Apply [`text_pre_normalize`](#text_pre_normalize) separately to the  `title` and `extra` inputs.
2. Apply [`text_trim`](#text_trim) to the results of step 1. *The results of this step MUST be supplied as basic metadata for ISCC registration.*
3. Concatenate trimmed `title` and `extra` from using a space ( `\u0020`) as a seperator.
4. Apply [`text_normalize`](#text_normalize) to the results of step 3.
5. Create a list of 4 character [n-grams](https://en.wikipedia.org/wiki/N-gram) by sliding character-wise through the result of step 4.
6. Encode each n-gram from step 5 to an UTF-8 bytestring and calculate its [xxHash64](http://cyan4973.github.io/xxHash/) digest.
7. Apply [`similarity_hash`](#similarity_hash) to the list of digests from step 6.
8. Prepend the 1-byte component header according to component type and ISCC version (e.g. `0x00`) to the results of step 7.
9. Encode the resulting 9 byte sequence with [`encode`](#encode)
10. Return encoded Meta-Code, trimmed `title` and trimmed `extra` data.


See also: [Meta-Code reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L20)

!!! warning "Text trimming"
    When trimming text be sure to trim the byte-length of the UTF-8 encoded version and not the number of characters. The trim point MUST be such, that it does not cut into multibyte characters. Characters might have different UTF-8 byte-length. For example `ü` is 2-bytes, `驩` is 3-bytes and `𠜎` is 4-bytes. So the trimmed version of a string with 128 `驩`-characters will result in a 42-character string with a 126-byte UTF-8 encoded length. This is necessary because the results of this operation will be stored as basic metadata with strict byte size limits on the blockchain.

!!! note "Automated Data-Ingestion"
    Applications that perform automated data-ingestion SHOULD apply a customized preliminary normalization to title data tailored to the dataset. Depending on catalog data removing pairs of brackets [], (), {}, and text in between them or cutting all text after the first occurence of a semicolon (;) or colon (:) can vastly improve deduplication.

#### Dealing with Meta-Code collisions

Ideally we want multiple ISCCs that identify different manifestations of the *same intangible creation* to be automatically grouped by an identical leading Meta-Code component. We call such a natural grouping an **intended component collision**. Metadata, captured and edited by humans, is notoriously unreliable. By using normalization and a similarity hash on the metadata we account for some of this variation while keeping the Meta-Code component somewhat stable.

Auto-generated Meta-Codes components are **expected** to miss some intended collisions. An application SHOULD check for such **missed intended component collisions** before registering a new Meta-Code with the *canonical registry* of ISCCs by conducting a similarity search and asking for user feedback.

But what about **unintended component collisions**? Such collisions might happen because two *different intangible creations* have very similar or even identical metadata. But they might also happen simply by chance. With 2^56 possibile Meta-Code components the probability of random collisions rises in an S-curved shape with the number of deployed ISCCs (see: [Hash Collision Probabilities](http://preshing.com/20110504/hash-collision-probabilities/)).  We should keep in mind that, the Meta-Code component is only one part of a fully qualified ISCC Code. Unintended collisions of the Meta-Code component are generally deemed as **acceptable and expected**.

If for any reason an application wants to avoid unintended collisions with pre-existing Meta-Code components it may utilize the `extra`-field. An application MUST first generate a Meta-Code without asking the user for input to the `extra`-field and then first check for collisions with the *canonical registry* of ISCCs. After it finds a collision with a pre-existing Meta-Code it may display the metadata of the colliding entry and interact with the user to determine if it indeed is an unintended collision. Only if the user indicates an unintended collision, may the application ask for a disambiguation that is then added as an amendment to the metadata via the `extra`-field to create a different Meta-Code component. The application may repeat the pre-existence check until it finds no collision or a user intended collision. The application MUST NOT supply auto-generated input to the `extra`-field.

It is our opinion that the concept of **intended collisions** of Meta-Code components is generally useful concept and a net positive. But one must be aware that this characteristic also has its pitfalls. It is by no means an attempt to provide an unambiguous - agreed upon - definition of *"identical intangible creations"*.

### Content-Code Component

The Content-Code component has multiple subtypes. The subtypes correspond with the **Generic Media Types (GMT)**. A fully qualified ISCC can only have one Content-Code component of one specific GMT, but there may be multiple ISCCs with different Content-Code types per digital media object.

A Content-Code is generated in two broad steps. In the first step, we extract and convert content from a rich media type to a normalized GMT. In the second step, we use a GMT-specific process to generate the Content-Code component of an ISCC.

#### Generic Media Types

The  Content-Code type is signaled by the first 3 bits of the second nibble of the first byte of the Content-Code:

| Conent-ID Type | Nibble 2 Bits 0-3 | Description                                        |
| :------------- | :---------------- | -------------------------------------------------- |
| text           | 000               | Generated from extracted and normalized plain-text |
| image          | 001               | Generated from normalized grayscale pixel data     |
| *audio*        | *010*             | To be defined in later version of specification    |
| *video*        | *011*             | To be defined in later version of specification    |
| mixed          | 100               | Generated from multiple Content-Codes                |
|                | 101, 110, 111     | Reserved for future versions of specification      |

#### Content-Code-Text

The Content-Code-Text is built from the extracted plain-text content of an encoded media object. To build a stable Content-Code-Text the plain-text content must first be extracted from the digital media object. It should be extracted in a way that is reproducible. There are many different text document formats out in the wilde and extracting plain-text from all of them is anything but a trivial task. While text-extraction is out of scope for this specification it is RECOMMENDED, that plain-text content SHOULD be extracted with the open-source [Apache Tika v1.17](https://tika.apache.org/) toolkit, if a generic reproducibility of the Content-Code-Text component is desired.

An ISCC generating application MUST provide a `content_id(text, partial=False)` function that accepts UTF-8 encoded plain text and a boolean indicating the [partial content flag](#partial-content-flag-pcf) as input and returns a Content-Code with GMT type `text`. The procedure to create a Content-Code-Text is as follows:

1. Apply [`text_pre_normalize`](#text_pre_normalize).
2. Apply [`text_normalize`](#text_normalize) to the text input.
3. Split the normalized text into a list of words at whitespace boundaries.
4. Create a list of 5 word shingles by sliding word-wise through the list of words.
5. Create  a list of 32-bit unsigned integer features by applying [xxHash32](http://cyan4973.github.io/xxHash/) to results of step 4.
6. Apply [`minimum_hash`](#minimum_hash) to the list of features from step 5.
7. Collect the least significant bits from the 128 MinHash features from step 6.
8. Create two 64-bit digests from the first and second half of the collected bits.
9. Apply [`similarity_hash`](#similarity_hash) to the digests returned from step 8.
10. Prepend the 1-byte component header (`0x10` full content or `0x11` partial content).
11. Encode and return the resulting 9-byte sequence with [`encode`](#encode).

See also: [Content-Code-Text reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L58)

#### Content-Code-Image

For the Content-Code-Image we are opting for a DCT-based perceptual image hash instead of a more sophisticated keypoint detection based method. In view of the generic deployability of the ISCC we chose an algorithm that has moderate computation requirements and is easy to implement while still being robust against common image manipulations.

An ISCC generating application MUST provide a `content_id_image(image, partial=False)` function that accepts a local file path to an image and returns a Content-Code with GMT type `image`. The procedure to create a Content-Code-Image is as follows:

1. Apply [`image_normalize`](#image_normalize) to receive a two-dimensional array of grayscale pixel data.
2. Apply [`image_hash`](#image_hash) to the results of step 1.
9. Prepend the 1-byte component header (`0x12` full content or `0x13` partial content) to results of step 2.
4. Encode and return the resulting 9-byte sequence with [`encode`](#encode)

See also: [Content-Code-Image reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L98)

!!! note "Image Data Input"
    The `content_id_image` function may optionally accept the raw byte data of an encoded image or an internal native image object as input for convenience.

!!! warning "JPEG Decoding"
    Decoding of JPEG images is non-deterministic. Different image processing libraries may yield diverging pixel data and result in different Image-IDs. The reference implementation currently uses the builtin decoder of the [Python Pillow](https://github.com/python-pillow/Pillow) imaging library. Future versions of the ISCC specification may define a custom deterministic JPEG decoding procedure.

#### Content-Code-Mixed

The Content-Code-Mixed aggregates multiple Content-Codes of the same or different types. It may be used for digital media objects that embed multiples types of media or for collections of contents of the same type. First we have to collect contents from the mixed media object or content collection and generate Content-Codes for each item. An ISCC conforming application must provide a `content_id_mixed` function that takes a list of Content-Code Codes as input and returns a Content-Code-Mixed. Follow these steps to create a Content-Code-Mixed:

Signature: `conent_id_mixed(cids: List[str], partial: bool=False) -> str`

1. Decode the list of Content-Codes.
2. Extract the **first 8-bytes** from each digest (**Note**: this includes the header part of the Content-Codes).
4. Apply [`similarity_hash`](#similarity_hash) to the list of digests from step 2.
4. Prepend the 1-byte component header(`0x18` full content or `0x19` partial content)
5. Apply [`encode`](#encode) to the result of step 5 and return the result.

See also: [Content-Code-Mixed reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L116)

#### Partial Content Flag (PCF)

The last bit of the header byte of the Content-Code is the "Partial Content Flag". It designates if the Content-Code applies to the full content or just some part of it. The PCF MUST be set as a `0`-bit (**full GMT-specific content**) by default. Setting the PCF to `1` enables applications to create multiple linked ISCCs of partial extracts of a content collection. The exact semantics of *partial content* are outside of the scope of this specification. Applications that plan to support partial Content-Codes MUST clearly define their semantics.

 ![Partial Contant Flag](images/iscc-pcf.svg)

!!! example "PCF Linking Example"

    Let's assume we have a single newspaper issue "The Times - 03 Jan 2009". You would generate one Meta-Code component with title "The Times" and extra "03 Jan 2009". The resulting Meta-Code component will be the grouping prefix in this szenario.

    We use a Content-Code-Mixed with PCF `0` (not partial) for the ISCC of the newspaper issue. We generate Data-Code and Instance-Code from the print PDF of the newspaper issue.

    To create an ISCC for a single extracted image that should convey context with the newspaper issue we reuse the Meta-Code of the newspaper issue and create a Content-Code-Image with PCF `1` (partial to the newspaper issue). For the Data-Code or Instance-Code of the image we are free to choose if we reuse those of the newspaper issue or create separate ones. The former would express strong specialization of the image to the newspaper issue (not likely to be useful out of context). The latter would create a stronger link to an eventual standalone ISCC of the image. Note that in any case the ISCC of the individual image retains links in both ways:

    - Image is linked to the newspaper issue by identical Meta-Code component
    - Image is linked to the standalone version of the image by identical Content-Code-Image body

    This is just one example that illustrates the flexibility that the PCF-Flag provides in concert with a grouping Meta-Code. With great flexibility comes great danger of complexity. Applications SHOULD do careful planning before using the PCF-Flag with internally defined semantics.

### Data-Code Component

For the Data-Code that encodes data similarity we use a content defined chunking algorithm that provides some shift resistance and calculate the MinHash from those chunks. To accomodate for small files the first 100 chunks have a ~140-byte size target while the remaining chunks target ~ 6kb in size.

The Data-Code is built from the raw encoded data of the content to be identified. An ISCC generating application MUST provide a `data_id` function that accepts the raw encoded data as input.

#### Generate Data-Code

1. Apply [`data_chunks`](#data_chunks) to the raw encoded content data.
2. For each chunk calculate the xxHash32 integer hash.
3. Apply [`minimum_hash`](#minimum_hash) to the resulting list of 32-bit unsigned integers.
4. Collect the least significant bits from the 128 MinHash features.
5. Create two 64-bit digests from the first and second half of the collected bits.
6. Apply [`similarity_hash`](#similarity_hash) to the results of step 5.
7. Prepend the 1-byte component header (e.g. 0x20).
8. Apply [`encode`](#encode) to the result of step 5 and return the result.

See also: [Data-Code reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L137)

### Instance-Code Component

The Instance-Code is built from the raw data of the media object to be identified and serves as checksum for the media object. The raw data of the media object is split into 64-kB data-chunks. Then we build a hash-tree from those chunks and use the truncated tophash (merkle root) as component body of the Instance-Code.

To guard against length-extension attacks and second pre-image attacks we use double sha256 for hashing. We also prefix the hash input data with a `0x00`-byte for the leaf nodes hashes and with a `0x01`-byte for the  internal node hashes. While the Instance-Code itself is a non-cryptographic checksum, the full tophash may be supplied in the extended metadata of an ISCC secure integrity verification is required.

![iscc-creation-Instance-Code](images/iscc-creation-Instance-Code.svg)

An ISCC generating application MUST provide a `instance_id` function that accepts the raw data file as input and returns an encoded Instance-Code and a full hex-encoded 256-bit tophash.

#### Generate Instance-Code

1. Split the raw bytes of the encoded media object into 64-kB chunks.
2. For each chunk calculate the sha256d of the concatenation of a `0x00`-byte and the chunk bytes. We call the resulting values *leaf node hashes* (LNH).
3. Calculate the next level of the hash tree by applying sha256d to the concatenation of a `0x01`-byte and adjacent pairs of LNH values. If the length of the list of LNH values is uneven concatenate the last LNH value with itself. We call the resulting values *internal node hashes* (INH).
4. Recursively apply `0x01`-prefixed pairwise hashing to the results of  step 3 until the process yields only one hash value. We call this value the tophash.
5. Trim the resulting tophash to the first 8 bytes.
6. Prepend the 1-byte component header (e.g. `0x30`).
7. Encode resulting 9-byte sequence with [`encode`](#encode) to an Instance-Code Code
8. Hex-Encode the tophash
9. Return the Intance-ID and the hex-encoded tophash

See also: [Instance-Code reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L162)

Applications may carry, store, and process the leaf node hashes for advanced streaming data identification or partial data integrity verification.

## ISCC Metadata

As a generic content identifier the ISCC makes minimal assumptions about metadata that must or should be supplied together with an ISCC. The RECOMMENDED data-interchange format for ISCC metadata is [JSON](https://www.json.org/). We distinguish between **Basic Metadata** and **Extended Metadata**:

### Basic Metadata

Basic metadata for an ISCC is metadata that is explicitly defined by this specification. The following table enumerates basic metadata fields for use in the top-level of the JSON metadata object:

| Name    | Type       | Required | Description                                                  |
| ------- | ---------- | -------- | ------------------------------------------------------------ |
| version | integer    | No       | Version of ISCC Specification. Assumed to be 1 if omitted.   |
| title   | text       | Yes      | The title of an intangible creation identified by the ISCC. The normalized and trimmed UTF-8 encoded text MUST not exceed 128 Bytes. The result of processing `title` and `extra` data with the `meta_id` function MUST  match the Meta-Code component of the ISCC. |
| extra   | text       | No       | An optional short statement that distinguishes this intangible creation from another one for the purpose of Meta-Code uniqueness. |
| tophash | text (hex) | No       | The full hex-encoded tophash (merkle root) returned by the `instance_id`  function. |
| meta    | array      | No       | A list of one or more **extended metadata** entries. Must include at least one entry if specified. |

!!! attention
    Depending on adoption and real world use, future versions of this specification may define new basic metadata fields. Applications MAY add custom fields at the top level of the JSON object but MUST prefix those fields with an underscore to avoid collisions with future extensions of this specification.

### Extended Metadata

Extended metadata for an ISCC is metadata that is not explicitly defined by this specification. All such metadata SHOULD be supplied as JSON objects within the top-level `meta`array field. This allows for a flexible and extendable way to supply additional industry specific metadata about the identified content.

Extended metadata entries MUST be wrapped in JSON object of the following structure:

| Name      | Description                                                  |
| --------- | ------------------------------------------------------------ |
| schema    | The `schema`-field may indicate a well known metadata schema (such as Dublin Core, IPTC, ID3v2, ONIX) that is used. RECOMMENDED `schema`: "[schema.org](http://schema.org/)" |
| mediatype | The `mediatype`-field specifies an [IANA Media Type](https://www.iana.org/assignments/media-types/media-types.xhtml). RECOMMENDED `mediatype`: "application/ld+json" |
| url       | An URL that is expected to host the metadata with the indicated `schema` and `mediatype`. This field is only required if the `data`-field is omitted. |
| data      | The `data`-field holds the metadata conforming to the indicated `schema` and `mediatype.` It is only required if the `url` field is omitted. |

## ISCC Registration

The ISCC is a decentralized identifier. ISCCs can be generated for content by anybody who has access to the content. Due to the clustering properties of its components the ISCC provides utility in data interchange and de-duplication scenarios even without a global registry. There is no central authority for the registration of ISCC identifiers or certification of content authorship.

As an open system the ISCC allows any person or organization to offer ISCC registration services as they see fit and without the need to ask anyone for permission. This also presumes that no person or organization may claim exclusive authority about ISCC registration.

### Blockchain Registry

A well known, decentralized, open, and public registry for canonical discoverability of ISCC identified content is of great value. For this reason it is RECOMMENDED to register ISCC identifiers on the open `iscc` data-stream of the [Content Blockchain](https://content-blockchain.org/). For details please refer to the [ISCC-Stream specification](https://coblo.github.io/cips/cip-0003-iscc/) of the Content Blockchain.

## ISCC Embedding

Embedding ISCC codes into content is only RECOMMENDED if it does not create a side effect. We call it a side effect if embedding an ISCC code modifies the content to such an extent, that it yields a different ISCC code.

Side effects will depend on the combination of ISCC components that are to be embedded. A Meta-Code can always be embedded without side effect because it does not depend on the content itself. Content-Code and Data-Code may not change if embedded in larger media objects. Instance-Codes cannot easily be embedded as they will inevitably have a side effect on the post-embedding Instance-Code without special processing.

Applications MAY embed ISCC codes that have side effects if they specify a procedure by which the embedded ISCC codes can be stripped in such a way that the stripped content will yield the original embedded ISCC codes.

!!! example "ISCC Embedding"

    We are able to embed the following combination of components from the [markdown version](https://github.com/coblo/iscc-specs/edit/master/docs/specification.md) of this document into the document itself because adding or removing them has no side effect:

    **ISCC**: CCDbMYw6NfC8a-CTfLV4GoxGh7f-CDLmtRpZGVJhU

## ISCC URI Scheme

The purpose of the ISCC URI scheme based on [RFC 3986](https://www.ietf.org/rfc/rfc3986.txt) is to enable users to easily discover information like metadata or license offerings about a ISCC marked content by simply clicking a link on a webpage or by scanning a QR-Code.

The scheme name is `iscc`. The path component MUST be a fully qualified ISCC Code without hyphens. An optional `stream` query key MAY indicate the blockchain stream information source. If the `stream` query key is omitted applications SHOULD return information from the open [ISCC Stream](https://coblo.github.io/cips/cip-0003-iscc/).

The scheme name component ("iscc:") is case-insensitive. Applications MUST accept any combination of uppercase and lowercase letters in the scheme name. All other URI components are case-sensitive.

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

### Base58-ISCC

The ISCC uses a custom per-component data encoding similar to the [zbase62](https://github.com/simplegeo/zbase62) encoding by [Zooko Wilcox-O'Hearn](https://en.wikipedia.org/wiki/Zooko_Wilcox-O%27Hearn) but with a 58-character symbol table. The encoding does not require padding and will always yield component codes of 13 characters length for ths 72-bit component digests. The predictable size of the encoding is a property that allows for easy composition and decomposition of components without having to rely on a delimiter (hyphen) in the ISCC code representation. Colliding body segments of the digest are preserved by encoding the header and body separately. The ASCII symbol table also minimizes transcription and OCR errors by omitting the easily confused characters `'O', '0', 'I', 'l'` and is shuffled to generate human readable component headers.

!!! note "Symbol table"

    `SYMBOLS = "C23456789rB1ZEFGTtYiAaVvMmHUPWXKDNbcdefghLjkSnopRqsJuQwxyz"`

#### encode

Signature: `encode(digest: bytes) -> str`

The `encode` function accepts a 9-byte **ISCC Component Digest** and returns the Base58-ISCC encoded  alphanumeric string of 13 characters which we call the **ISCC-Component Code**.

See also: [Base-ISCC Encoding reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L464)

#### decode

Signature: decode(code: str) -> bytes

the `decode` function accepts a 13-character **ISCC-Component Code** and returns the corresponding 9-byte **ISCC-Component Digest**.

See also: [Base-ISCC Decoding reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L484)

### Content Normalization

The ISCC standardizes some content normalization procedures to support reproducible and stable identifiers. Following the list of normalization functions that MUST be provided by a conforming implementation.

#### text_pre_normalize

Signature: `text_pre_normalize(text: str|bytes) -> str `

Decodes raw plain-text data and applies Unicode [Normalization Form KC (NFKC)](http://www.unicode.org/reports/tr15/#Norm_Forms) . The plain-text data MUST be stripped of any markup beforehand. Text input is expected to be UTF-8 encoded plain-text data or a native type of the implementing programming language that supports Unicode. Text decoding errors MUST fail with an error.

See also: [Text pre-normalization reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L193)

#### text_trim

Signature: `text_trim(text: str) -> str`

Trim text such that its UTF-8 encoded byte representation does not exceed 128-bytes each.

See also: [Text trimming reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L202)

#### text_normalize

Signature: `text_normalize(text: str) -> str`

We define a text normalization function that is specific to our application. It takes unicode text as an input and returns *normalized* Unicode text for further algorithmic processing. The `text_normalize` function performs the following operations in the given order while each step works with the results of the previous operation:

1. Decompose the input text by applying [Unicode Normalization Form D (NFD)](http://www.unicode.org/reports/tr15/#Norm_Forms).
2. Filter and normalize text by iterating over unicode characters while:
   - replacing groups of one or more consecutive `Separator` characters ([Unicode categories](https://en.wikipedia.org/wiki/Unicode_character_property) Zs, Zl and Zp) with exactly one Unicode `SPACE` character (`U+0020`) .
   - removing characters that are not in one of the Unicode categories `Separator` , `Letter`, `Number` or `Symbol`.
   - converting characters to lowercase.
3. Remove any leading or trailing `Separator` characters.
4. Re-Compose the text by applying `Unicode Normalization Form C (NFC)`.

See also: [Text normalization reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L212)

#### image_normalize

Signature: `image_normalize(img) -> List[List[int]]`

Accepts a file path, byte-stream or raw binary image data and MUST at least support JPEG, PNG, and GIF image formats. Normalize the image with the following steps:

1. Convert the image to grayscale
2. Resize the image to 32x32 pixels using [bicubic interpolation](https://en.wikipedia.org/wiki/Bicubic_interpolation)
3. Create a 32x32 two-dimensional array of 8-bit grayscale values from the image data

See also: [Image normalization reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L237)

### Feature Hashing

The ISCC standardizes various feature hashing algorithms that reduce content features to a binary vector used as the body of the various Content-Code components.

#### similarity_hash

Signature: `similarity_hash(hash_digests: Sequence[ByteString]) -> bytes `

The `similarity_hash` function takes a sequence of hash digests which represent a set of features. Each of the digests MUST be of equal size. The function returns a new hash digest (raw 8-bit bytes) of the same size. For each bit in the input hashes calculate the number of hashes with that bit set and subtract the the count of hashes where it is not set. For the output hash set the same bit position to `0` if the count is negative or `1` if it is zero or positive. The resulting hash digest will retain similarity for similar sets of input hashes. See also  [[Charikar2002]][#Charikar2002].

![iscc-similarity-hash](images/iscc-similarity-hash.svg)

See also: [Similarity hash reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L262)

#### minimum_hash

Signature: `minimum_hash(features: Iterable[int]) -> List[int]`

The `minimum_hash` function takes an arbitrary sized set of 32-bit integer features and reduces it to a fixed size vector of 128 features such that it preserves similarity with other sets. It is based on the MinHash implementation of the [datasketch](https://ekzhu.github.io/datasketch/) library by [Eric Zhu](https://github.com/ekzhu).

See also: [Minimum hash reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L286)

#### image_hash

Signature: `image_hash(pixels: List[List[int]]) -> bytes`

1. Perform a discrete cosine transform per row of input pixels.
2. Perform a discrete cosine transform per column on the resulting matrix from step 2.
3. Extract upper left 8x8 corner of array from step 2 as a flat list.
4. Calculate the median of the results from step 3.
5. Create a 64-bit digest by iterating over the values of step 5 and setting a  `1`- for values above median and `0` for values below or equal to median.
6. Return results from step 5.

See also: [Image hash reference code](hhttps://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L305)

### Content Defined Chunking

For shift resistant data chunking the ISCC requires a custom chunking algorithm:

#### data_chunks

Signature: `data_chunks(data: stream) -> Iterator[bytes]`

The `data_chunks` function accepts a byte-stream and returns variable sized chunks. Chunk boundaries are determined by a gear based chunking algorithm based on [[WenXia2016]][#WenXia2016].

See also: [CDC reference code](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py#L365)

## Conformance Testing

An application that claims ISCC conformance MUST pass the ISCC conformance test suite. The test suite is available as json data in our [Github Repository](https://raw.githubusercontent.com/coblo/iscc-specs/master/tests/test_data.json). Test Data is structured as follows:

```json
{
    "<function_name>": {
        "<test_name>": {
            "inputs": ["<value1>", "<value2>"],
            "outputs": ["value1>", "<value2>"]
        }
    }
}
```

Outputs that are expected to be raw bytes are embedded as HEX encoded strings in JSON and prefixed with  `hex:` to support automated decoding during implementation testing.

!!! example
    Byte outputs in JSON testdata:

        {
          "data_chunks": {
            "test_001_cat_jpg": {
              "inputs": ["cat.jpg"],
              "outputs": ["hex:ffd8ffe1001845786966000049492a0008", ...]
            }
          }
        }


## License

Copyright © 2016 - 2018 **Content Blockchain Project**

<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons (CC BY-NC-SA 4.0)</a>.


*[CDC]: Content defined chunking

*[ISCC Code]: Base58-ISCC encoded string representation of an ISCC

*[ISCC Digest]: Raw binary data of an ISCC

*[ISCC ID]: Integer representation of an ISCC

*[ISCC]: International Standard Content Code

*[M-ID]: Meta-Code Component

*[C-ID]: Content-Code Component

*[D-ID]: Data-Code Component

*[I-ID]: Instance-Code Component

*[GMT]: Generic Media Type

*[PCF]: Partial Content Flag

*[LNH]: Leaf Node Hash - A hash of a data-chunk.

*[INH]: Internal Node Hash - A hash of concatenated hashes in a hash-tree.

*[character]: A character is defined as one Unicode code point

*[sha256d]: Double SHA256

*[tophash]: Root hash of an Instance-Code hash-tree

[#Charikar2002]:  http://dx.doi.org/10.1145/509907.509965 "Charikar, M.S., 2002, May. Similarity estimation techniques from rounding algorithms. In Proceedings of the thiry-fourth annual ACM symposium on Theory of computing (pp. 380-388). ACM."

[#WenXia2016]: http://dx.doi.org/10.1109/TC.2016.2595565 "Wen Xia, Yukun Zhou, Hong Jiang, Yu Hua, Yuchong Hu, Yucheng Zhang, Qing Liu, 2016. FastCDC: a Fast and Efficient Content-Defined Chunking Approach for Data Deduplication."
