from pathlib import Path

from migration_steps import MigrationStep


class ExampleCleanup(MigrationStep):
    def __init__(self):
        self.path = Path(__file__).parent / "example-cleanup-file.txt"

    def validate(self):
        return not self.path.exists()

    def run(self):
        self.path.open("w").write("Clean me up!")

    def cleanup(self, _tmpdir):
        self.path.open("w").write("This is clean, trust me")


steps = [ExampleCleanup()]
