import argparse
from collections import defaultdict
import json
import logging
import typing

from datatypes import TestCase
from handler import TestHandler

logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Test script - mkdir")

	# Add the arguments
	parser.add_argument("config_file", help="Path to the test configuration file", type=str)
	parser.add_argument("--debug", help="Enable debug logging", action="store_true")
	
	return parser.parse_args()

def parse_test_config(config_path: str) -> typing.Dict:
	"""Parse test configuration from provided config file."""
	test_cases = defaultdict(list)
	# Parse given test config
	with open(config_path, 'r') as file:
		config = json.load(file)
	# Parse test suites for all targets and create test_cases
	for test_target in config:
		for test_suite in test_target["test_suites"]:
			with open(test_suite, 'r') as file:
				test_cases_config = json.load(file)
			for test_case in test_cases_config:
				test_cases[test_target["target"]].append(TestCase(**test_case))

	return test_cases
	
def main() -> None:
	args = parse_arguments()
	# Enable logging
	log_level = logging.DEBUG if args.debug else logging.INFO
	logging.basicConfig(level=log_level, format='%(message)s')
	# Parse test config
	test_cases = parse_test_config(args.config_file)
	logger.debug(f"Parsed config: {test_cases}")

	test_handler = TestHandler(test_cases=test_cases)
	test_handler.run()


if __name__ == "__main__":
	main()