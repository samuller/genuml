#!/usr/bin/env python3
from genuml import *


def test_split_args():
    assert split_args("arg1") == ['arg1']
    assert split_args("arg1, arg2") == ['arg1', 'arg2']
    assert split_args("arg1<A,B>, arg2<C,D>") == ['arg1<A,B>', 'arg2<C,D>']
    assert split_args("arg1<A<B, C,D>,E,F>, arg2<C,D>") == ['arg1<A<B, C,D>,E,F>', 'arg2<C,D>']


def test_parse_method():
    assert parse_method("public static void main(String[])") == {
        '_type': 'method', 'name': 'main', 'type': ['void'],
        'modifiers': ['public', 'static'],
        'args': ['String[]']
    }
    assert parse_method("public java.lang.String()") == {
        '_type': 'method',  # constructor
        'name': 'java.lang.String', 'type': [],
        'modifiers': ['public'],
        'args': ['']  # []
    }


def test_remove_package_from_type():
    assert remove_package_from_type("java.lang.String") == "String"
    assert remove_package_from_type("String") == "String"


def test_remove_class_from_package():
    assert remove_class_from_package("java.lang.String") == "java.lang"
