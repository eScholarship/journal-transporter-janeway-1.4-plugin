# Journal Transporter - Plugin for Janeway 1.4

A plugin for the [Janeway](https://github.com/BirkbeckCTP/janeway) journal platform that handles imports (and eventually maybe exports) from the [Journal Transporter Application](https://github.com/castiron/journal-transporter).

## Installation

Clone this repository into `{JANEWAY_ROOT}/plugins` on your Janeway server and rename the resulting directory to `journal_transporter`.

## Usage

This plugin adds API routes needed to interface with Journal Transporter. For validation, these routes can be accessed at

```http
{JANEWAY_URL}/plugins/journal-transporter/
```

if you'd like to review the import and export formats manually.

Otherwise, these endpoints are used primarily by Journal Transporter.

## LICENSE

TODO

## Contributing

TODO
