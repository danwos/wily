"""
Diff command.

Compares metrics between uncommitted files and indexed files.
"""
import os

import tabulate

from wily import logger
from wily.config import DEFAULT_GRID_STYLE
from wily.operators import (
    resolve_metric,
    resolve_operator,
    get_metric,
    GOOD_COLORS,
    BAD_COLORS,
    OperatorLevel,
)
from wily.state import State


def diff(config, files, metrics, changes_only=True, detail=True):
    """
    Show the differences in metrics for each of the files.

    :param config: The wily configuration
    :type  config: :namedtuple:`wily.config.WilyConfig`

    :param files: The files to compare.
    :type  files: ``list`` of ``str``

    :param metrics: The metrics to measure.
    :type  metrics: ``list`` of ``str``

    :param changes_only: Only include changes files in output.
    :type  changes_only: ``bool``

    :param detail: Show details (function-level)
    :type  detail: ``bool``
    """
    config.targets = files
    files = list(files)
    state = State(config)
    last_revision = state.index[state.default_archiver].revisions[0]

    # Convert the list of metrics to a list of metric instances
    operators = {resolve_operator(metric.split(".")[0]) for metric in metrics}
    metrics = [(metric.split(".")[0], resolve_metric(metric)) for metric in metrics]
    data = {}
    results = []

    # Build a set of operators
    _operators = [operator.cls(config) for operator in operators]

    cwd = os.getcwd()
    os.chdir(config.path)
    for operator in _operators:
        logger.debug(f"Running {operator.name} operator")
        data[operator.name] = operator.run(None, config)
    os.chdir(cwd)

    # Write a summary table..
    extra = []
    for operator, metric in metrics:
        if detail and resolve_operator(operator).level == OperatorLevel.Object:
            for file in files:
                try:
                    extra.extend(
                        [
                            f"{file}:{k}"
                            for k in data[operator][file]["detailed"].keys()
                            if k != metric.name
                            and isinstance(data[operator][file]["detailed"][k], dict)
                        ]
                    )
                except KeyError:
                    logger.debug(f"File {file} not in cache")
                    logger.debug("Cache follows -- ")
                    logger.debug(data[operator])
    files.extend(extra)
    logger.debug(files)
    for file in files:
        metrics_data = []
        has_changes = False
        for operator, metric in metrics:
            try:
                current = last_revision.get(
                    config, state.default_archiver, operator, file, metric.name
                )
            except KeyError as e:
                current = "-"
            try:
                new = get_metric(data, operator, file, metric.name)
            except KeyError as e:
                new = "-"
            if new != current:
                has_changes = True
            if metric.type in (int, float) and new != "-" and current != "-":
                if current > new:
                    metrics_data.append(
                        "{0:n} -> \u001b[{2}m{1:n}\u001b[0m".format(
                            current, new, BAD_COLORS[metric.measure]
                        )
                    )
                elif current < new:
                    metrics_data.append(
                        "{0:n} -> \u001b[{2}m{1:n}\u001b[0m".format(
                            current, new, GOOD_COLORS[metric.measure]
                        )
                    )
                else:
                    metrics_data.append("{0:n} -> {1:n}".format(current, new))
            else:
                if current == "-" and new == "-":
                    metrics_data.append("-")
                else:
                    metrics_data.append("{0} -> {1}".format(current, new))
        if has_changes or not changes_only:
            results.append((file, *metrics_data))
        else:
            logger.debug(metrics_data)

    descriptions = [metric.description for operator, metric in metrics]
    headers = ("File", *descriptions)
    if len(results) > 0:
        print(
            # But it still makes more sense to show the newest at the top, so reverse again
            tabulate.tabulate(
                headers=headers, tabular_data=results, tablefmt=DEFAULT_GRID_STYLE
            )
        )
