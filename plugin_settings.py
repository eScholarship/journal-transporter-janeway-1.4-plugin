from utils import plugins
from utils.install import update_settings

PLUGIN_NAME = "Journal Transporter for Janeway 1.4"
DESCRIPTION = "A plugin to handle importing JSON journal data"
AUTHOR = "Tim Frazee"
VERSION = "0.1"
SHORT_NAME = "cdl_janeway_plugin"
MANAGER_URL = "transporter_manager"

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
        file_path="plugins/cdl_janeway_plugin/install/settings.json"
    )

def hook_registry():
    """
    When site with hooks loaded, this is run for each plugin to create list of plugins
    """
    return {}
