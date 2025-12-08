"""Parses Python Files."""

import ast
from pathlib import Path

from common_api_representation import (
    ApiAttribute,
    ApiClass,
    ApiFunction,
    ApiModule,
)

PY_TO_C: dict[str, str] = {
    'type[FusionStrategyType]': 'FusionType',
    'type[FusionEngineType]': 'FusionType',
    'FusionEngineType | None': 'CommonFusionEngine | None',
    'FusionStrategyType | None': 'CommonFusionStrategy | None',
    'InertialType | None': 'CommonInertial | None',
    'InitializationType | None': 'CommonInitializationStrategy | None',
    'type[StateModelProviderType]': 'FusionType',
    'StateModelProviderType | None': 'CommonStateModelProvider | None',
}


class ApiVisitor(ast.NodeVisitor):
    """
    An AST Visitor implementation that is designed to parse Python files and extract typing information.

    The current implementation disregards decorators and inheritance information.
    """

    module: ApiModule
    curr_class: ApiClass | None

    def __init__(self, module_name: str) -> None:
        """Initializes class attributes."""
        self.module = ApiModule(name=module_name)
        self.curr_class = None

    def visit_Module(self, node: ast.Module) -> None:
        """
        Customized method for visiting modules.

        NOTE: Only searches classes.
        """
        for stmt in node.body:
            if isinstance(stmt, ast.ClassDef):
                self.visit(stmt)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Customized method for visiting classes.

        NOTE: Only searches functions and attributes (AnnAssign).
        """
        cls = ApiClass(name=node.name)
        self.curr_class = cls
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AnnAssign)):
                self.visit(stmt)
        self.module.add_class(cls)
        self.curr_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Customized method for visiting methods and their arguments."""
        name = node.name
        return_type = ast.unparse(node.returns)
        return_type = [self._convert_type(return_type)]
        params = {}
        for arg in node.args.args:
            param_name = arg.arg
            if param_name == 'self':
                param_type = [self.curr_class.name]
            # treat callback param as its own function
            elif param_name == 'callback':
                self._parse_callback_param(arg, name)
                continue
            else:
                param_type = ast.unparse(arg.annotation)
                param_type = [self._convert_type(param_type)]
            params[param_name] = param_type
        func = ApiFunction(name=name, return_type=return_type, parameters=params)
        self.curr_class.add_method(func)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Customized method for visiting class attributes."""
        if isinstance(node.target, ast.Name):
            attr_name = node.target.id
            attr_type = ast.unparse(node.annotation)
            attr_type = [self._convert_type(attr_type)]
            attr = ApiAttribute(name=attr_name, type=attr_type)
            self.curr_class.add_attribute(attr)

    def _convert_type(self, read_type: str) -> str:
        read_type = read_type.replace("'", '')
        conv_type = PY_TO_C.get(read_type)
        if conv_type is not None:
            return conv_type
        return read_type

    def _parse_callback_param(self, arg: ast.arg, func_name: str) -> None:
        """Parses ``callback`` parameter and stores it as its own function."""
        callback_spelling = ast.unparse(arg.annotation)
        sep = callback_spelling.rfind(',')
        callback_type = callback_spelling[sep + 2 : -1]  # slice out return type
        callback_param_type_spelling = callback_spelling[
            10 : sep - 1
        ]  # slice out parameters
        callback_param_type_spelling = callback_param_type_spelling.replace(
            "'", ''
        )  # remove typing quotes
        callback_param_types = callback_param_type_spelling.split(', ')
        callback_params = {}
        for i, ptype in enumerate(callback_param_types):
            callback_params[f'param_{i}'] = [ptype]
        callback_func = ApiFunction(
            name=func_name + '_callback',
            return_type=[callback_type],
            parameters=callback_params,
        )
        self.curr_class.add_method(callback_func)


def parse_python_file(in_file: Path) -> ApiModule:
    """Parses Python file."""
    with in_file.open('r', encoding='utf-8') as file:
        contents = file.read()
    tree = ast.parse(contents)

    visitor = ApiVisitor(in_file.as_posix())
    visitor.visit(tree)
    return visitor.module
