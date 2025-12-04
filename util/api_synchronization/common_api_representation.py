"""Common API Representation."""

from dataclasses import dataclass, field

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'


def colored(msg: str, color: str) -> str:
    """
    Returns the colored version of an input string.

    Args:
        msg (str): Message to be colored.
        color (str): The code of the color to use.

    Returns:
        str
    """
    return f'{color}{msg}\033[0m'


@dataclass
class ApiFunction:
    """Generic API Function dataclass."""

    name: str
    return_type: list[str] = field(default_factory=list)
    parameters: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ApiAttribute:
    """Generic API Attribute dataclass."""

    name: str
    type: list[str] = field(default_factory=list)


@dataclass
class ApiClass:
    """Generic API Class dataclass."""

    name: str
    methods: list[ApiFunction] = field(default_factory=list)
    attributes: list[ApiAttribute] = field(default_factory=list)

    def add_method(self, new_function: ApiFunction) -> None:
        """Adds method to class method list."""
        self.methods.append(new_function)

    def add_attribute(self, new_attribute: ApiAttribute) -> None:
        """Adds attribute to class attribute list."""
        self.attributes.append(new_attribute)


@dataclass
class ApiModule:
    """Generic API Module dataclass."""

    name: str
    classes: list[ApiClass] = field(default_factory=list)

    def add_class(self, new_class: ApiClass) -> None:
        """Adds class to module class list."""
        self.classes.append(new_class)


