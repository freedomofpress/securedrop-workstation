from pathlib import Path

from migration_steps import MigrationStep


class ExampleCleanupFailure(MigrationStep):
    def __init__(self):
        self.path = Path(__file__).parent / "example-cleanup-file.txt"

    def validate(self):
        return not self.path.exists()

    def run(self):
        self.path.write_text("Clean me up!")

    def cleanup(self, _tmpdir):
        raise Exception("Intentionally failing")


steps = [ExampleCleanupFailure()]
