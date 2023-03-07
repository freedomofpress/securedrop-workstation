from pathlib import Path

from migration_steps import MigrationStep


class ExampleRollbackSuccess(MigrationStep):
    def __init__(self, step):
        self.path = Path(__file__).parent / f"example-rollback-{step}.txt"

    def run(self):
        pass

    def rollback(self, _tmpdir):
        self.path.write_text("I was rolled back!")


class ExampleRollbackFail(MigrationStep):
    def run(self):
        pass

    def rollback(self, _tmpdir):
        raise Exception("Intentionally failing")


class ExampleFailTriggerFailingRollback(MigrationStep):
    def run(self):
        raise Exception("Intentionally failing")


steps = [
    ExampleRollbackSuccess(1),
    ExampleRollbackFail(),
    ExampleRollbackSuccess(2),
    ExampleFailTriggerFailingRollback(),
    ExampleRollbackSuccess(3),
]
