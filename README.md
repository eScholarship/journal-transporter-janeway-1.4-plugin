# Journal Transporter - Plugin for Janeway 1.4

A plugin for the [Janeway](https://github.com/BirkbeckCTP/janeway) publishing platform that handles imports (and eventually maybe exports) from [Journal Transporter](https://github.com/castiron/journal-transporter).

## Installation

Clone this repository into `{JANEWAY_ROOT}/src/plugins` on your Janeway server and rename the resulting directory to `journal_transporter`.

In the Janeway Django admin interface, go to Utils -> Plugins and click "Add Plugin". Name it `journal_transporter`, assign the current version number, and ensure that the "Enabled" and "Press wide" checkboxes are selected.

Restart your Janeway server.

## Usage

This plugin adds API routes needed to interface with Journal Transporter.

### Setting up the server in Journal Transporter

See the [Journal Transporter](https://github.com/castiron/journal-transporter) documentation for instructions on connecting Journal Transporter to your Janeway instance. If you followed the installation instructions above, the server host will be:

```http
{JANEWAY_URL}/plugins/journal-transporter/
```

Adjust as needed, if you provided the plugin a different name.

### Viewing API data

You can also access the endpoints directly in a browser or REST client. In a browser, you must be logged into Janeway. In a REST client, provide credentials as basic auth.

### Tests

There is a*very* small group of tests written as standard django test cases. The following command will run the tests assuming you've installed the plugin in a directory called "journal_transporter".

```
manage.py test journal_transporter
```

## License

This Janeway plugin is available under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE (Version 3, 19 November 2007).

[See the LICENCE file for full details.](https://github.com/castiron/journal-transporter-janeway-1.4-plugin/blob/main/LICENSE)

## Contributing

Contributions to improve this plugin are welcome. [Please see the contributing.md file for guidelines.](https://github.com/castiron/journal-transporter-janeway-1.4-plugin/blob/main/contributing.md)
