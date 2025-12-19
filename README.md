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
usage: imapdump [-h] [-l {critical,fatal,error,warn,info,debug}] [--use-logfile] [--logfile-path LOGFILE_PATH]
                [--logfile-level {critical,fatal,error,warn,info,debug}] [--host HOST] [-f DATABASE_FILE] [-p PORT]
                [-u USERNAME] [--password PASSWORD] [--encryption-mode {none,ssl,starttls}] [--folder-regex FOLDER_REGEX]
                [--recreate | --mirror] [--dry-run] [--dump-folder DUMP_FOLDER] [-c ADDITIONAL_CONFIG_FILES]

Dump an IMAP account to a local directory

options:
  -h, --help            show this help message and exit
  -l, --logging {critical,fatal,error,warn,info,debug}
                        Console log level (default: info)
  --use-logfile         Write log files (default: False)
  --logfile-path LOGFILE_PATH
                        File to write log entries into (default: imapdump.log)
  --logfile-level {critical,fatal,error,warn,info,debug}
                        Log files log level (default: info)
  --host HOST           Hostname of the IMAP server (default: 127.0.0.1)
  -f, --file DATABASE_FILE
                        Database file (default: .imapdump-cache.db)
  -p, --port PORT       Port of the IMAP server (default: 993)
  -u, --username USERNAME
                        Username for the IMAP account (default: None)
  --password PASSWORD   Password of the IMAP account (default: None)
  --encryption-mode {none,ssl,starttls}
                        IMAP encryption mode (default: ssl)
  --folder-regex FOLDER_REGEX
                        Pattern to match against for including folders (default: ^.*$)
  --recreate            Recreate cache and recreate the dump directory (destructive, this will delete dumped files!),
                        then dump all matching messages (default: False)
  --mirror              Remove all unknown files and folders from output folder and exactly mirror server state (default:
                        False)
  --dry-run             Only simulate what would be done, don't actually write/change anything (default: False)
  --dump-folder DUMP_FOLDER
                        Where to dump .eml files to (default: dumped_mails)
  -c, --config ADDITIONAL_CONFIG_FILES
                        Supply a config file (can be specified multiple times) (default: None)
```

## Configuration
Create a `config.yml`.

Example configuration:
```yaml
host: imap.example.com
username: user
password: supers3cr3tp4ssw0rd
dump_folder: /path/to/dump/folder
```

All possible settings:
```yaml
host: imap.example.com
port: 993
username: user
password: supers3cr3tp4ssw0rd
database_file: .imapdump-cache.db
encryption_mode: ssl
folder_regex: ^.*$
dump_folder: /path/to/dump/folder

```

Then run the application:
```bash
$ imapdump -l debug --config config.yml --mirror
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
