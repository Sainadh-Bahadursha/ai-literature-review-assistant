class ApplicationException(Exception):
    """Base exception for the application."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ConfigurationException(ApplicationException):
    """Raised when application configuration is invalid."""

    pass


class PaperProcessingException(ApplicationException):
    """Raised when a research paper cannot be processed."""

    pass


class DuplicatePaperException(ApplicationException):
    """Raised when a duplicate research paper is uploaded."""

    pass