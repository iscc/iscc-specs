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
        "code": "AAA77PPFVQJUAP6S",
        "extra": '"@context":"http://schema.org/","@type":"Person","jobTitle":"Professor","name":"Jane '
        'Doe","telephone":"425 1234567","url":"http://www.janedoe.com"',
        "metahash": "b7b701a9c02155f5d617b55477d49950f670d5ac4ed97f6ba12948fff312d3c2",
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
        "metahash": "e2f123b51f44268f1361f513629c3013366a853075fb32329b3316727313e837",
        "title": "Hello World",
    }
