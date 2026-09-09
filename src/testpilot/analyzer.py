# MIT License
# Copyright (c) 2024 Maharshi Soni

"""AST-based Python source code analyzer for TestPilot AI.

Parses Python source files into structured representations used for
test generation. Extracts function signatures, type annotations,
docstrings, complexity metrics, and class hierarchies.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path
from typing import Sequence

from testpilot.models import (
    ClassInfo,
    FunctionInfo,
    ModuleAnalysis,
    ParameterInfo,
    TypeCategory,
)


# ---------------------------------------------------------------------------
# Type-category inference
# ---------------------------------------------------------------------------

_ANNOTATION_MAP: dict[str, TypeCategory] = {
    "int": TypeCategory.INTEGER,
    "float": TypeCategory.FLOAT,
    "str": TypeCategory.STRING,
    "bool": TypeCategory.BOOLEAN,
    "list": TypeCategory.LIST,
    "List": TypeCategory.LIST,
    "dict": TypeCategory.DICT,
    "Dict": TypeCategory.DICT,
    "set": TypeCategory.SET,
    "Set": TypeCategory.SET,
    "tuple": TypeCategory.TUPLE,
    "Tuple": TypeCategory.TUPLE,
    "None": TypeCategory.NONE,
    "NoneType": TypeCategory.NONE,
}


def _infer_type_category(annotation_str: str | None) -> TypeCategory:
    """Map an annotation string to a broad TypeCategory."""
    if annotation_str is None:
        return TypeCategory.UNKNOWN
    base = annotation_str.split("[")[0].strip()
    if base.startswith("Optional"):
        return TypeCategory.OPTIONAL
    return _ANNOTATION_MAP.get(base, TypeCategory.CUSTOM)


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _annotation_to_str(node: ast.expr | None) -> str | None:
    """Convert an AST annotation node to a human-readable string."""
    if node is None:
        return None
    return ast.unparse(node)


def _default_to_str(node: ast.expr | None) -> str | None:
    """Convert an AST default-value node to a string."""
    if node is None:
        return None
    return ast.unparse(node)


def _decorator_names(decorators: list[ast.expr]) -> list[str]:
    """Extract decorator name strings from decorator_list nodes."""
    names: list[str] = []
    for dec in decorators:
        names.append(ast.unparse(dec))
    return names


def _cyclomatic_complexity(node: ast.AST) -> int:
    """Estimate cyclomatic complexity of a function body.

    Counts decision points: if, for, while, except, with, boolean ops,
    assert, comprehensions.
    """
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.IfExp)):
            complexity += 1
        elif isinstance(child, (ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, (ast.While,)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, (ast.With, ast.AsyncWith)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            # each 'and' / 'or' adds a branch
            complexity += len(child.values) - 1
        elif isinstance(child, ast.Assert):
            complexity += 1
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            complexity += 1
    return complexity


# ---------------------------------------------------------------------------
# Parameter extraction
# ---------------------------------------------------------------------------

def _extract_parameters(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ParameterInfo]:
    """Extract parameter information from a function definition."""
    params: list[ParameterInfo] = []
    args = func_node.args

    # Compute default alignment: defaults are right-aligned with positional args
    num_positional = len(args.args)
    num_defaults = len(args.defaults)
    default_offset = num_positional - num_defaults

    for idx, arg in enumerate(args.args):
        ann_str = _annotation_to_str(arg.annotation)
        default_idx = idx - default_offset
        default_val = (
            _default_to_str(args.defaults[default_idx])
            if default_idx >= 0
            else None
        )
        is_optional = default_val is not None or (
            ann_str is not None and ann_str.startswith("Optional")
        )
        params.append(
            ParameterInfo(
                name=arg.arg,
                annotation=ann_str,
                default=default_val,
                type_category=_infer_type_category(ann_str),
                is_optional=is_optional,
            )
        )

    # *args
    if args.vararg:
        ann_str = _annotation_to_str(args.vararg.annotation)
        params.append(
            ParameterInfo(
                name=f"*{args.vararg.arg}",
                annotation=ann_str,
                type_category=_infer_type_category(ann_str),
            )
        )

    # keyword-only
    for idx, arg in enumerate(args.kwonlyargs):
        ann_str = _annotation_to_str(arg.annotation)
        default_val = _default_to_str(args.kw_defaults[idx]) if args.kw_defaults[idx] else None
        params.append(
            ParameterInfo(
                name=arg.arg,
                annotation=ann_str,
                default=default_val,
                type_category=_infer_type_category(ann_str),
                is_optional=default_val is not None,
            )
        )

    # **kwargs
    if args.kwarg:
        ann_str = _annotation_to_str(args.kwarg.annotation)
        params.append(
            ParameterInfo(
                name=f"**{args.kwarg.arg}",
                annotation=ann_str,
                type_category=_infer_type_category(ann_str),
            )
        )

    return params


# ---------------------------------------------------------------------------
# Source extraction
# ---------------------------------------------------------------------------

def _extract_source(source_lines: list[str], node: ast.AST) -> str:
    """Extract the source code of an AST node from the file's lines."""
    start = getattr(node, "lineno", 1) - 1
    end = getattr(node, "end_lineno", start + 1)
    snippet = "\n".join(source_lines[start:end])
    return textwrap.dedent(snippet)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_function(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    module_path: str,
    source_lines: list[str],
    class_name: str | None = None,
) -> FunctionInfo:
    """Analyze a single function/method AST node.

    Parameters
    ----------
    func_node:
        The AST node for the function definition.
    module_path:
        Dotted module path (e.g. ``"mypackage.utils"``).
    source_lines:
        Full source file split into lines (for source extraction).
    class_name:
        If the function is a method, the enclosing class name.

    Returns
    -------
    FunctionInfo
        Structured representation of the function.
    """
    decorators = _decorator_names(func_node.decorator_list)
    params = _extract_parameters(func_node)
    docstring = ast.get_docstring(func_node)
    return_ann = _annotation_to_str(func_node.returns)

    is_static = "staticmethod" in decorators
    is_classmethod = "classmethod" in decorators
    is_property = "property" in decorators
    is_method = class_name is not None

    return FunctionInfo(
        name=func_node.name,
        module_path=module_path,
        lineno=func_node.lineno,
        end_lineno=func_node.end_lineno,
        docstring=docstring,
        parameters=params,
        return_annotation=return_ann,
        decorators=decorators,
        is_method=is_method,
        is_static=is_static,
        is_classmethod=is_classmethod,
        is_property=is_property,
        class_name=class_name,
        source_code=_extract_source(source_lines, func_node),
        complexity=_cyclomatic_complexity(func_node),
    )


