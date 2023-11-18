from abc import ABC, abstractmethod
import logging
from pathlib import Path
import subprocess
import typing

from datatypes import TestCase
from utils import is_safe_path

logger = logging.getLogger(__name__)

class TestTarget(ABC):
	"""Base class for test targets"""
	def __init__(self):
		self.execute_command = ["mkdir"]
		self.test_command = ["test", "-d"]
		self.clean_command = ["rm", "-r"]
		self.cmd_prefix = ["sudo", "-u"]
 
	def add_user(self, user: str) -> None:
		# Check if the test user exists
		result = self.run_command(['id', user])
		if result:
			logger.debug(f"User '{user}' already exists.")
		else:
			logger.debug(f"User '{user}' does not exist. Creating user...")
			self.run_command(['sudo', 'useradd', '-m', user])
			logger.debug(f"User '{user}' created.")

	@abstractmethod
	def run_command(self, command: typing.List[str]) -> typing.Tuple[bool, str]:
		"""Run command against the target. Command should be checked and sanitized beforehand."""
		pass

	@abstractmethod
	def execute(self, target_path: str, user: str, test_case: TestCase) -> typing.Tuple[bool, str]:
		pass

	@abstractmethod
	def check(self, target_path: str, user: str) -> typing.Tuple[bool, str]:
		pass

	@abstractmethod
	def clean(self, base_dir: str, target_path: str) -> None:
		pass

class LocalHost(TestTarget):
	"""Test target to run on localhost"""
	def __init__(self):
		super().__init__()

	def run_command(self, command: typing.List[str]) -> typing.Tuple[bool, str]:
		"""Run command against the localhost target."""
		logger.debug(f"Running '{command}' command")
		result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

		return result.returncode == 0, f"stdout: {result.stdout}, stderr: {result.stderr}"

	def execute(self, target_path: str, user: str, flags: typing.List[str]) -> typing.Tuple[bool, str]:
		if not is_safe_path(target_path):
			return False, "Path '{target_path}' is not safe or outside of allowed base - check logs for more details"
		exec_command = self.cmd_prefix + [user] + self.execute_command + flags + [target_path]
		
		return self.run_command(exec_command)

	def check(self, target_path: str, user: str) -> typing.Tuple[bool, str]:
		if not is_safe_path(target_path):
			return False, "Path '{target_path}' is not safe or outside of allowed base - check logs for more details"
		check_command = self.cmd_prefix + [user] + self.test_command + [target_path]

		return self.run_command(check_command)

	def clean(self, base_dir: str, target_path: str) -> None:
		# Convert given dirs into Path objects
		base_dir, target_path = Path(base_dir), Path(target_path)
		# Find top directory path
		top_directory_path = base_dir / target_path.relative_to(base_dir).parts[0]
		# Construct clean command and clear created folder
		clean_command = self.clean_command + [top_directory_path]
		status, exec_info = self.run_command(clean_command)

		if not status:
			logger.warning(f"Error running clean command - {exec_info}")

	