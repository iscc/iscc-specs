title: ISCC - Implementations
description: Implementations of ISCC Codes
authors: Titusz Pan

# ISCC - Implementations

## Developer Libraries

| Language    | Author(s)                                                 | URL                                  |
| ----------- | --------------------------------------------------------- | ------------------------------------ |
| Python3     | Patricia Schinke, [Titusz Pan](https://github.com/titusz) | https://pypi.python.org/pypi/iscc    |
| Go (golang) | Patricia Schinke, Marvin Schmies                          | https://github.com/coblo/iscc-golang |
| C# .Net     | [Jason Madden](https://github.com/dirric)                 | https://github.com/iscc/iscc-dotnet  |
| Rust        | [Alexander Niederbühl](https://github.com/Alexander-N)             | https://github.com/iscc/iscc-rs  |

If you are missing an implementation in your favorite programming language, please feel free to port it over. The reference implementation is a [single python module](https://github.com/coblo/iscc-specs/blob/master/src/iscc/iscc.py) and we have language independent [test data in JSON](https://github.com/coblo/iscc-specs/blob/master/tests/test_data.json).

## Software & Tools

- [ISCC CLI](https://github.com/iscc/iscc-cli) - Command line tool that creates ISCC Codes from media files

## Early Prototypes

!!! warning
    These a are early prototype demos. Please be aware that they do not represent the current state. Many things have changed since those prototypes where build.

- Blockchain wallet demo: https://github.com/coblo/gui-demo
- Smart License demo: https://github.com/coblo/smartlicense
- Early concept demo: https://isccdemo.content-blockchain.org/
