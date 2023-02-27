from migration_steps import MigrationStep

# If this filename is not 0.0.1.py, then fail already during validation
FAIL_AT_VALIDATE = False if "0.0.1.py" in __file__ else True


class ExampleFail(MigrationStep):
    def __init__(self, fail_at_validate=False):
        self.fail_at_validate = fail_at_validate

    def validate(self):
        if self.fail_at_validate:
            raise Exception("Intentionally failing")
        return True

    def run(self):
        raise Exception("Intentionally failing")


steps = [ExampleFail(FAIL_AT_VALIDATE)]
