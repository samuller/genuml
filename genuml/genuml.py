#!/usr/bin/env python3
#
# GenUML
#
# Tool to aid in using PlantUML to create class diagrams by generating
# UML diagrams. Based on the style and functionality of ObjectAid UML
# Explorer, an Eclipse plug-in which is no longer supported.
#
# Requirements: python javap graphviz
#
# Todo:
# - handle method overloads in pattern filter?
# - use proper EBNF parsing?
# - internal classes?
# - stdlib or 3rd-party lib classes?
#

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any, cast

import typer

from . import __version__

app = typer.Typer(
    help="Generate PlantUML class diagram DSL from Java class files.",
    add_completion=False
)


def split_indices(string: str, indices: List[Optional[int]]) -> List[str]:
    # See: https://stackoverflow.com/questions/10851445/splitting-a-string-by-list-of-indices
    parts = [string[i:j] for i, j in zip(indices, indices[1:]+[None])]
    return parts


# [10,20,30,40,50]
# [0,10, 11,20, 21,30, 31,40, 41,50]
def split_indices_exclude(string: str, splits: List[int]) -> List[str]:
    """Split string at indices, and also exclude characters at each index."""
    if len(splits) == 0:
        return [string]
    parts = [string[0:splits[0]]]
    for idx, spl in enumerate(splits):
        if idx == 0:
            continue
        beg = splits[idx-1]+1
        end = spl
        parts.append(string[beg:end])
    parts.append(string[splits[-1]+1:])
    return parts


def split_args(args: str) -> List[str]:
    """Split argument list of types.

    Also has to work for generic types where type names can contain multiple
    type names recursively."""
    depth = 0
    split_points = []
    for idx, char in enumerate(args):
        if char == '<':
            depth += 1
        if char == '>':
            depth -= 1
        if char == ',' and depth == 0:
            split_points.append(idx)
    split_args = split_indices_exclude(args, split_points)
    split_args = [a.strip() for a in split_args]
    return split_args


METHOD_MODIFIERS = [
    'public', 'protected', 'private', 'static',
    'abstract', 'final', 'synchronized', 'native',
    'default'
]


def parse_modifiers_plus_type(modifiers: List[str]) -> Tuple[List[str], List[str]]:
    """Parse modifier keywords that are usually combined with a type."""
    return_type = [mod for mod in modifiers if mod not in METHOD_MODIFIERS]
    modifiers = [mod for mod in modifiers if mod in METHOD_MODIFIERS]
    return modifiers, return_type


def parse_method(signature: str) -> Dict[str, Any]:
    """Parse method signature."""
    # https://cs.au.dk/~amoeller/RegAut/JavaBNF.html
    # <method header>
    if '(' not in signature:
        # not a method
        return {}
    info: Dict[str, Any] = {'_type': 'method'}
    pre_args, args = signature.split('(')
    # check that "throws" etc. doesn't appear after arguments
    assert args[-1] == ')'
    args = args[:-1]
    info['args'] = split_args(args)
    split_pre_args = pre_args.split(' ')
    info['name'] = split_pre_args[-1]
    modifiers = split_pre_args[:-1]
    modifiers, type_ = parse_modifiers_plus_type(modifiers)
    info['type'] = type_
    info['modifiers'] = modifiers
    return info


def parse_field(declaration: str) -> Dict[str, Any]:
    """Parse method declaration."""
    info: Dict[str, Any] = {'_type': 'field'}
    # re.split(' ', declaration)
    decls = declaration.split(' ')
    modifiers, type_ = parse_modifiers_plus_type(decls[:-1])
    info['type'] = type_
    info['modifiers'] = modifiers
    info['name'] = decls[-1]
    return info


def parse_method_or_field(declaration: str) -> Dict[str, Any]:
    """Parse method or field declarations."""
    if '(' in declaration:
        return parse_method(declaration)
    return parse_field(declaration)


def remove_package_from_type(type_: str) -> str:
    """Remove package details from all types, i.e. from FQCN to only class.

    Also has to work for generic types where type names can contain multiple
    type names recursively.
    """
#    # Handle generics
#    gen_type = None
#    if '<' in type_:
#        type_, gen_type = type_.split('<')
#        assert gen_type[-1] == '>'
#        gen_type = gen_type[:-1]
#        gen_type = remove_package_from_type(gen_type)
#    type_ = type_.split('.')
#    type_ = type_[-1]
#    if gen_type is not None:
#        type_ = f'{type_}<{gen_type}>'
    type_ = re.sub(r"[^ .()<>]+\.", "", type_)
    return type_


