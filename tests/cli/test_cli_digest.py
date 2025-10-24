import os
import shutil

import pandas as pd
from click.testing import CliRunner

from tlparser.cli import cli

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
WORKING_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "tmp"))


def test_digest_command():
    runner = CliRunner()

    test_json = os.path.join(TEST_DATA_DIR, "test.json")
    os.makedirs(WORKING_DIR, exist_ok=True)

    files_before = set(os.listdir(WORKING_DIR))
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["digest", test_json, "--output", WORKING_DIR])
        assert result.exit_code == 0

    files_after = set(os.listdir(WORKING_DIR))
    new_files = files_after - files_before
    assert len(new_files) == 1, "Expected exactly one new file, but found: {}".format(
        new_files
    )

    new_file_path = os.path.join(WORKING_DIR, new_files.pop())
    assert os.path.isfile(new_file_path), f"Output file {new_file_path} does not exist."

    df = pd.read_excel(new_file_path)
    assert not df.empty, "The output file is empty."


def teardown_module():
    if os.path.isdir(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)
