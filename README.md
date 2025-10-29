# imapdump
[![Upload Python Package](https://github.com/das-kaesebrot/imapdump/actions/workflows/python-publish.yml/badge.svg)](https://github.com/das-kaesebrot/imapdump/actions/workflows/python-publish.yml)

`imapdump` is a cli based tool to export an IMAP account to a local folder.

## Installation

Install the module from [PyPI](https://pypi.org/project/imapdump/):
```bash
$ pip install imapdump
```

or simply run it using [`uvx`](https://docs.astral.sh/uv/guides/tools/) (recommended):
```bash
$ uvx imapdump [args...]
```

## Usage
Launch the application via the included command `imapdump`.

You may also run it using [`uv tool run`](https://docs.astral.sh/uv/guides/tools/) (recommended method).

```bash
# regular pip install
$ imapdump -h
# ...or uvx
$ uvx imapdump -h
usage: dump.py [-h] [-l {critical,fatal,error,warn,info,debug}] [--host HOST] [-f DATABASE_FILE] [-p PORT] [-u USERNAME]
                   [--password PASSWORD] [--encryption-mode {none,ssl,starttls}] [--folder-regex FOLDER_REGEX] [--force-dump]
                   [--dump-folder DUMP_FOLDER] [--config CONFIG]

Dump IMAP accounts to a local directory

options:
  -h, --help            show this help message and exit
  -l, --logging {critical,fatal,error,warn,info,debug}
                        set the log level (default: info)
  --host HOST           Hostname of the IMAP server (default: None)
  -f, --file DATABASE_FILE
                        Database file (default: None)
  -p, --port PORT       Port of the IMAP server (default: 993)
  -u, --username USERNAME
                        Username for the IMAP account (default: None)
  --password PASSWORD   Password of the IMAP account (default: None)
  --encryption-mode {none,ssl,starttls}
                        IMAP encryption mode (default: ssl)
  --folder-regex FOLDER_REGEX
                        Pattern to match against for including folders (default: ^.*$)
  --force-dump          Force dump all matching messages without checking against existing database (default: False)
  --mirror              Remove all unknown files and folders from output folder and exactly mirror server state (default: False)
  --dump-folder DUMP_FOLDER
                        Where to dump .eml files to (default: None)
  --config CONFIG       Supply a config file (default: None)
```

## Configuration
Create a `config.yml`.

Example configuration:
```yaml
host: imap.example.com
username: user
password: supers3cr3tp4ssw0rd
loglevel: info
dump_folder: /path/to/dump/folder
mirror: true
```

Then run the application:
```bash
$ imapdump -l debug --config config.yml
```

## Open Source License Attribution

This application uses Open Source components. You can find the source code of their open source projects along with license information below. We acknowledge and are grateful to these developers for their contributions to open source.
### [dacite](https://github.com/konradhalas/dacite)
- Copyright (c) [Konrad Hałas](https://github.com/konradhalas) and contributors
- [MIT License](https://github.com/konradhalas/dacite/blob/master/LICENSE)

### [PyYAML](https://pyyaml.org/)
- Copyright (c) [The YAML Project](https://github.com/yaml) and contributors
- [MIT License](https://github.com/yaml/pyyaml/blob/main/LICENSE)

### [imapclient](https://github.com/mjs/imapclient/)
- Copyright (c) 2014 [Menno Smits](https://github.com/mjs) and contributors
- [New BSD License](https://github.com/mjs/imapclient/blob/master/COPYING)
