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
        "metahash": "d916f95eaa226a1ffa3d1cb44e8f570cfbd4cb0e84f0d990c299d4f52e9709a2",
        "title": "Hello World",
    }


def test_code_meta_extra_dict():
    assert iscc.code_meta("Hello World", {"Some": "Description"}) == {
        "code": "AAA77PPFVTNH55L7",
        "extra": '"Some":"Description"',
        "metahash": "43af9020f7e93c602482d98fee0e723408ee84aa08e3f3ca5c6abd83fd07ebf5",
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
        "code": "AAA77PPFVQJUAP6S",
        "extra": '"@context":"http://schema.org/","@type":"Person","jobTitle":"Professor","name":"Jane '
        'Doe","telephone":"425 1234567","url":"http://www.janedoe.com"',
        "metahash": "e5e901c618337a9a467b48adaf0b696cc2ae53a5c75675d9c04fcbc388de55df",
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
        "code": "AAA77PPFVRF6BZOA",
        "extra": '"@context":"ical":"http://www.w3.org/2002/12/cal/ical#","ical:dtstart":"@type":"xsd:dateTime","xsd":"http://www.w3.org/2001/XMLSchema#","ical:dtstart":"20110409T20:00:00Z","ical:location":"New '
        'Orleans Arena, New Orleans, Louisiana, USA","ical:summary":"Lady '
        'Gaga Concert"',
        "metahash": "cc61ddc04fd00f335b757550d477e11357152b016bed686d67b742c9da93254f",
        "title": "Hello World",
    }
