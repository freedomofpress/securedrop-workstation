from migration_steps import MigrationStep


class ExampleFail(MigrationStep):
    def run(self):
        raise Exception("Intentionally failing")


steps = [ExampleFail()]
