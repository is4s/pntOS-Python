"""Parses C/C++ headers."""

import re
import tempfile
from pathlib import Path

import clang.cindex
from clang.cindex import CursorKind
from common_api_representation import (
    ApiAttribute,
    ApiClass,
    ApiFunction,
    ApiModule,
)

callback_param_exceptions: set[str] = {
    'receiver',
    'num_modified_keys',
}


def replace_macros(file_contents: str) -> str:
    """Replaces C header macros."""
    file_contents = re.sub(
        'PNTOS_NULLABLE',
        '_Nullable*',
        file_contents,
    )
    return re.sub(
        'PNTOS_ASSUME_NONNULL_END|PNTOS_ASSUME_NONNULL_BEGIN',
        '',
        file_contents,
    )


def remove_directives(file_contents: str) -> str:
    """Replaces C header preprocessor directives."""
    file_contents = re.sub(
        r'#ifdef PNTOS_STATIC_BUILD.*#endif', '', file_contents, flags=re.DOTALL
    )
    file_contents = re.sub(
        r'#ifdef __cplusplus.*{\n#endif', '', file_contents, flags=re.DOTALL
    )
    return re.sub(r'#ifdef __cplusplus.*#endif', '', file_contents, flags=re.DOTALL)


def preprocess_file(in_file: Path) -> str:
    """Preprocesses header file by removing macros and directives."""
    with in_file.open('r', encoding='utf-8') as file:
        header = file.read()
        header = replace_macros(header)
        return remove_directives(header)


def create_temp_file(file_contents: str) -> str:
    """Creates a temporary file with the provided input."""
    with tempfile.NamedTemporaryFile(suffix='.h', delete=False, mode='w') as tmp_file:
        tmp_file.write(file_contents)
    return tmp_file.name


def generate_file_for_parsing(in_file: Path) -> str:
    """Preprocesses input file and returns a temp file with those changes."""
    contents = preprocess_file(in_file)
    return create_temp_file(contents)


def generate_type_list(type_decl: str) -> list[str]:
    """Generates a list of types given a type declaration string."""
    only_type_info = type_decl.split(')(', maxsplit=1)[0]
    only_type_info = only_type_info.replace(
        '(*', '', 1
    )  # remove artifact left over after split
    temp_list = only_type_info.split()
    type_list = []
    for i, item in enumerate(temp_list):
        if '*' in item or item == '':  # skip asterisk (handled later)
            continue
        # rejoin pointer declaration
        if i + 1 < len(temp_list) and '*' in temp_list[i + 1]:
            # make arrays with nullable elements easier to identify
            # differentiate between an array with nullable elements and standard nullability
            # '_Nullable**' vs. '_Nullable*'
            if item == '_Nullable' and temp_list[i + 1] == '**':
                type_list[-1] += '*'
            type_list.append(item + temp_list[i + 1])
        else:
            type_list.append(item)
    return type_list


def parse_callback_param(cursor: clang.cindex.Cursor) -> dict[str, list[str]]:
    """Parses the ``callback`` parameter and returns a dictionary of its parameters."""
    params = {}
    i = 0
    for param in cursor.get_children():
        if param.displayname in callback_param_exceptions:
            continue
        param_type = generate_type_list(param.type.spelling)
        params[f'param_{i}'] = param_type
        i += 1
    return params


def clang_parse_file(
    in_file: Path, c_api_path: Path, firehose_outputs_path: Path
) -> ApiModule:
    """Uses clang to parse a C/C++ header file."""
    module = ApiModule(name=in_file.as_posix())
    tmp_file_path = generate_file_for_parsing(in_file)

    index = clang.cindex.Index.create()
    tu = index.parse(
        tmp_file_path,
        args=[
            '-x',
            'c++',
            '-std=c++17',
            '-fnullability',
            f'-I{c_api_path}',
            f'-I{firehose_outputs_path}',
        ],
    )
    for cursor in tu.cursor.get_children():
        if (
            cursor.kind != CursorKind.STRUCT_DECL
            or cursor.displayname[0] == '_'
            or not cursor.is_definition()
        ):
            continue
        new_class = ApiClass(name=cursor.displayname)
        for field in cursor.get_children():
            field_name = field.displayname
            field_type = generate_type_list(field.type.spelling)

            parameters = {}
            for param in field.get_children():
                if param.kind == CursorKind.PARM_DECL:
                    param_name = param.displayname
                    param_type = generate_type_list(param.type.spelling)
                    # treat callback parameter as its own function
                    if param_name == 'callback':
                        callback_params = parse_callback_param(param)
                        new_class.add_method(
                            ApiFunction(
                                name=field_name + '_callback',
                                return_type=param_type,
                                parameters=callback_params,
                            )
                        )
                        continue
                    parameters[param_name] = param_type
            if parameters:
                new_field = ApiFunction(
                    name=field_name, return_type=field_type, parameters=parameters
                )
                new_class.add_method(new_field)
            else:
                new_field = ApiAttribute(name=field_name, type=field_type)
                new_class.add_attribute(new_field)
        module.add_class(new_class)
    Path(tmp_file_path).unlink()
    return module