class CtoPyApiComparator:
    """A class designed to compare the C API with the Python API."""

    common_types: dict[str, str]
    uncommon_types: dict[str, str]
    exceptions: set[str]
    mismatch: bool

    def __init__(self) -> None:
        """Default constructor. Setup common types dict."""
        self.common_types = {
            # Generic
            'char*': 'str',
            'char**': 'list[str',
            'double': 'float64',
            'double*': 'NDArray[float64]',
            'int': 'int',  # size_t
            '_Nullable**': ' | None]',
            '_Nullable*': ' | None',
            'struct': '',
            'void': 'None',
            'void*': 'Any',
            # Pntos Messages
            'PntosMessage*': 'Message',
            'PntosMessage**': 'list[Message',
            'PntosMessageArray*': 'list[Message',
            'PntosMessageType': 'type[AspnBase]',
            'PntosMessageTypeArray*': 'list[type[AspnBase]',
            # Generic Pntos Managed Types
            'PntosByteArray*': 'bytes',
            'PntosMatrix*': 'NDArray[float64]',
            'PntosMatrix**': 'list[NDArray[float64]',
            'PntosStringArray*': 'list[str',
            # Edge cases
            'AspnBase*': 'AspnBase',
            'PntosInertialType': 'type[InertialType]',
            'PntosInitializationType': 'type[InitializationType]',
            'PntosKeyValueStoreType': 'type[RegistryValueTypeUnion]',
            'PntosPluginArray*': 'list[CommonPlugin',
            'double[3]': 'NDArray[float64]',
            'AspnTypeTimestamp*': 'list[TypeTimestamp',
            'PntosStandardDynamicsModelCallback': 'Callable[[NDArray[float64]], NDArray[float64]]',
            'PntosStandardMeasurementModelCallback': 'Callable[[NDArray[float64]], NDArray[float64]]',
        }
        self.uncommon_types = {
            'unsigned char*': 'bytes',
        }
        self.attribute_exceptions = {
            'memory': '',
            'length': '',
            'plugin_type': '',
            'num_covariances': '',
            'common': '',
            'num_preprocessors': '',
            'num_processors': '',
            'num_blocks': '',
            'num_virtual_blocks': '',
            'num_state_block_labels': '',
        }
        self.method_exceptions = {
            'log_message_fmt': 'log_message',
            'log_fmt': 'log',
            'clone': '',
            # KeyValueStore mapping
            'get_key_array': 'keys',
            'has_key': '__contains__',
            'get_str': 'get_value',
            'get_str_array': 'get_value',
            'get_int': 'get_value',
            'get_bool': 'get_value',
            'get_double': 'get_value',
            'get_double_array': 'get_value',
            'get_message': 'get_value',
            'set_str': 'set_value',
            'set_str_array': 'set_value',
            'set_int': 'set_value',
            'set_bool': 'set_value',
            'set_double': 'set_value',
            'set_double_array': 'set_value',
            'set_message': 'set_value',
            # StandardFusionEngine
            'get_time': 'time',
            'get_strategy': 'strategy',
            'set_time': 'time',
            'set_strategy': 'strategy',
            'get_state_block_labels': 'state_block_labels',
            'get_measurement_processor_labels': 'measurement_processor_labels',
            'get_virtual_state_block_target_labels': 'virtual_state_block_target_labels',
            'has_block': '',
            'has_processor': '',
            # StandardFusionStrategy
            'set_covariance_block': 'set_covariance_slice',
            'set_covariance_slice': 'set_covariance_slice',
            'get_num_states': 'num_states',
            'get_estimate': 'estimate',
            'get_covariance': 'covariance',
            # Orchestration/Mediator
            'get_filter_description_list': 'filter_description_list',
        }
        self.parameter_exceptions = {
            'receiver': '',
            'num_bytes': '',
            'num_solution_times': '',
            'num_block_labels': '',
            'num_times': '',
            'num_state_block_labels': '',
            'gen_x_and_p_func': 'x_and_p',  # semantically different but functionally equivalent
        }
        self.class_exceptions = {
            # Pntos Managed Memory => ''
            'PntosMessageArray': '',
            'PntosString': '',
            'PntosByteArray': '',
            'PntosStringArray': '',
            'PntosIntArray': '',
            'PntosDoubleArray': '',
            'PntosMatrix': '',
            'PntosMessageTypeArray': '',
            'PntosPluginArray': '',
            'PntosGenXandP': 'EstimateWithCovariance',
            # Struct => TypeVar
            'PntosCommonFusionEngine': 'FusionEngineType',
            'PntosCommonFusionStrategy': 'FusionStrategyType',
            'PntosCommonStateModelProvider': 'StateModelProviderType',
            # Actual Exceptions
            'PntosMessageStreamConfig': 'MessageStreamConfig',
        }
        self.mismatch = False

    def _convert_attrs_to_dict(self, attrs: list[ApiAttribute]) -> dict[str, list[str]]:
        ret_dict: dict[str, list[str]] = {}
        for attr in attrs:
            ret_dict[attr.name] = attr.type
        return ret_dict

    def _convert_methods_to_dicts(
        self, meths: list[ApiFunction]
    ) -> tuple[dict[str, list[str]], dict[str, dict[str, list[str]]]]:
        return_type_dict: dict[str, list[str]] = {}
        param_dict: dict[str, dict[str, list[str]]] = {}
        for meth in meths:
            return_type_dict[meth.name] = meth.return_type
            param_dict[meth.name] = meth.parameters
        return (return_type_dict, param_dict)

    def _convert_c_type(self, type_list: list[str]) -> str:
        converted_type = ''
        length = len(type_list)
        if length == 1:
            c_type = type_list[0]
            type_piece = self.common_types.get(c_type)
            # c_type is likely a plugin type, if it isn't an error will be logged during c_to_py type comparison
            if type_piece is None:
                converted_type = c_type.removeprefix('Pntos').removeprefix('Aspn')
                converted_type = converted_type.removesuffix('*')
            else:
                converted_type += type_piece
                # close list bracket
                if type_piece.startswith('list'):
                    converted_type += ']'
            return converted_type

        joined_c_type = ' '.join(type_list)
        uncommon_type = self.uncommon_types.get(joined_c_type)
        if uncommon_type is not None:
            return uncommon_type

        for index, specifier in enumerate(type_list):
            type_piece = self.common_types.get(specifier)
            if type_piece is None:
                converted_type += (
                    specifier.removeprefix('Pntos')
                    .removeprefix('Aspn')
                    .removesuffix('*')
                )
            else:
                converted_type += type_piece
                if type_piece.startswith('list') and (
                    index + 1 == length or type_list[index + 1] != '_Nullable**'
                ):
                    converted_type += ']'
        return converted_type

    def _compare_classname(self, c_class: ApiClass, py_class: ApiClass) -> None:
        temp = c_class.name.removeprefix('Pntos')
        if temp != py_class.name:
            print(
                f'WARNING: The C struct name {c_class.name} does not match the Python class name '
                f'{py_class.name} after removing the "Pntos" prefix. Comparison will continue, '
                'but ensure these classes should be compared.'
            )

    def _compare_type(
        self, c_type: list[str], py_type: list[str], log_msg: str = ''
    ) -> bool:
        pyt = py_type[0]
        ct = self._convert_c_type(c_type)
        if pyt == ct:
            return True
        print(
            f'{log_msg} C type specifiers {c_type} was converted to {ct} '
            f'which is not equivalent to the Python API type {pyt}'
        )
        return False

    def _compare_attributes(self, c_class: ApiClass, py_class: ApiClass) -> bool:
        c_attrs = self._convert_attrs_to_dict(c_class.attributes)
        py_attrs = self._convert_attrs_to_dict(py_class.attributes)
        ret_val = True

        for attr_name, c_type in c_attrs.items():
            if attr_name in self.attribute_exceptions:
                print(
                    f'Attribute {attr_name} was found in exceptions list. Skipping attribute...'
                )
                continue
            if attr_name not in py_attrs:
                print(
                    f'{colored("ERROR:", RED)} C struct {c_class.name} has attribute {attr_name} not present '
                    f'in Python class {py_class.name}. Skipping attribute...'
                )
                ret_val = False
                continue
            py_type = py_attrs[attr_name]
            if not self._compare_type(
                c_type,
                py_type,
                f'{colored("ERROR:", RED)} For attribute "{attr_name}",',
            ):
                ret_val = False
        return ret_val

    def _compare_methods(self, c_class: ApiClass, py_class: ApiClass) -> bool:
        c_method_types, c_method_params = self._convert_methods_to_dicts(
            c_class.methods
        )
        py_method_types, py_method_params = self._convert_methods_to_dicts(
            py_class.methods
        )
        ret_val = True

        # Compare method return types
        for meth_name, c_type in c_method_types.items():
            if meth_name in self.method_exceptions:
                print(
                    f'Method "{meth_name}" was found in exceptions list. Skipping method...'
                )
                continue
            if meth_name not in py_method_types:
                print(
                    f'{colored("ERROR:", RED)} C struct {c_class.name} has method {meth_name} not present '
                    f'in Python class {py_class.name}. Skipping method...'
                )
                ret_val = False
                continue
            py_type = py_method_types[meth_name]
            if not self._compare_type(
                c_type,
                py_type,
                f'{colored("ERROR:", RED)} Method "{meth_name}" return type mismatch.',
            ):
                ret_val = False

        # Compare method parameters
        for meth_name, c_params in c_method_params.items():
            if meth_name in self.method_exceptions:
                # Message already printed
                continue
            if meth_name not in py_method_params:
                # Warning already printed, just continue
                continue
            py_params = py_method_params[meth_name]
            for param_name, c_param_type in c_params.items():
                if param_name in self.parameter_exceptions:
                    print(
                        f'Parameter "{param_name}" was found in exceptions list. Skipping parameter...'
                    )
                    continue
                if param_name not in py_params:
                    print(
                        f'{colored("ERROR:", RED)} C struct {c_class.name} method {meth_name} has '
                        f'parameter "{param_name}" not present in '
                        f'Python class {py_class.name}. Skipping...'
                    )
                    ret_val = False
                    continue
                py_param_type = py_params[param_name]
                if not self._compare_type(
                    c_param_type,
                    py_param_type,
                    f'{colored("ERROR:", RED)} Parameter "{param_name}" in method "{meth_name}" has type mismatch.',
                ):
                    ret_val = False
        return ret_val

    def compare_classes(self, c_class: ApiClass, py_class: ApiClass) -> None:
        """Compares two classes for semantic equivalence."""
        self._compare_classname(c_class, py_class)

        if not self._compare_attributes(c_class, py_class):
            self.mismatch = True
            print(
                f'{colored("RESULT:", YELLOW)} C struct {c_class.name} is NOT semantically '
                f'equivalent with Python class {py_class.name}.'
            )
            return

        # Compare Methods
        if not self._compare_methods(c_class, py_class):
            self.mismatch = True
            print(
                f'{colored("RESULT:", YELLOW)} C struct {c_class.name} is NOT semantically '
                f'equivalent with Python class {py_class.name}.'
            )
            return

        print(
            f'{colored("RESULT:", YELLOW)} C struct {c_class.name} is semantically equivalent with Python class {py_class.name}.'
        )

    def compare_modules(self, c_module: ApiModule, py_module: ApiModule) -> bool:
        """Compares two modules for semantic equivalence."""
        py_classes: dict[str, ApiClass] = {}
        for cls in py_module.classes:
            py_classes['Pntos' + cls.name] = cls
        for c_class in c_module.classes:
            if c_class.name in self.class_exceptions:
                print(f'C Struct {c_class.name} found in exceptions list. Skipping...')
                continue
            if c_class.name not in py_classes:
                print(
                    f'{colored("ERROR:", RED)} C struct {c_class.name} not found in Python API module {py_module.name}. Skipping...'
                )
                self.mismatch = True
                continue
            self.compare_classes(c_class, py_classes[c_class.name])
        c_mod_name = c_module.name.split('/')[-1]
        py_mod_name = py_module.name.split('/')[-1]
        if self.mismatch:
            print(
                f'{colored("FINAL RESULT:", RED)} The C module {c_mod_name} is NOT '
                f'semantically equivalent with the Python module {py_mod_name}'
            )
        else:
            print(
                f'{colored("FINAL RESULT:", GREEN)} The C module {c_mod_name} is '
                f'semantically equivalent with the Python module {py_mod_name}'
            )
        return self.mismatch
