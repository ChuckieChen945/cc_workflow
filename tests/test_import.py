"""Test cc_workflow."""

import cc_workflow


def test_import() -> None:
    """Test that the package can be imported."""
    assert isinstance(cc_workflow.__name__, str)
