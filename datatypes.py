from dataclasses import dataclass, field, fields
import typing


@dataclass
class TestCaseResult:
	"""Dataclass to store test case results"""
	# Check if command run has no error
	exp_run_no_eror: bool
	# Check if directory was created
	exp_existance: bool
	# Check for specific program output
	exp_run_output: bool
	# Check for created directory permissions
	exp_permissions: bool

	def __bool__(self):
		return all(getattr(self, field.name) for field in fields(self))


@dataclass
class TestCase:
	"""Dataclass to store Test Case specification."""

	# Block: Mandatory Test Specs
	# Test case name
	name : str

	# Block: Optional Test Specs
	# User to run a test for
	user_run: str = "testuser"
	# User to check the
	user_check: str = "testuser"
	# Path depth
	depth: int = 1
	# Base directory
	base_dir: str = "/tmp"
	# Length of individual folder names
	folder_name_length: int = 10
	# Allow whitespaces in a folder name
	allow_spaces: bool = False
	# Flag whether a valid folder name to be generated
	valid_folder_name : bool = True
	# Flag whether created folder should be deleted after test
	clean_up: bool = True
	# Additional flags
	flags: typing.List[str] = field(default_factory=list)

	# Block: Expected Results
	# Expected run no error
	exp_run_no_error: bool = True
	# Expected folder existance
	exp_existance: bool = True
	# Expected permissions
	exp_permissions: typing.Optional[str] = None
	# Expected run output
	exp_run_output: typing.Optional[str] = None

	# Field to store test result
	test_result: typing.Optional[TestCaseResult] = None


@dataclass
class ExecuteResult:
	"""Dataclass to store execution result."""
	# Check if execution was successful
	success: typing.Optional[bool] = None
	# Field to store execution output (stdout, stderr)
	output: typing.Optional[str] = None


@dataclass
class CheckResult:
	"""Dataclass to store check result."""
	# Check if requested folder exists
	folder_exists: typing.Optional[bool] = None
	# Check if permissions are set correctly
	permissions_check_status: typing.Optional[bool] = None
	# Field to store check output (stdout, stderr)
	output: typing.Optional[str] = None
