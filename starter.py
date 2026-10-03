"""Starter loader for the warehouse network optimization exercise.

Pure standard library — no installs needed. Loads the data, runs a few sanity
checks, and shows how to look up costs. Build your model on top of this, or
ignore it and load the CSV files however you prefer.
"""
import csv
from pathlib import Path

DATA = Path(__file__).parent / "data"


def load_csv():
    with (DATA / "warehouses.csv").open() as f:
        warehouses = {
            r["warehouse_id"]: {
                "capacity": int(r["capacity"]),
                "fixed_cost": float(r["fixed_cost"]),
            }
            for r in csv.DictReader(f)
        }

    with (DATA / "customers.csv").open() as f:
        customers = {r["customer_id"]: {"demand": int(r["demand"])} for r in csv.DictReader(f)}

    # cost[(customer_id, warehouse_id)] -> cost to serve ALL of that customer from that warehouse
    cost = {}
    with (DATA / "assignment_costs.csv").open() as f:
        for r in csv.DictReader(f):
            cost[(r["customer_id"], r["warehouse_id"])] = float(r["cost"])

    return warehouses, customers, cost


def main():
    warehouses, customers, cost = load_csv()

    total_capacity = sum(w["capacity"] for w in warehouses.values())
    total_demand = sum(c["demand"] for c in customers.values())

    print(f"{len(warehouses)} warehouses, {len(customers)} customers")
    print(f"total capacity = {total_capacity:,}")
    print(f"total demand   = {total_demand:,}")
    print(f"slack          = {total_capacity - total_demand:,}")
    print()
    print("Example lookups:")
    print("  cost to serve all of C01 from W11 =", cost[("C01", "W11")])
    print("  demand of C01                     =", customers["C01"]["demand"])
    print("  capacity/fixed_cost of W11        =", warehouses["W11"])


if __name__ == "__main__":
    main()
