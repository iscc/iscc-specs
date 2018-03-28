# -*- coding: utf-8 -*-
import yaml
import json
import iscc


def main():
    data = yaml.load(open('test_inputs.yaml', 'rb'))
    for funcname, tests in data.items():
        for testname, testdata in tests.items():
            func = getattr(iscc, funcname)
            args = testdata['inputs']
            result = func(*args)
            if funcname in ['data_chunks']:
                result = ['hex:' + data.hex() for data in result]
                print(len(result))
            testdata['outputs'] = result
    with open('test_data.json', 'w', encoding='utf-8') as outf:
        json.dump(data, outf, indent=2, sort_keys=True, ensure_ascii=False)


if __name__ == '__main__':
    main()
