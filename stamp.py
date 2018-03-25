# -*- coding: utf-8 -*-
"""Generate an ISCC-Text for this specification"""
import os
import iscc


def get_content(mode='text'):

    content = '' if mode == 'text' else b''
    if mode == 'text':
        for root, dirs, files in os.walk('docs'):
            for f in files:
                if f.endswith('.md'):
                    path = os.path.join(root, f)
                    with open(path, 'r', encoding='utf-8') as textfile:
                        content += textfile.read()
    if mode == 'data':
        for root, dirs, files in os.walk('site'):
            for f in files:
                path = os.path.join(root, f)
                with open(path, 'rb') as datafile:
                    content += datafile.read()

    return content


def main():
    title = "ISCC - Content Identifiers"
    extra = "Version 0.9.7"
    text = get_content('text')
    data = get_content('data')
    mid, title, extra = iscc.meta_id(title, extra)
    cidt = iscc.content_id_text(text)
    did = iscc.data_id(data)
    iid, hash_ = iscc.instance_id(data)
    code = ''.join((mid, cidt, did, iid))
    print('ISCC:', code)
    print('Title:', title)
    if extra:
        print('Extra:', extra)
    print('Hash:', hash_)


if __name__ == '__main__':
    main()
