"""Test of app when used through CLI interface."""
from typer.testing import CliRunner

from genuml.genuml import app

runner = CliRunner()

EXAMPLE_ENUM_PLANTUML = """enum ExampleEnum {
  test.data
  --
  + LOW: ExampleEnum
  + MEDIUM: ExampleEnum
  + HIGH: ExampleEnum
  --
  + values(): ExampleEnum[]
  + valueOf(String): ExampleEnum
  - ExampleEnum():
}
"""

EXAMPLE_FIELD_TYPES = """
  ~ field: boolean
  - privateField: int
  # protectedField: Integer
  + publicField: String
"""

EXAMPLE_METHOD_TYPES = """
  - privateMethod(): int
  # protectedMethod(): Integer
  + publicMethod(): String
"""

EXAMPLE_CLASS_HEADER = """
class ExampleClass {
  test.data
  --
"""


def assert_strip(str1: str, str2: str) -> None:
    """Compare strings while ignoring some whitespace differences.

    We compare each line with leading & trailing whitespace stripped.
    """
    lines1 = str1.splitlines()
    lines2 = str2.splitlines()
    assert len(lines1) == len(lines2)
    for idx, line1 in enumerate(lines1):
        line2 = lines2[idx]
        assert line1.strip() == line2.strip(), f"Line {idx + 1}"


def test_generate_enum() -> None:
    """Test generation of an Enum."""
    result = runner.invoke(app, ["generate", "tests/data/ExampleEnum.class"])
    assert result.exit_code == 0
    assert_strip(result.stdout, EXAMPLE_ENUM_PLANTUML)


def test_insert() -> None:
    """Test 'insert' command."""
    diagram_path = "tests/data/diagram.puml"
    result = runner.invoke(app, ["insert", "--class-dir", ".", diagram_path])
    assert result.exit_code == 0
    assert EXAMPLE_CLASS_HEADER in result.stdout
    assert EXAMPLE_FIELD_TYPES in result.stdout
    assert EXAMPLE_METHOD_TYPES in result.stdout
    assert "+ defaultMethod(): Integer" in result.stdout
    assert "abstract ExampleAbstract" in result.stdout
    assert "interface ExampleInterface" in result.stdout
    assert "enum ExampleEnum" in result.stdout
