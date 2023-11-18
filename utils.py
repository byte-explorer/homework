import logging
import random
import string
from pathlib import Path

from datatypes import TestCase

logger = logging.getLogger(__name__)

def is_injection_safe(test_string: str) -> bool:
    """Check if string has injection symbols."""
    injection_risks = [
        ';', '&', '|', '`', '$(', ')', '>', '<', '>>', 
        '2>', '\\n', '\\r', '*', '?', '||', '&&'
    ]
    return not any(risk in test_string for risk in injection_risks)

def is_safe_path(path: str):
    """Check if the path is safe to use in a command. Only paths inside /tmp are allowed."""
    path = Path(path)
    # Check for command injection patterns
    if not is_injection_safe(str(path)):
        logger.warning(f"Provided path is not injection safe: {path}")
        return False

    # Check for relative path traversal
    if ".." in path.parts:
        logger.warning(f"Path traversal: {path}")
        return False
    
    path = path.resolve()  # Resolve to absolute path

    # Check that path is not exactly /tmp
    if path in [Path('/tmp')]:
        logger.warning(f"Provided path cannot be exactly /tmp: {path}")
        return False

    # Allowed base directories (subdirectories within /tmp)
    allowed_bases = [Path('/tmp')]

    # Check if path is a subdirectory of any of the allowed base directories
    if not any(str(path).startswith(str(base.resolve())) for base in allowed_bases):
        logger.warning(f"Provided path is outside of allowed bases! Path: {path}, allowed bases: {allowed_bases}")
        return False

    return True


class PathFactory:
    """Path factory to generate random path based on TestCase requirements."""
    def create_path(self, test_case: TestCase) -> str:
        """Create a random path based on TestCase"""
        path = Path(test_case.base_dir)
        for _ in range(test_case.depth):
            folder_name = self.generate_folder_name(
                test_case.folder_name_length, test_case.allow_spaces, test_case.valid_folder_name
            )
            path /= folder_name

        return str(path)

    @staticmethod
    def generate_folder_name(folder_name_length: int, allow_spaces: bool, valid_name: bool) -> str:
        """Generate a folder name"""
        if valid_name:
            chars = string.ascii_letters + string.digits + (' ' if allow_spaces else '') + '_'
        else:
            chars = string.printable if allow_spaces else string.ascii_letters + string.digits

        return ''.join(random.choice(chars) for _ in range(folder_name_length)).strip()
