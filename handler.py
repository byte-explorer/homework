"""Test Handler to execute tests and store results."""
from enum import Enum
import logging
import threading
import typing

from datatypes import CheckResult, ExecuteResult, TargetSpecs, TestCase, TestCaseResult
from target import DockerHost, LocalHost, RemoteHost, TestTarget
from utils import PathFactory

logger = logging.getLogger(__name__)

class SupportedTargets(Enum):
	"""Supperted Test Targets"""
	LOCALHOST = LocalHost
	DOCKERHOST = DockerHost
	REMOTEHOST = RemoteHost


class TestHandler:
	"""Test Handler to execute tests and store results."""
	def __init__(self, test_cases: typing.List) -> None:
		self.test_cases: typing.Dict[str, typing.List[TestCase]] = test_cases
		self.path_factory = PathFactory()
		self.successful_run = True

	def run(self) -> None:
		"""Run all test cases against all test targets in parallel using threading."""
		threads = []

		def run_test(target_name: str, test_cases: typing.List[TestCase]) -> None:
			"""Helper method to run test in a thread"""
			test_target = self.target_factory(target_name)
			for test_case in test_cases:
				logger.debug(f"Target: {test_target}, Test case: {test_case}")
				execute_result, check_result = self._run_single(test_target, test_case)
				logger.debug(f"Exec: {execute_result}, Check: {check_result}")
				# Check results against test case spec
				test_case.test_result = self._check_results(test_case, execute_result, check_result)
				# Log results
				if test_case.test_result:
					logger.info(f"[PASS] Target: {target_name}, Test case name: {test_case.name}")
				else:
					logger.info(
						f"[FAIL] Target: {target_name}, Test case name: {test_case.name}, "
						f"Test case spec: {test_case}, Exec status: {execute_result}, Check status: {check_result}"
					)
					self.successful_run = False

		# Create a thread for every test target
		for target_name in self.test_cases:
			thread = threading.Thread(target=run_test, args=(target_name, self.test_cases[target_name]))
			threads.append(thread)
			thread.start()

		# Wait for all threads to complete
		for thread in threads:
			thread.join()

	def _run_single(self, test_target: TestTarget, test_case: TestCase) -> typing.Tuple[ExecuteResult, CheckResult]:
		"""Run single test case against single test target."""
		if test_target is not None:
			users = set([test_case.user_run, test_case.user_check])
			# Check if test users were created
			for user in users:
				test_target.add_user(user)
			# Run the test and check results
			target_path = self.path_factory.create_path(test_case)
			execute_result = test_target.execute(test_case, target_path)
			check_result = test_target.check(test_case, target_path)
			# Clean up
			if test_case.clean_up and check_result.folder_exists:
				test_target.clean(test_case.base_dir, target_path)
		else:
			execute_result = ExecuteResult(output="Target wasn't created")
			check_result = CheckResult(output="Check wasn't executed")
		return execute_result, check_result

	def report(self) -> None:
		"""Report test results and statistics."""
		failing_cases = []
		num_successful_test_cases = 0
		num_total_test_cases = 0
		for target_name in self.test_cases:
			for test_case in self.test_cases[target_name]:
				if test_case.test_result:
					num_successful_test_cases += 1
				else:
					failing_cases.append(f"[{target_name} - {test_case.name}]")
				num_total_test_cases += 1

		stats = f"{num_successful_test_cases}/{num_total_test_cases}"
		tested_hosts = ", ".join(self.test_cases.keys())

		if self.successful_run:
			logger.info(f"/** TEST PASSED: {stats} succeful test cases. Tested hosts: {tested_hosts} **/")
		else:
			logger.info(
				f"/** TEST FAILED: {stats} succeful test cases. Tested hosts: {tested_hosts}, "
				f"Failed cases: {', '.join(failing_cases)} **/")

	@staticmethod
	def _check_results(
			test_case: TestCase, execute_result: ExecuteResult, check_result: CheckResult
		) -> TestCaseResult:
		"""Check given results against test case spec"""
		return TestCaseResult(
			# Check if mkdir run didn't have errors (if expected)
			test_case.exp_run_no_error == execute_result.success,
			# Check if output dir exists (if expected)
			test_case.exp_existance == check_result.folder_exists,
			# Check expected output
			True if test_case.exp_run_output is None else \
				execute_result.output.strip() in test_case.exp_run_output.strip(),
			# Check expected dir permissions
			True if test_case.exp_permissions is None else check_result.permissions_check_status
		)

	@staticmethod
	def target_factory(target_type: str) -> typing.Optional[TestTarget]:
		"""Factory to create a test target based on given type."""
		target = None
		try:
			parsed_type = TargetSpecs(*target_type.split("_"))
			target = SupportedTargets[parsed_type.host.upper()].value(parsed_type.parameters)
		except KeyError:
			logger.exception("Requested target doesn't exist - {target_type}!")

		return target