def analyze_class(
    class_node: ast.ClassDef,
    module_path: str,
    source_lines: list[str],
) -> ClassInfo:
    """Analyze a single class AST node and its methods.

    Parameters
    ----------
    class_node:
        The AST node for the class definition.
    module_path:
        Dotted module path.
    source_lines:
        Full source file split into lines.

    Returns
    -------
    ClassInfo
        Structured representation including all methods.
    """
    bases = [ast.unparse(b) for b in class_node.bases]
    docstring = ast.get_docstring(class_node)
    decorators = _decorator_names(class_node.decorator_list)

    methods: list[FunctionInfo] = []
    for item in class_node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(
                analyze_function(item, module_path, source_lines, class_name=class_node.name)
            )

    return ClassInfo(
        name=class_node.name,
        module_path=module_path,
        lineno=class_node.lineno,
        end_lineno=class_node.end_lineno,
        docstring=docstring,
        bases=bases,
        methods=methods,
        decorators=decorators,
    )


def analyze_module(file_path: Path) -> ModuleAnalysis:
    """Analyze a complete Python module file.

    Parameters
    ----------
    file_path:
        Filesystem path to the ``.py`` file.

    Returns
    -------
    ModuleAnalysis
        Full structured analysis of the module.
    """
    source = file_path.read_text(encoding="utf-8")
    source_lines = source.splitlines()
    module_name = file_path.stem

    result = ModuleAnalysis(
        file_path=str(file_path),
        module_name=module_name,
        total_lines=len(source_lines),
    )

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        result.parse_errors.append(f"SyntaxError: {exc}")
        return result

    # Imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                result.imports.append(f"{module}.{alias.name}")

    # Top-level functions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.functions.append(
                analyze_function(node, module_name, source_lines)
            )
        elif isinstance(node, ast.ClassDef):
            cls = analyze_class(node, module_name, source_lines)
            result.classes.append(cls)

    return result


def analyze_paths(paths: Sequence[Path]) -> list[ModuleAnalysis]:
    """Analyze multiple Python files.

    Parameters
    ----------
    paths:
        Iterable of ``.py`` file paths.

    Returns
    -------
    list[ModuleAnalysis]
        One analysis per file.
    """
    results: list[ModuleAnalysis] = []
    for p in paths:
        if p.suffix == ".py" and p.is_file():
            results.append(analyze_module(p))
    return results