def remove_class_from_package(fqcn: str) -> str:
    package_path = re.sub(r"\.[^ .()<>]+$", "", fqcn)
    return package_path


def parse_class(declaration: str) -> Dict[str, Any]:
    """Parse class declaration."""
    assert declaration.endswith(' {')
    declaration = declaration[:-2]
    info: Dict[str, Any] = {'_type': 'class'}

    impl = declaration.split(' implements ')
    info['implements'] = split_args(impl[1]) if len(impl) > 1 else None
    exts = impl[0].split(' extends ')
    info['extends'] = exts[1] if len(exts) > 1 else None
    modifiers = exts[0].split(' ')
    info['name'] = modifiers[-1]
    info['package'] = remove_class_from_package(info['name'])
    modifiers = modifiers[:-1]
    if 'interface' in modifiers:
        info['_type'] = 'interface'
        modifiers.remove('interface')
    elif 'abstract' in modifiers:
        info['_type'] = 'abstract'
        modifiers.remove('abstract')
    else:
        modifiers.remove('class')
    info['modifiers'] = modifiers
    if info['extends'] is not None and info['extends'].startswith('java.lang.Enum'):
        info['_type'] = 'enum'
    # Annotation's @interface = interface ... extends java.lang.annotation.Annotation
    if info['extends'] is not None and info['extends'].startswith(
            'java.lang.annotation.Annotation'):
        info['_type'] = 'annotation'
    return info


def symbol_from_modifiers(modifiers: List[str]) -> str:
    if 'private' in modifiers:
        return '-'
    if 'protected' in modifiers:
        return '#'
    if 'public' in modifiers:
        return '+'
    return '~'


def pprint(value: str) -> None:
    print(json.dumps(value, sort_keys=True, indent=4))


def evalf(fstring: str, local_vars: Dict[str, Any]) -> str:
    """Eval() for dynamic f-string (that may contain unescaped single quotes)."""
    return cast(str, eval('f"{}"'.format(fstring), None, local_vars))


def parse_javap_output(output: str, keep_names: Optional[List[str]] = None) -> str:
    """Parse output of javap and convert to PlantUML diagram code.

    Parameters
    ----------
        keep_names:
            None: means all fields and methods are shown
            []: means no fields or methods are shown
            List[str]: means only the given fields and methods are shown
    """
    # if keep_names is None:
    #     keep_names = []

    lines = output.splitlines()
    lines = [line.strip() for line in lines]
    # Remove first log line: Compiled from "Job.java"
    assert lines[0].startswith("Compiled from")
    del lines[0]

    assert lines[-1] == "}"
    class_ = parse_class(lines[0])

    methods_fields = lines[1:-1]
    # remove inner class functions (any line containing a $)
    methods_fields = [mf for mf in methods_fields if '$' not in mf]
    # remove "static {}" that appears in enums from javap
    methods_fields = [mf for mf in methods_fields if '{}' not in mf]
    # remove semi-colons
    methods_fields = [mf.replace(';', '') for mf in methods_fields]
    # parse lines containing methods or fields into
    parsed_members: List[Dict[str, Any]] = [parse_method_or_field(mf) for mf in methods_fields]

    # remove package paths from types and names
    for mf in parsed_members:
        mf['name'] = remove_package_from_type(mf['name'])
        mf['type'] = [remove_package_from_type(mft) for mft in mf['type']]
        if mf['_type'] == 'method':
            mf['args'] = [remove_package_from_type(mfa) for mfa in mf['args']]

    if keep_names is not None:
        # filter to only keep fields and methods with given names
        parsed_members = [mf for mf in parsed_members if mf['name'] in keep_names]
        # check that all given values were valid field/method names
        mf_names = [mf['name'] for mf in parsed_members]
        for name in keep_names:
            if name not in mf_names:
                raise ValueError(f"Unknown method or field: {name}")

    # construct dict with all parsed information
    info: Dict[str, Any] = {}
    info['class'] = class_
    info['methods'] = [mf for mf in parsed_members if mf['_type'] == 'method']
    info['fields'] = [mf for mf in parsed_members if mf['_type'] == 'field']
    # pprint(info['class'])

    # convert to dict values to strings & strip package paths
    info['class']['name'] = remove_package_from_type(info['class']['name'])
    for mf in parsed_members:
        mf['type'] = ' '.join(mf['type'])
        if mf['_type'] == 'method':
            mf['args'] = ', '.join(mf['args'])
        # keep list value as _modifiers
        mf['_modifiers'] = mf['modifiers']
        mf['modifiers'] = ' '.join(mf['modifiers'])

    FIELD_OUTPUT = "  {symbol_from_modifiers(_modifiers)} {name}: {type}"
    fields = []
    for field in info['fields']:
        line = evalf(FIELD_OUTPUT, field)
        fields.append(line)

    METHOD_OUTPUT = "  {symbol_from_modifiers(_modifiers)} {name}({args}): {type}"
    methods = []
    for method in info['methods']:
        line = evalf(METHOD_OUTPUT, method)
        methods.append(line)

    fields_str = ('\n'.join(fields) + '\n') if len(fields) > 0 else ''
    # add separator between fields and methods if both have data
    fields_str += '  --\n' if len(fields) > 0 and len(methods) > 0 else ''
    methods_str = ('\n'.join(methods) + '\n') if len(methods) > 0 else ''

    return (
        f"{info['class']['_type']} {info['class']['name']} {{\n"
        f"  {info['class']['package']}\n  --\n"
        f"{fields_str}"
        f"{methods_str}"
        f"}}"
    )


