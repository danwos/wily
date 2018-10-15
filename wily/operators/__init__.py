from collections import namedtuple


class BaseOperator(object):
    """Abstract Operator Class"""

    """Name of the operator"""
    name = "abstract"

    """Default settings"""
    defaults = {}

    """Available metrics as a list of tuple ("name"<str>, "description"<str>, "type"<type>)"""
    metrics = ()

    def run(self, module, options):
        raise NotImplementedError()


from wily.operators.mccabe import MccabeOperator
from wily.operators.cyclomatic import CyclomaticComplexityOperator
from wily.operators.maintainability import MaintainabilityIndexOperator
from wily.operators.raw import RawMetricsOperator

"""Type for an operator"""
Operator = namedtuple("Operator", "name cls description")

OPERATOR_MCCABE = Operator(
    name="mccabe",
    cls=MccabeOperator,
    description="Number of branches via the Mccabe algorithm",
)

OPERATOR_CYCLOMATIC = Operator(
    name="cyclomatic",
    cls=CyclomaticComplexityOperator,
    description="Cyclomatic Complexity of modules",
)

OPERATOR_RAW = Operator(
    name="raw", cls=RawMetricsOperator, description="Raw Python statistics"
)

OPERATOR_MAINTAINABILITY = Operator(
    name="maintainability",
    cls=MaintainabilityIndexOperator,
    description="Maintainability index (lines of code and branching)",
)


"""Set of all available operators"""
ALL_OPERATORS = {
    OPERATOR_MCCABE,
    OPERATOR_CYCLOMATIC,
    OPERATOR_MAINTAINABILITY,
    OPERATOR_RAW,
}


def resolve_operator(name):
    """
    Get the :namedtuple:`wily.operators.Operator` for a given name
    :param name: The name of the operator
    :return: The operator type
    """
    r = [operator for operator in ALL_OPERATORS if operator.name == name.lower()]
    if not r:
        raise ValueError(f"Operator {name} not recognised.")
    else:
        return r[0]


def resolve_operators(operators):
    return [resolve_operator(operator) for operator in operators]
