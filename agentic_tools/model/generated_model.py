import csv
from pathlib import Path
import math

def load_data(data_dir: Path) -> dict:
    # Load sets
    with (data_dir / "warehouses.csv").open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
        W = list(dict.fromkeys([row["warehouse_id"] for row in rows]))

    with (data_dir / "customers.csv").open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
        C = list(dict.fromkeys([row["customer_id"] for row in rows]))

    # Load parameters
    with (data_dir / "warehouses.csv").open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
        fixed_cost_w = {row["warehouse_id"]: float(row["fixed_cost"]) for row in rows}
        capacity_w = {row["warehouse_id"]: float(row["capacity"]) for row in rows}

    with (data_dir / "customers.csv").open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
        demand_c = {row["customer_id"]: float(row["demand"]) for row in rows}

    with (data_dir / "assignment_costs.csv").open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
        cost_cw = {(row["customer_id"], row["warehouse_id"]): float(row["cost"]) for row in rows}

    return {
        "W": W,
        "C": C,
        "fixed_cost_w": fixed_cost_w,
        "capacity_w": capacity_w,
        "demand_c": demand_c,
        "cost_cw": cost_cw,
    }

from ortools.linear_solver import pywraplp

def build_model(data: dict) -> tuple[pywraplp.Solver, dict]:
    solver = pywraplp.Solver.CreateSolver("HIGHS")

    x_w = {w: solver.BoolVar(f"x_w[{w}]") for w in data["W"]}
    y_cw = {(c, w): solver.NumVar(0, 1, f"y_cw[{c},{w}]") for c in data["C"] for w in data["W"]}

    solver.Minimize(
        solver.Sum([data["fixed_cost_w"][w] * x_w[w] for w in data["W"]]) +
        solver.Sum([data["cost_cw"][c, w] * y_cw[c, w] for c in data["C"] for w in data["W"]])
    )

    for w in data["W"]:
        solver.Add(
            solver.Sum([data["demand_c"][c] * y_cw[c, w] for c in data["C"]]) <= data["capacity_w"][w] * x_w[w],
            f"RULE_001_capacity_{w}"
        )

    for c in data["C"]:
        solver.Add(
            solver.Sum([y_cw[c, w] for w in data["W"]]) == 1,
            f"RULE_004_demand_satisfaction_{c}"
        )

    solver.Add(
        solver.Sum([x_w[w] for w in data["W"]]) <= 12,
        "RULE_005_max_warehouses"
    )

    return solver, {"x_w": x_w, "y_cw": y_cw}
