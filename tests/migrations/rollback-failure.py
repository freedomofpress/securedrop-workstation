from pathlib import Path

from migration_steps import MigrationStep


class ExampleRollback(MigrationStep):
    def __init__(self, step):
        self.path = Path(__file__).parent / f"example-rollback-{step}.txt"

    def run(self):
        pass

    def rollback(self, _tmpdir):
        self.path.open("w").write("I was rolled back!")


class ExampleRollbackFail(MigrationStep):
    def run(self):
        pass

    def rollback(self, _tmpdir):
        raise Exception("Intentionally failing")


class ExampleFail(MigrationStep):
    def run(self):
        raise Exception("Intentionally failing")


steps = [
    ExampleRollback(1),
    ExampleRollbackFail(),
    ExampleRollback(2),
    ExampleFail(),
    ExampleRollback(3),
]
