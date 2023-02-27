"""
success-if-valid test migration

This a reusable, multi-use migration. By default it will be copied to 0.0.1.py by the fixture, but
in addition can also be copied to 0.0.2.py, 0.0.3.py, 0.0.4.py and so on and will still work.

However, if the sequence is broken up, as in 0.0.[1-24].py, this test will fail validation.
"""

from pathlib import Path

from migration_steps import MigrationStep, path_validate

PATCH_VERSION = int(__file__[:-3].rsplit(".", 1)[1])


class ExampleFile(MigrationStep):
    def __init__(self, check_exists):
        self.check_exists = check_exists
        # During execution, this will be written to the temporary directory set up by the test
        self.path = Path(__file__).parent / "example-file.txt"
        self.patch = PATCH_VERSION

    def validate(self):
        if path_validate(self.path, self.check_exists):
            if PATCH_VERSION > 1:
                # Ensure that we're attempting to increment the example migration by one
                return int(self.path.open().read()[-1]) == (PATCH_VERSION - 1)
            return True
        return False

    def run(self):
        self.path.open("w").write(f"0.0.{self.patch}")


steps = [ExampleFile(PATCH_VERSION != 1)]
