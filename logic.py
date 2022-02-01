from json_mapper import JSONMapper
from core.models import Account
from journal.models import Journal

def import_journal(journal_json):
    """
    Import a Journal JSON representation
    """

    journal_path = journal_json["path"]
    existing = Journal.object.filter(code=journal_path)

    if existing is None:
        journal = Journal.object.create(
            code=journal_path,
            domain="https://www.example.com/%s" %(journal_path)
        )
