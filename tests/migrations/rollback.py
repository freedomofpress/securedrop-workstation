from pathlib import Path

from migration_steps import MigrationStep


class ExampleRollback(MigrationStep):
    def __init__(self, step, keep=False):
        self.path = Path(__file__).parent / f"example-rollback-{step}.txt"
        self.keep = keep

    def validate(self):
        # This file should not yet exist
        return not self.path.exists()

    def run(self):
        self.path.open("w").write("roll me back please!")

    def rollback(self, _tmpdir):
        # This file hasn't existed before so it shouldn't exist if we
        if not self.keep:
            self.path.unlink()


class ExampleFail(MigrationStep):
    def run(self):
        raise Exception("Intentionally failing")


steps = [ExampleRollback(1), ExampleRollback(2), ExampleFail(), ExampleRollback(3, True)]
