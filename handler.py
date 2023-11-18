from enum import Enum
import logging
import typing

from datatypes import TestCase
from target import LocalHost, TestTarget
from utils import PathFactory

logger = logging.getLogger(__name__)

class SupportedTargets(Enum):
	LOCALHOST = "LocalHost"

class TestHandler:
	def __init__(self, test_cases: typing.List) -> None:
		self.test_cases: typing.Dict[str, typing.List[TestCase]] = test_cases
		self.path_factory = PathFactory()

	def run(self) -> None:
		"""Run all test cases against all test targets."""
		for target_name in self.test_cases:
			test_target = self.target_factory(target_name)
			for test_case in self.test_cases[target_name]:
				logger.debug(f"Target: {target_name}, Test case: {test_case}")
				run_status, run_exec_info, check_status, check_exec_info = self._run_single(test_target, test_case)
				# Check and report results		
				test_case.test_result = True if test_case.expected_result == all([run_status, check_status]) else False
				if test_case.test_result:
					logger.info(f"[PASS] Test case name: {test_case.name}")
				else:
					logger.info(
						f"[FAIL] Test case name: {test_case.name}, Expected: {test_case.expected_result}"
						f"Run status: {run_status}, ({run_exec_info}) Check status: {check_status} ({check_exec_info})"
			)
	def _run_single(self, test_target: TestTarget, test_case: TestCase) -> typing.Tuple:
		"""Run single test case against single test target."""
		if test_target is not None:
			users = set([test_case.user_run, test_case.user_check])
			# Check if test users were created
			for user in users:
				test_target.add_user(user)
			# Run the test and check results
			target_path = self.path_factory.create_path(test_case)
			run_status, run_exec_info = test_target.execute(target_path, test_case.user_run, test_case.flags)
			check_status, check_exec_info = test_target.check(target_path, test_case.user_check)
			# Clean up
			if test_case.clean_up and check_status:
				test_target.clean(test_case.base_dir, target_path)
		else:
			run_status, check_status = None, None
			run_exec_info, check_exec_info = "Target wasn't created", "Check wasn't executed"
		return run_status, run_exec_info, check_status, check_exec_info

	@staticmethod
	def target_factory(target_type: str) -> typing.Optional[TestTarget]:
		target = None
		try:
			if SupportedTargets[target_type.upper()] == SupportedTargets.LOCALHOST:
				target = LocalHost()
		except KeyError:
			logger.exception("Requested target doesn't exist - {target_type}!")
		
		return target
