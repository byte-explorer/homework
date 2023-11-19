"""Testing framework utils."""
import logging
import random
import string
from pathlib import Path, PurePath

from datatypes import TestCase

logger = logging.getLogger(__name__)

def is_injection_safe(test_string: str) -> bool:
	"""Check if string has injection symbols."""
	injection_risks = [
		";", "&", "|", "`", "$(", ")", ">", "<", ">>", 
		"2>", "\\n", "\\r", "*", "?", "||", "&&"
	]
	return not any(risk in test_string for risk in injection_risks)

def is_safe_path(path: str):
	"""Check if the path is safe to use in a command. Only paths inside /tmp are allowed."""
	# Check for command injection patterns
	if not is_injection_safe(path):
		logger.warning(f"Provided path is not injection safe: {path}")
		return False

	# Remove the first and last characters
	if path.startswith('"') and path.endswith('"'):
		path = path[1:-1]

	path = PurePath(path)

	# Check for relative path traversal
	if ".." in path.parts:
		logger.warning(f"Path traversal: {path}")
		return False

	# Check if path is absolute
	if not path.is_absolute():
		logger.warning(f"Provided path is not absolute: {path} {path.is_absolute()}")
		return False

	# Check that path is not exactly /tmp
	if path in [Path("/tmp")]:
		logger.warning(f"Provided path cannot be exactly /tmp: {path}")
		return False

	# Allowed base directories (subdirectories within /tmp)
	allowed_bases = [Path("/tmp")]

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
			folder_name = self.generate_folder_name(test_case)
			path /= folder_name

		path = str(path)
		if test_case.add_quotes:
			path = f'"{path}"'

		logger.debug(f"PathFactory: generated: {path}")

		return path

	@staticmethod
	def generate_folder_name(test_case: TestCase) -> str:
		"""Generate a folder name"""
		if test_case.valid_folder_name:
			chars = string.ascii_letters + string.digits + (" " if test_case.allow_spaces else "") + "_"
		else:
			chars = string.ascii_letters + string.digits + "!@#^"
		folder_name = "".join(random.choice(chars) for _ in range(test_case.folder_name_length)).strip()
		# pylint: disable=anomalous-backslash-in-string
		folder_name = folder_name.replace(" ", "\ ") # Add \ to whitespaces so they won't be considered as a new path

		return folder_name
