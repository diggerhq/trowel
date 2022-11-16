class LambdaError(Exception):
    def __init__(self, message):
        self.message = message


class PayloadValidationException(LambdaError):
    pass


class GitHubError(LambdaError):
    pass


class TerraformFormatError(LambdaError):
    pass