def generate_uml_from_class(
        class_file: Path,
        filters: Optional[List[str]] = None
        ) -> Optional[str]:
    """Helper function to generate PlantUML for single given Java class file."""
    res = subprocess.run(["javap", "-private", class_file], stdout=subprocess.PIPE)
    if res.returncode == 0:
        try:
            uml = parse_javap_output(res.stdout.decode('UTF-8'), filters)
            return uml
        except Exception as err:
            print(f"Error: {err}", file=sys.stderr)
    return None


def parse_pattern(pattern: str) -> Tuple[str, Optional[List[str]]]:
    """Parse pattern string into FQCN and filters."""
    parts = pattern.split(":")
    fqcn = parts[0]
    filters = None
    if len(parts) == 2:
        filters = parts[1].strip().split(' ')
        if filters == ['']:
            filters = []
    return fqcn, filters


def convert_fqcn_to_path(class_dir: Path, fqcn: str) -> Path:
    """Convert fully qualified class name to a path to class file."""
    pattern_file = fqcn.replace(".", os.path.sep)
    pattern_file += ".class"
    return class_dir / pattern_file


@app.command()
def generate(
        class_file: Path = typer.Argument(
            ...,
            help="Path to compiled Java class file.",
            exists=True,
            file_okay=True,
            dir_okay=False
        ),
        filters: str = typer.Argument(
            None,
            help="List of only field/method names that should be shown.",
        )) -> None:
    """Generate PlantUML for single given Java class file."""
    filter_list = filters.split(' ') if filters is not None else None
    uml = generate_uml_from_class(class_file, filter_list)
    if uml is not None:
        print(uml)


@app.command()
def insert(
        plantuml_file: Path = typer.Argument(
            ...,
            help="Path to file containing only PlantUML.",
            exists=True,
            file_okay=True,
            dir_okay=False
        ),
        class_dir: Path = typer.Option(
            "classes",
            help="Directory containing class files.",
            exists=True,
            file_okay=False,
            dir_okay=True
        ),
        pattern_marker: str = typer.Option(
            "[JAVA] ",
            help="Marker string used to indicate the following string is a pattern to process."
        )) -> None:
    """Insert diagrams into PlantUML containing pattern comments.

    "Patterns" are strings describing the class diagram to generate. They consist of
    a fully qualified class name (FQCN) as well as an optional "filter" which lists the
    only fields and methods that should be included in the diagram. A colon (":") separates
    the pattern and FQCN.

    The pattern strings should be placed in a PlantUML comment (lines starting with single
    quote) and should also be preceded by a "pattern marker" which is a string identifying
    that the rest of the line should be processed as a pattern string.

    \b
    The default format is: '[JAVA] FQCN[: [FILTERS...]]
    Full example of line in PlantUML:

    '[JAVA] java.util.lang.String: length replaceAll toUpperCase
    """
    with open(plantuml_file) as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines]

    # output whole file with generated UML placed after patterns
    pattern_marker = "'" + pattern_marker
    for line in lines:
        print(line)
        if line.startswith(pattern_marker):
            # extract pattern from line
            pattern = line.replace(pattern_marker, "")
            # parse pattern and generate diagram code
            fqcn, filters = parse_pattern(pattern)
            class_file = convert_fqcn_to_path(class_dir, fqcn)
            uml = generate_uml_from_class(class_file, filters)
            # output generated pattern
            if uml is not None:
                print(uml)
            print()


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"genuml, version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
        version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
        )) -> None:
    pass


if __name__ == "__main__":
    app()
