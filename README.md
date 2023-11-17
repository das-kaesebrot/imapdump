# imapdump

## About
imapdump is a cli based tool to export imap accounts to a local folder.

## Configuration
Edit the default `config.yml`.

Example configuration:
```yaml
servers:
  # A unique key for your imap server config.
  myhost:
    host: imap.example.com
    username: user
    password: supers3cr3tp4ssw0rd
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
