"""Validate and apply model patches without calling any model."""

from functools import reduce

from data_model.BusinessProblemSpec import (
    BusinessConstraint,
    BusinessProblemSpec,
    ConstraintHardness,
    InformationStatus,
)
from data_model.MathematicalStructure import (
    DataBinding,
    MathematicalStructure,
    NamedItem,
)
from data_model.ModelPatch import ModelPatch, PatchOperation


def key(item: NamedItem | DataBinding) -> str:
    """Return the name identifying an element of the spec."""
    return item.symbol if isinstance(item, DataBinding) else item.name

def operation_errors(
    spec: MathematicalStructure,
    operation: PatchOperation,
) -> list[str]:
    """Explain why an operation cannot be applied to the spec."""

    if operation.target == "objective":
        directions = ("minimize", "maximize")
        valid = operation.action == "replace" and operation.name in directions
        return [] if valid else [
            ("An objective operation must use action replace and name "
             "minimize or maximize.")]

    names = {key(item) for item in getattr(spec, operation.target)}

    if operation.action == "add" and operation.name in names:
        return [(f"{operation.target} already contains {operation.name}; "
                 "use replace.")]

    if operation.action != "add" and operation.name not in names:
        return [(f"{operation.target} has no element {operation.name}; "
                 f"existing names: {sorted(names)}.")]

    return []


def spec_errors(spec: MathematicalStructure) -> list[str]:
    """List the parameters without data or value and the dangling bindings."""
    bound = {binding.symbol for binding in spec.data_bindings}
    symbols = {item.name for item in spec.sets + spec.parameters}

    unvalued = [f"Parameter {p.name} has no data binding and no value in "
                "its description; state its value or ask the user for it."
                for p in spec.parameters
                if p.name not in bound
                and not any(char.isdigit() for char in p.description)]
    dangling = [f"Data binding {b.symbol} refers to no set or parameter; "
                "remove it." for b in spec.data_bindings
                if b.symbol not in symbols]

    return unvalued + dangling


def patch_errors(spec: MathematicalStructure, patch: ModelPatch) -> list[str]:
    """List the problems preventing a patch from being applied.

    Beyond invalid operations, a patch must not leave a parameter without
    data or value, nor a binding without symbol, that did not exist before.
    """
    errors = [error for operation in patch.operations
              for error in operation_errors(spec, operation)]

    if errors:
        return errors

    before = set(spec_errors(spec))
    return [error for error in spec_errors(apply_patch(spec, patch))
            if error not in before]


def apply_operation(
    spec: MathematicalStructure,
    operation: PatchOperation,
) -> MathematicalStructure:
    """Return a copy of the spec with one operation applied."""
    if operation.target == "objective":
        return spec.model_copy(update={
            "direction": operation.name,
            "objective": operation.description,
        })
    item: NamedItem | DataBinding = (
        DataBinding(symbol=operation.name, column=operation.description)
        if operation.target == "data_bindings"
        else NamedItem(name=operation.name,
                       description=operation.description))
    items = getattr(spec, operation.target)
    if operation.action == "add":
        updated = [*items, item]
    elif operation.action == "remove":
        updated = [old for old in items if key(old) != operation.name]
    else:
        updated = [item if key(old) == operation.name else old
                   for old in items]
    return spec.model_copy(update={operation.target: updated})


def apply_patch(
    spec: MathematicalStructure,
    patch: ModelPatch,
) -> MathematicalStructure:
    """Return a copy of the spec with every operation applied in order."""
    return reduce(apply_operation, patch.operations, spec)


def sync_rules(
    business: BusinessProblemSpec,
    patch: ModelPatch,
) -> BusinessProblemSpec:
    """Mirror the constraint changes of a patch in the business rules."""
    rules = {rule.id: rule for rule in business.business_constraints}

    for operation in patch.operations:
        if operation.target != "constraints":
            continue
        previous = rules.pop(operation.name, None)
        if operation.action != "remove":
            rules[operation.name] = BusinessConstraint(
                id=operation.name,
                original_text=patch.summary,
                hardness=(previous.hardness if previous is not None
                          else ConstraintHardness.hard),
                status=InformationStatus.confirmed)

    return business.model_copy(
        update={"business_constraints": list(rules.values())})
