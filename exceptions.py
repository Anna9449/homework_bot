class EmptyResponseFromAPIError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'EmptyResponseFromAPIError, {0}'.format(self.message)
        return 'EmptyResponseFromAPIError: Empty response from API'


class InvalidResponseCodeError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'InvalidResponseCodeError, {0}'.format(self.message)
        return 'InvalidResponseCodeError: Invalid response code'
