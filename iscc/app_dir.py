# -*- coding: utf-8 -*-
"""
Print application directory. Usefull for CI.

Usage:

$python -m iscc.app_dir
"""
import iscc


def main():
    print(iscc.APP_DIR)


if __name__ == "__main__":
    main()
