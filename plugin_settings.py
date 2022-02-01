from utils import plugins
from utils.install import update_settings

PLUGIN_NAME = "JSON Importer for Janeway X.X.X"
DESCRIPTION = "A plugin to handle importing JSON journal data"
AUTHOR = "Tim Frazee"
VERSION = "0.1"
SHORT_NAME = "json_importer"
MANAGER_URL = "json_importer"

class CDLJournalTransferJaneway(plugins.Plugin):
    plugin_name = PLUGIN_NAME
    display_name = PLUGIN_NAME
    description = DESCRIPTION
    author = AUTHOR
    short_name = SHORT_NAME

    manager_url = MANAGER_URL

    version = VERSION
    janeway_version = "1.4.0"

    is_workflow_plugin = False

def install():
    CDLJournalTransferJaneway.install()
    update_settings(
        file_path="plugins/cdl_journal_transfer_janeway/install/settings.json"
    )

def hook_registry():
    """
    When site with hooks loaded, this is run for each plugin to create list of plugins
    """
    return {}
