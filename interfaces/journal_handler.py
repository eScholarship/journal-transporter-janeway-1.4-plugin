from journal.models import Journal

class JournalHandler:

    def import_single(self, data):
        """
        Import a Journal JSON representation into Janeway as a new Journal
        """

        journal_path = data["path"]
        exists = Journal.objects.filter(code=journal_path).exists()

        if not exists:
            journal = Journal.objects.create(
                code=journal_path,
                domain="https://www.example.com/%s" %(journal_path)
            )

            journal.name = data["title"]
            journal.save()
