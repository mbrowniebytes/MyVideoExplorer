import pytest
from MyVideoExplorer.utils.file_util_model import FileUtilModel


def pytest_addoption(parser) -> None:
    """Add custom command-line options."""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="Run slow tests"
    )


@pytest.fixture
def mock_folder_items():
    return [
        FileUtilModel(
            type="dir", name="Folder A", full_path="/path/to/Folder A", depth=0
        ),
        FileUtilModel(
            type="dir", name="Folder B", full_path="/path/to/Folder B", depth=0
        ),
        FileUtilModel(
            type="file", name="File C.txt", full_path="/path/to/File C.txt", depth=0
        ),
    ]


@pytest.fixture
def mock_nested_folder_items():
    return [
        FileUtilModel(type="dir", name="Root", full_path="/path/to/Root", depth=0),
        FileUtilModel(
            type="dir", name="Subfolder", full_path="/path/to/Root/Subfolder", depth=1
        ),
    ]


@pytest.fixture
def mock_file_items():
    return [
        FileUtilModel(
            type="file", name="video1.mp4", full_path="/path/to/video1.mp4", depth=0
        ),
        FileUtilModel(
            type="file", name="video2.mkv", full_path="/path/to/video2.mkv", depth=0
        ),
        FileUtilModel(
            type="file", name="readme.txt", full_path="/path/to/readme.txt", depth=0
        ),
    ]
