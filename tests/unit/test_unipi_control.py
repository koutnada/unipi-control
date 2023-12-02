"""Unit tests for unipi-control entry point."""

from argparse import Namespace

from unipi_control.unipi_control import UnipiControl


class TestHappyPathUnipiControl:
    def test_parse_args(self) -> None:
        """Test cli arguments for 'unipi-control'."""
        parser = UnipiControl.parse_args(["-vv"])

        assert parser.verbose == 2
        assert isinstance(parser, Namespace)
