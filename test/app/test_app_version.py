from __future__ import annotations

from unittest.mock import patch

from MyVideoExplorer.app import app_version


class TestAppVersion:
    """Verify that the version module reads and exposes the package version correctly."""

    def test_version_should_not_be_empty(self) -> None:
        assert app_version.__version__
        assert app_version.__version__ != ""

    def test_version_should_not_be_dev_when_installed(self) -> None:
        # Since the package is installed in editable mode, version should resolve
        assert app_version.__version__ != "dev"

    def test_metadata_should_contain_version(self) -> None:
        metadata = app_version.get_app_metadata()
        assert "app_version" in metadata
        assert metadata["app_version"] == app_version.__version__

    def test_fallback_to_dev_when_package_not_found(self) -> None:
        # Simulate PackageNotFoundError to verify fallback behavior
        with patch(
            "MyVideoExplorer.app.app_version.version",
            side_effect=Exception("Package not found"),
        ):
            # Re-read the version to trigger the fallback
            fallback_version = app_version._read_version()
            assert fallback_version == "dev"

    def test_display_format_should_convert_calver_to_github_format(self) -> None:
        # CalVer with leading zeros should convert correctly
        result = app_version.format_version_for_display("2026.11.16.008")
        assert result == "20261116-008"

    def test_display_format_should_handle_short_build_number(self) -> None:
        # Short build number should be zero-padded
        result = app_version.format_version_for_display("2026.11.16.1")
        assert result == "20261116-001"

    def test_display_format_should_return_dev_unchanged(self) -> None:
        # Development version should pass through unchanged
        result = app_version.format_version_for_display("dev")
        assert result == "dev"

    def test_display_format_should_return_empty_unchanged(self) -> None:
        # Empty string should pass through unchanged
        result = app_version.format_version_for_display("")
        assert result == ""

    def test_display_format_should_return_unknown_format_unchanged(self) -> None:
        # Non-CalVer format should pass through unchanged
        result = app_version.format_version_for_display("1.0.0")
        assert result == "1.0.0"
