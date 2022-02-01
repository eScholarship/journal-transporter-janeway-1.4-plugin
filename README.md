# CDL Journal Portability - Janeway Plugin

A plugin for the [Janeway](https://github.com/BirkbeckCTP/janeway) journal platform that handles imports (and eventually maybe exports) from the [CDL Journal Transfer Application](https://github.com/castiron/cdl-journal-transfer).

## Installation

Clone this repository into `${JANEWAY_ROOT}/plugins` on your Janeway server.

## Usage

This plugin adds interfaces for JSON data to be ingested into Janeway models. They can be invoked directly from the Django shell `python manage.py shell`, i.e.

```python
from cdl_journal_transfer_janeway.interfaces.journal_handler import JournalHandler

data = {...}

handler = JournalHandler()
handler.import_single(data)
```

...or the data can be provided from the shell by utilizing the `import_journal` Django CLI command. Using this command requires that the JSON to import has been written to a file accessible from the Janeway instance and as the logged in user.

```shell
touch tmp/example.json
echo '{"path": "example", "title": "Example Journal"}' >> tmp/example.json

python $JANEWAY_ROOT/src/manage.py import_journal tmp/example.json
```

Generally, this should be handled by the CDL Journal Transfer Application.
