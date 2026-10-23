"""Wiring tests for the checkpoint guard in ``CNNPredictor``.

``predictor.py`` imports torch, so it cannot be imported in the torch-free
test environment. These tests parse its source instead, which is enough to
enforce the invariant that matters: the digest is verified before the
checkpoint is deserialised, with ``weights_only=True``.
"""

import ast
from pathlib import Path

PREDICTOR = Path(__file__).resolve().parents[1] / "src" / "models" / "predictor.py"


def load_tree():
    return ast.parse(PREDICTOR.read_text(encoding="utf-8"))


def find_class(tree, name):
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == name
    )


def find_method(class_node, name):
    return next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def call_lines(method, attribute):
    lines = []

    for node in ast.walk(method):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name == attribute:
                lines.append(node)

    return lines


def test_verification_precedes_torch_load():
    method = find_method(find_class(load_tree(), "CNNPredictor"), "load_model")

    verify_calls = call_lines(method, "read_verified_checkpoint")
    load_calls = call_lines(method, "load")

    assert verify_calls, "load_model does not read verified checkpoint bytes"
    assert load_calls, "load_model does not call torch.load"

    assert verify_calls[0].lineno < load_calls[0].lineno, (
        "checkpoint verification must run before torch.load"
    )


def test_torch_load_uses_weights_only():
    method = find_method(find_class(load_tree(), "CNNPredictor"), "load_model")

    load_call = call_lines(method, "load")[0]

    weights_only = [
        keyword for keyword in load_call.keywords
        if keyword.arg == "weights_only"
    ]

    assert weights_only, "torch.load must pass weights_only"
    assert isinstance(weights_only[0].value, ast.Constant)
    assert weights_only[0].value.value is True


def test_init_handles_integrity_failure_separately():
    init = find_method(find_class(load_tree(), "CNNPredictor"), "__init__")

    handled = [
        handler
        for node in ast.walk(init)
        if isinstance(node, ast.Try)
        for handler in node.handlers
        if isinstance(handler.type, ast.Name)
    ]

    names = {handler.type.id for handler in handled}

    assert "ModelIntegrityError" in names, (
        "__init__ must handle ModelIntegrityError explicitly"
    )
