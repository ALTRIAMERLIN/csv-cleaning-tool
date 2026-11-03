import csvclean
from csvclean import core
from csvclean.cli import build_parser


def test_package_imports():
    assert csvclean.__version__ == "0.1.0"
    assert issubclass(core.EmptyFileError, core.CsvCleanError)


def test_cli_parser():
    args = build_parser().parse_args(["in.csv", "--out", "o", "--keep", "last"])
    assert args.keep == "last"
