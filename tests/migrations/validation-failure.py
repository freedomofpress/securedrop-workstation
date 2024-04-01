from migration_steps import MigrationStep


class ExampleValidationFail(MigrationStep):
    def validate(self):
        raise Exception("Intentionally failing")

    def run(self):
        pass


steps = [ExampleValidationFail()]
