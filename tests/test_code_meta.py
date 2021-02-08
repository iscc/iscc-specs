# -*- coding: utf-8 -*-
import iscc


def test_code_meta_empty():
    assert iscc.code_meta("") == {
        "code": "AAA26E2JXH27TING",
        "metahash": "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262",
        "title": "",
    }


def test_code_meta_hello_world():
    assert iscc.code_meta("Hello World") == {
        "code": "AAA77PPFVS6JDUQB",
        "metahash": "41f8394111eb713a22165c46c90ab8f0fd9399c92028fd6d288944b23ff5bf76",
        "title": "Hello World",
    }


def test_code_meta_hello_world_bytes():
    assert iscc.code_meta(b"Hello World") == {
        "code": "AAA77PPFVS6JDUQB",
        "metahash": "41f8394111eb713a22165c46c90ab8f0fd9399c92028fd6d288944b23ff5bf76",
        "title": "Hello World",
    }


def test_code_meta_extra_text():
    assert iscc.code_meta("Hello World", "Some Description") == {
        "code": "AAA77PPFVTPBZ5L7",
        "extra": "Some Description",
        "metahash": "543a47e96f1d6c6e2515a9f98484df6de4c819ae2f8b1d14a5d9b4751d3e4f0d",
        "title": "Hello World",
    }


def test_code_meta_extra_dict():
    assert iscc.code_meta("Hello World", {"Some": "Description"}) == {
        "code": "AAA77PPFVTNH55L7",
        "extra": '"Some":"Description"',
        "metahash": "ae4dfd36a9c6c1b2170f1328dbd0af11e0725713d50d3dabb7dacf5732e69623",
        "title": "Hello World",
    }


def test_code_meta_extra_schema_org():
    data = {
        "@context": "http://schema.org/",
        "@type": "Person",
        "name": "Jane Doe",
        "jobTitle": "Professor",
        "telephone": "(425) 123-4567",
        "url": "http://www.janedoe.com",
    }

    assert iscc.code_meta("Hello World", data) == {
        "code": "AAA77PPFVTLFYRO6",
        "extra": ':c14n0 <http://schema.org/jobTitle> "Professor" . :c14n0 '
        '<http://schema.org/name> "Jane Doe" . :c14n0 '
        '<http://schema.org/telephone> "425 1234567" . :c14n0 '
        "<http://schema.org/url> <http://www.janedoe.com> . :c14n0 "
        "<http://www.w3.org/1999/02/22rdfsyntaxns#type> "
        "<http://schema.org/Person> .",
        "metahash": "61aa0525902e5905b10d0a25ae799f6047b64d94b13a2ffb550b4799c20790a5",
        "title": "Hello World",
    }


def test_code_meta_extra_json_ld():
    jld = {
        "@context": {
            "ical": "http://www.w3.org/2002/12/cal/ical#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "ical:dtstart": {"@type": "xsd:dateTime"},
        },
        "ical:summary": "Lady Gaga Concert",
        "ical:location": "New Orleans Arena, New Orleans, Louisiana, USA",
        "ical:dtstart": "2011-04-09T20:00:00Z",
    }

    assert iscc.code_meta("Hello World", jld) == {
        "code": "AAA77PPFVRJXDZM6",
        "extra": ":c14n0 <http://www.w3.org/2002/12/cal/ical#dtstart> "
        '"20110409T20:00:00Z"^^<http://www.w3.org/2001/XMLSchema#dateTime> . '
        ':c14n0 <http://www.w3.org/2002/12/cal/ical#location> "New Orleans '
        'Arena, New Orleans, Louisiana, USA" . :c14n0 '
        '<http://www.w3.org/2002/12/cal/ical#summary> "Lady Gaga Concert" .',
        "metahash": "f1ee420d071a4e078942ff622fa7b85d74e776f99de8cd64298d94a61fb80029",
        "title": "Hello World",
    }
