class Repo2DockerError(Exception):
    """Failed to execute repo2docker"""

    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

class DockerError(Exception):
    """Failed to execute repo2docker"""

    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
