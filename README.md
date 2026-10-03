# Warehouse Network Optimization — Take-Home Exercise

## Scenario

You are planning a regional distribution network. There are **16 candidate
warehouses** and **50 customers** (stores) that must be supplied.

- Opening a warehouse costs a **fixed cost** and gives it a fixed **capacity**
  (max total units it can ship).
- Each customer has a **demand** (units it needs).
- Shipping to a customer from a given warehouse has a **cost** (the number in
  the data is the cost of covering that customer's **entire** demand from that
  warehouse; if you cover half their demand from a warehouse, you pay half).

**Goal:** decide **which warehouses to open** and **how to assign customer
demand to open warehouses** so that **total cost (fixed + shipping) is
minimized**, without exceeding any warehouse's capacity.

A customer's demand **may be split across several warehouses**.

## Data files (`data/`)

All files are plain CSV, UTF-8, with a header row.

| File | Columns | Meaning |
|------|---------|---------|
| `warehouses.csv` | `warehouse_id, capacity, fixed_cost` | One row per candidate warehouse. |
| `customers.csv` | `customer_id, demand` | One row per customer. |
| `assignment_costs.csv` | `customer_id, warehouse_id, cost` | Tidy/long format: cost to serve **all** of `customer_id`'s demand from `warehouse_id`. 16 × 50 = 800 rows. |

`cap41_raw.txt` is the original OR-Library source file; you can ignore it.

## The optimization task


Minimize the total cost (fixed and variable costs).

Subject to:

1. Every customer fully served
2. Capacity respected
3. Only open warehouses used 

This indications are here to remove ambiguity about the rules. Any method that returns a valid, low-cost plan is
welcome.

## Getting started

`starter.py` loads the data with the Python standard library (no installs
needed) and prints a few sanity checks:

```
python3 starter.py
```
