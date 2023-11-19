"""Test targets to execute requested tests."""
from abc import ABC, abstractmethod
import logging
from pathlib import Path
import re
import subprocess
import threading
import typing

import docker

from datatypes import CheckResult, ExecuteResult, TestCase
from utils import is_safe_path

logger = logging.getLogger(__name__)


class TestTarget(ABC):
	"""Base class for test targets"""
	def __init__(self, parameters: typing.Optional[str]):
		self.login = []
		self.set_user = ["sudo", "-u"]
		self.add_user_commad = ['sudo', 'useradd', '-m']
		self.execute_command = ["mkdir"]
		self.test_command = ["ls",  "-ld"]
		self.clean_command = ["rm", "-r"]
		self.parameters = parameters

	@abstractmethod
	def run_command(self, command: typing.List[str]) -> typing.Tuple[bool, str]:
		"""Run command against the target. Command should be checked and sanitized beforehand."""

	@abstractmethod
	def _construct_command(self, user: str, command: typing.List[str]) -> typing.List[str]:
		"""Construct a command so it can run for specific target under specific user."""

	def add_user(self, user: str) -> None:
		"""Add a system user (if doesn't exist)"""
		# Check if the test user exists
		result, _ = self.run_command(['id', user])
		if result:
			logger.debug(f"User '{user}' already exists.")
		else:
			logger.debug(f"User '{user}' does not exist. Creating user...")
			self.run_command(self.add_user_commad + [user])
			logger.debug(f"User '{user}' created.")

	def execute(self, test_case: TestCase, target_path: str) -> ExecuteResult:
		"""Execute test case."""
		if test_case.security_check and not is_safe_path(target_path):
			return ExecuteResult(
				success=False,
				output=f"Path '{target_path}' is not safe or outside of allowed base - check logs for more details"
			)
		exec_command = self._construct_command(
			test_case.user_run, self.execute_command + test_case.flags + [target_path]
		)
		success, output = self.run_command(exec_command)

		return ExecuteResult(success=success, output=output)

	def check(self, test_case: TestCase, target_path: str) -> CheckResult:
		"""Check test case execution results."""
		if target_path == "":
			return CheckResult(
				folder_exists=False,
				output="Empty path is provided - nothing to check!"
			)
		# Don't check if path is not safe
		if not is_safe_path(target_path):
			return CheckResult(
				folder_exists=False,
				output=f"Path '{target_path}' is not safe or outside of allowed base - check logs for more details"
			)
		# Check existance
		check_existance_command = self._construct_command(test_case.user_check, self.test_command + [target_path])
		existance_status, check_existance_info = self.run_command(check_existance_command)

		# Don't check permission if target_path doesn't exist
		if not existance_status:
			return CheckResult(
				folder_exists=existance_status,
				output=check_existance_info
			)

		# Check permissions
		permissions = re.match(r'^([drwx-]+)\s+', check_existance_info).group(1)
		permissions_check_status = permissions == test_case.exp_permissions

		return CheckResult(
			folder_exists=existance_status,
			permissions_check_status=permissions_check_status,
			output=check_existance_info
		)

	def clean(self, base_dir: str, target_path: str) -> None:
		"""Clean up after test execution."""
		# Convert given dirs into Path objects
		base_dir, target_path = base_dir.strip('"'), target_path.strip('"')
		# Find top directory path
		try:
			components = target_path.split("/")
			top_component = None
			for idx, component in enumerate(components):
				if component == base_dir.split("/")[-1]:
					top_component = components[idx + 1]
					break
			if top_component is not None:
				top_directory_path = Path(base_dir) / top_component
		except IndexError:
			top_directory_path = base_dir
		assert is_safe_path(str(top_directory_path))
		# Construct clean command and clear created folder
		clean_command = self.clean_command + [str(top_directory_path)]
		status, exec_info = self.run_command(clean_command)

		if not status:
			logger.warning(f"Error running clean command - {exec_info}")


class LocalHost(TestTarget):
	"""Test target to run on localhost"""
	def run_command(self, command: typing.List[str]) -> typing.Tuple[bool, str]:
		"""Run command against the localhost target."""
		command = " ".join(self.login + command)
		logger.debug(f"Running '{command}' command")
		result = subprocess.run(
			command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			text=True, shell=True, check=False
		)

		return result.returncode == 0, result.stdout + result.stderr

	def _construct_command(self, user: str, command: typing.List[str]) -> typing.List[str]:
		"""Construct a command so it can run for specific target under specific user."""
		return self.set_user + [user] + command

class RemoteHost(LocalHost):
	"""Test target to run on localhost"""
	def __init__(self, parameters: str):
		super().__init__(parameters)
		self.login = ["ssh", f"root@{self.parameters}"]

class DockerHost(TestTarget):
	"""Test target to run on Docker host"""
	def __init__(self, parameters: str):
		super().__init__(parameters)
		self.cmd_prefix = ["-c"]
		self.set_user = ["su", "-"]
		self.add_user_commad = ['useradd', '-m']
		self.client = docker.from_env()
		self.container = self.client.containers.run(self.parameters, command="sleep infinity", detach=True)

	def _construct_command(self, user: str, command: typing.List[str]) -> typing.List[str]:
		"""Construct a command so it can run for specific target under specific user."""
		return self.set_user + [user] + self.cmd_prefix + ["'"] + command + ["'"]

	def run_command(self, command: typing.List[str]) -> typing.Tuple[bool, str]:
		"""Run command against the localhost target."""
		command = " ".join(command)
		logger.debug(f"Running '{command}' command")
		result = self.container.exec_run(command)

		return result.exit_code == 0, result.output.decode("utf-8")

	def remove_container(self):
		"""Stop and remove container"""
		self.container.stop()
		self.container.remove()

	def __del__(self):
		logger.debug("Stopping Docker Host")
		thread = threading.Thread(target=self.remove_container)
		thread.start()
