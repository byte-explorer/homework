from dataclasses import dataclass, field, fields
import typing

@dataclass
class TestCaseResult:
	exp_run_no_eror: bool
	exp_existance: bool
	exp_run_output: bool
	exp_permissions: bool

	def __bool__(self):
		return all(getattr(self, field.name) for field in fields(self))

@dataclass
class TestCase:
	"""Mandatory test specs block"""
	# Test case name
	name : str
	# User to run a test for
	user_run: str
	# User to check the
	user_check: str
	# Path depth
	depth: int

	"""Optional test specs block"""
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

	"""Expected Results block"""
	# Expected run no error
	exp_run_no_error: bool = True
	# Expected folder existance
	exp_existance: bool = True
	# Expected permissions
	exp_permissions: typing.Optional[str] = None
	# Expected run output
	exp_run_output: typing.Optional[str] = None

	# Flag to store test result
	test_result: typing.Optional[TestCaseResult] = None

@dataclass
class ExecuteResult:
	success: typing.Optional[bool] = None
	output: typing.Optional[str] = None

@dataclass
class CheckResult:
	folder_exists: typing.Optional[bool] = None
	permissions_check_status: typing.Optional[bool] = None
	exp_permissions: typing.Optional[str] = None
	output: typing.Optional[str] = None
