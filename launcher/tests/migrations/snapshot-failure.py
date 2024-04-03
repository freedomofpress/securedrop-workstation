from pathlib import Path

from migration_steps import MigrationStep, path_snapshot


class ExampleSnapshot(MigrationStep):
    def __init__(self):
        self.path = Path(__file__).parent / "example-snapshot-file.txt"
        self.path.write_text("Snapshot me!")

    def snapshot(self, tmpdir):
        path_snapshot(self.path, tmpdir)

    def run(self):
        pass


class ExampleSnapshotFail(MigrationStep):
    def snapshot(self, _tmpdir):
        raise Exception("Intentionally failing")

    def run(self):
        pass


steps = [ExampleSnapshot(), ExampleSnapshotFail()]
