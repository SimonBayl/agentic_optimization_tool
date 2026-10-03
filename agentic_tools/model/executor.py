"""Check and execute generated code in an isolated subprocess.

The AST check and the subprocess guard against mistakes of the generated
code; they are not a security sandbox.
"""

import ast
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from data_model.settings import Settings


def extract_code(text: str) -> str:
    """Return the last fenced code block, or the whole text without one."""
    blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    return (blocks[-1] if blocks else text).strip()


def imported_modules(tree: ast.AST) -> set[str]:
    """List the top-level modules imported by a syntax tree."""
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            modules.add((node.module or "").split(".")[0])
    return modules


def code_errors(code: str, function: str, settings: Settings) -> str:
    """Report syntax errors, forbidden constructs or a missing function."""

    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return f"SyntaxError: {error}"

    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    defined = {
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)}

    builder = settings.model_builder
    imports = sorted(imported_modules(tree) - builder.allowed_imports)
    forbidden = sorted(names & builder.forbidden_names)

    problems = [f"Forbidden import: {module}." for module in imports]
    problems += [f"Forbidden name: {name}." for name in forbidden]

    if function not in defined:
        problems.append(f"Function {function} is not defined.")

    return "\n".join(problems)


async def run_stage(
    stage: str,
    script: Path,
    data_dir: Path,
    settings: Settings,
) -> tuple[dict[str, Any], str]:
    """
    Run the generated script through the runner in a subprocess.

    Parameters
    ----------
    stage:
        ``data`` to load the data only, ``solve`` to also solve the model.
    script:
        File holding the generated code.
    data_dir:
        Folder containing the input files.
    settings:
        Global parameters, giving the time limits and the error length.

    Returns
    -------
    tuple[dict[str, Any], str]
        Parsed JSON report and an empty error, or an empty report and the
        error text to feed back to the code generator.
    """
    builder = settings.model_builder
    timeout = builder.timeouts[stage]
    runner = Path(__file__).with_name("runner.py")
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-I", str(runner), stage, str(script),
        str(data_dir.resolve()), str(builder.time_limit),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={"PATH": os.environ.get("PATH", "")})

    try:
        output, error = await asyncio.wait_for(process.communicate(), timeout)

    except TimeoutError:
        process.kill()
        await process.wait()
        return {}, f"Execution exceeded {timeout:.0f} seconds."

    if process.returncode != 0:
        return {}, error.decode(errors="replace")[-builder.error_tail:]

    return json.loads(output.decode().splitlines()[-1]), ""
