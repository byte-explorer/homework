from abc import ABC, abstractmethod
import logging
from pathlib import Path
import re
import subprocess
import typing

from datatypes import CheckResult, ExecuteResult, TestCase
from utils import is_safe_path

logger = logging.getLogger(__name__)

class TestTarget(ABC):
	"""Base class for test targets"""
	def __init__(self):
		self.set_user = ["sudo", "-u"]
		self.execute_command = ["mkdir"]
		self.test_command = ["ls",  "-ld"]
		self.clean_command = ["rm", "-r"]
 
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
	def execute(self, target_path: str, user: str, test_case: TestCase) -> ExecuteResult:
		pass

	@abstractmethod
	def check(self, target_path: str, user: str, exp_permissions: str) -> CheckResult:
		pass

	@abstractmethod
	def clean(self, base_dir: str, target_path: str) -> None:
		pass

class LocalHost(TestTarget):
	"""Test target to run on localhost"""
	def __init__(self):
		self.cmd_prefix = []
		super().__init__()

	def run_command(self, command: typing.List[str]) -> typing.Tuple[bool, str]:
		"""Run command against the localhost target."""
		logger.debug(f"Running '{command}' command")
		result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

		return result.returncode == 0, result.stdout + result.stderr

	def execute(self, target_path: str, user: str, flags: typing.List[str]) -> ExecuteResult:
		if not is_safe_path(target_path):
			return ExecuteResult(
				success=False,
				output="Path '{target_path}' is not safe or outside of allowed base - check logs for more details"
			)
		exec_command = self.cmd_prefix + self.set_user + [user] + self.execute_command + flags + [target_path]		
		success, output = self.run_command(exec_command)

		return ExecuteResult(success=success, output=output)

	def check(self, target_path: str, user: str, exp_permissions: str) -> CheckResult:
		# Don't check if path is not safe
		if not is_safe_path(target_path):
			return CheckResult(
				output="Path '{target_path}' is not safe or outside of allowed base - check logs for more details"
			)
		# Check existance
		check_existance_command = self.cmd_prefix + self.set_user + [user] + self.test_command + [target_path]
		existance_status, check_existance_info = self.run_command(check_existance_command)

		# Don't check permission if target_path doesn't exist
		if not existance_status:
			return CheckResult(
				folder_exists=existance_status,
				exp_permissions=exp_permissions,
				output=check_existance_info
			)
		
		# Check permissions
		permissions = re.match(r'^([drwx-]+)\s+', check_existance_info).group(1)
		permissions_check_status = permissions == exp_permissions

		return CheckResult(
			folder_exists=existance_status,
			permissions_check_status=permissions_check_status,
			exp_permissions=exp_permissions,
			output=check_existance_info
		)

	def clean(self, base_dir: str, target_path: str) -> None:
		# Convert given dirs into Path objects
		base_dir, target_path = Path(base_dir), Path(target_path)
		# Find top directory path
		top_directory_path = base_dir / target_path.relative_to(base_dir).parts[0]
		# Construct clean command and clear created folder
		clean_command = self.cmd_prefix + self.set_user + ["root"] + self.clean_command + [str(top_directory_path)]
		status, exec_info = self.run_command(clean_command)

		if not status:
			logger.warning(f"Error running clean command - {exec_info}")
