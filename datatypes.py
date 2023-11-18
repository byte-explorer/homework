from dataclasses import dataclass, field
import typing

@dataclass
class TestCase:
	# Test case name
	name : str
	# User to run a test for
	user_run: str
	# User to check the
	user_check: str
	# Path depth
	depth: int
	# Expected run / check result
	expected_result: bool
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
	# Flag to store test result
	test_result: typing.Optional[bool] = None
