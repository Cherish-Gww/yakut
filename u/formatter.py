# Copyright (c) 2019 UAVCAN Consortium
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@uavcan.org>

from __future__ import annotations
import typing
import click


Formatter = typing.Callable[[typing.Dict[int, typing.Dict[str, typing.Any]]], str]


def formatter_option() -> typing.Callable[[...], None]:
    def validate(ctx: click.Context, param: object, value: str) -> Formatter:
        _ = ctx
        _ = param
        try:
            return _FORMATTERS[value.upper()]()
        except LookupError:
            raise click.BadParameter(f"Invalid format name: {value!r}")

    choices = list(_FORMATTERS.keys())
    default = choices[0]

    return click.option(
        "--format",
        "-F",
        "formatter",
        type=click.Choice(choices, case_sensitive=False),
        callback=validate,
        default=default,
        help=f"""
The format of data printed into stdout.

The final representation of the output data is constructed from an intermediate "builtin-based" representation,
which is a simplified form that is stripped of the detailed DSDL type information, like JSON.
For more info please read the PyUAVCAN documentation on builtin-based representations.

YAML separates objects with `---`.

JSON and TSV (tab separated values) keep exactly one object per line.

TSV is intended for use with third-party software
such as computer algebra systems or spreadsheet processors.

The default is {default}.
""",
    )


def _make_yaml_formatter() -> Formatter:
    from .yaml import YAMLDumper

    dumper = YAMLDumper(explicit_start=True)
    return lambda data: dumper.dumps(data)


def _make_json_formatter() -> Formatter:
    # We prefer simplejson over the standard json because the native json lacks important capabilities:
    #  - simplejson preserves dict ordering, which is very important for UX.
    #  - simplejson supports Decimal.
    import simplejson as json

    return lambda data: json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _make_tsv_formatter() -> Formatter:
    # TODO print into a TSV (tab separated values, like CSV with tabs instead of commas).
    # The TSV format should place one scalar per column for ease of parsing by third-party software.
    # Variable-length entities such as arrays should expand into the maximum possible number of columns?
    # Unions should be represented by adjacent groups of columns where only one such group contains values?
    # We may need to obtain the full type information here in order to build the final representation.
    # Sounds complex. Search for better ways later. We just need a straightforward way of dumping data into a
    # standard tabular format for later processing using third-party software.
    raise NotImplementedError("Sorry, the TSV formatter is not yet implemented")


_FORMATTERS = {
    "YAML": _make_yaml_formatter,
    "JSON": _make_json_formatter,
    "TSV": _make_tsv_formatter,
}


def _unittest_formatter() -> None:
    obj = {
        2345: {
            "abc": {
                "def": [
                    123,
                    456,
                ],
            },
            "ghi": 789,
        }
    }
    assert (
        _FORMATTERS["YAML"]()(obj)
        == """---
2345:
  abc:
    def:
    - 123
    - 456
  ghi: 789
"""
    )
    assert _FORMATTERS["JSON"]()(obj) == '{"2345":{"abc":{"def":[123,456]},"ghi":789}}'
