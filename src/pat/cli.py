"""CLI interface for the Personal Asset Tracker."""

import argparse
import logging
import sys
from datetime import date

from pat.db import get_connection, init_schema
from pat.models import (
    AssetCategory,
    AssetCreate,
    AssetUpdate,
    AssetValueCreate,
)
from pat.repository import (
    add_value,
    create_asset,
    delete_asset,
    delete_value,
    get_asset,
    get_net_worth,
    get_values,
    list_assets,
    update_asset,
)
from pat.io import export_csv, export_json, import_csv, import_json

logger = logging.getLogger(__name__)


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print a simple aligned table to stdout."""
    if not rows:
        print("No results.")
        return

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*row))


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize the database."""
    conn = get_connection()
    init_schema(conn)
    conn.close()
    print("Database initialized.")


def cmd_asset_add(args: argparse.Namespace) -> None:
    """Add a new asset."""
    conn = get_connection()
    try:
        asset = create_asset(
            conn,
            AssetCreate(
                category=AssetCategory(args.category),
                name=args.name,
                description=args.description,
                acquired_date=(
                    date.fromisoformat(args.acquired_date)
                    if args.acquired_date
                    else None
                ),
            ),
        )
        print(f"Created asset #{asset.id}: {asset.name} [{asset.category}]")
    finally:
        conn.close()


def cmd_asset_list(args: argparse.Namespace) -> None:
    """List assets."""
    conn = get_connection()
    try:
        assets = list_assets(conn, category=args.category)
        headers = ["ID", "Category", "Name", "Acquired", "Disposed"]
        rows = [
            [
                str(a.id),
                a.category,
                a.name,
                str(a.acquired_date or ""),
                str(a.disposed_date or ""),
            ]
            for a in assets
        ]
        _print_table(headers, rows)
    finally:
        conn.close()


def cmd_asset_show(args: argparse.Namespace) -> None:
    """Show asset details."""
    conn = get_connection()
    try:
        asset = get_asset(conn, args.id)
        if asset is None:
            print(f"Asset #{args.id} not found.", file=sys.stderr)
            sys.exit(1)
        print(f"ID:           {asset.id}")
        print(f"Category:     {asset.category}")
        print(f"Name:         {asset.name}")
        print(f"Description:  {asset.description or ''}")
        print(f"Acquired:     {asset.acquired_date or ''}")
        print(f"Disposed:     {asset.disposed_date or ''}")
        print(f"Created:      {asset.created_at}")
        print(f"Updated:      {asset.updated_at}")
    finally:
        conn.close()


def cmd_asset_update(args: argparse.Namespace) -> None:
    """Update an asset."""
    conn = get_connection()
    try:
        update = AssetUpdate(
            name=args.name,
            description=args.description,
            disposed_date=(
                date.fromisoformat(args.disposed_date) if args.disposed_date else None
            ),
        )
        asset = update_asset(conn, args.id, update)
        if asset is None:
            print(f"Asset #{args.id} not found.", file=sys.stderr)
            sys.exit(1)
        print(f"Updated asset #{asset.id}: {asset.name}")
    finally:
        conn.close()


def cmd_asset_delete(args: argparse.Namespace) -> None:
    """Delete an asset."""
    conn = get_connection()
    try:
        if delete_asset(conn, args.id):
            print(f"Deleted asset #{args.id}.")
        else:
            print(f"Asset #{args.id} not found.", file=sys.stderr)
            sys.exit(1)
    finally:
        conn.close()


def cmd_value_add(args: argparse.Namespace) -> None:
    """Add a value record."""
    conn = get_connection()
    try:
        val = add_value(
            conn,
            AssetValueCreate(
                asset_id=args.asset_id,
                value_date=date.fromisoformat(args.date),
                amount=args.amount,
                currency=args.currency,
                note=args.note,
            ),
        )
        print(
            f"Recorded value #{val.id}: "
            f"{val.currency} {val.amount:,.2f} on {val.value_date}"
        )
    finally:
        conn.close()


def cmd_value_list(args: argparse.Namespace) -> None:
    """List values for an asset."""
    conn = get_connection()
    try:
        values = get_values(
            conn,
            args.asset_id,
            start=(date.fromisoformat(args.start) if args.start else None),
            end=date.fromisoformat(args.end) if args.end else None,
        )
        headers = ["ID", "Date", "Amount", "Currency", "Note"]
        rows = [
            [
                str(v.id),
                str(v.value_date),
                f"{v.amount:,.2f}",
                v.currency,
                v.note or "",
            ]
            for v in values
        ]
        _print_table(headers, rows)
    finally:
        conn.close()


def cmd_value_delete(args: argparse.Namespace) -> None:
    """Delete a value record."""
    conn = get_connection()
    try:
        if delete_value(conn, args.id):
            print(f"Deleted value #{args.id}.")
        else:
            print(f"Value #{args.id} not found.", file=sys.stderr)
            sys.exit(1)
    finally:
        conn.close()


def cmd_report_net_worth(args: argparse.Namespace) -> None:
    """Show net worth report."""
    conn = get_connection()
    try:
        as_of = date.fromisoformat(args.as_of) if args.as_of else None
        summary = get_net_worth(conn, as_of=as_of)
        print(f"Net Worth as of {summary.as_of}")
        print(f"{'=' * 50}")
        headers = ["Category", "Assets", "Total"]
        rows = [
            [c.category, str(c.asset_count), f"{c.total:,.2f}"]
            for c in summary.categories
        ]
        _print_table(headers, rows)
        print(f"{'=' * 50}")
        print(f"TOTAL: {summary.currency} {summary.total:,.2f}")
    finally:
        conn.close()


def cmd_report_history(args: argparse.Namespace) -> None:
    """Show value history."""
    conn = get_connection()
    try:
        if args.asset_id:
            assets_to_show = [get_asset(conn, args.asset_id)]
        else:
            assets_to_show = list_assets(conn, category=args.category)

        headers = ["Asset", "Date", "Amount", "Currency", "Note"]
        rows: list[list[str]] = []
        for asset in assets_to_show:
            if asset is None:
                continue
            values = get_values(conn, asset.id)
            for v in values:
                rows.append(
                    [
                        asset.name,
                        str(v.value_date),
                        f"{v.amount:,.2f}",
                        v.currency,
                        v.note or "",
                    ]
                )
        _print_table(headers, rows)
    finally:
        conn.close()


def cmd_import(args: argparse.Namespace) -> None:
    """Import from file."""
    conn = get_connection()
    try:
        fmt = args.format
        if fmt is None:
            if args.file.endswith(".json"):
                fmt = "json"
            elif args.file.endswith(".csv"):
                fmt = "csv"
            else:
                print("Cannot detect format. Use --format.", file=sys.stderr)
                sys.exit(1)

        if fmt == "json":
            count = import_json(conn, args.file)
        else:
            count = import_csv(conn, args.file)
        print(f"Imported {count} assets.")
    finally:
        conn.close()


def cmd_export(args: argparse.Namespace) -> None:
    """Export to file."""
    conn = get_connection()
    try:
        fmt = args.format
        if fmt is None:
            if args.file.endswith(".json"):
                fmt = "json"
            elif args.file.endswith(".csv"):
                fmt = "csv"
            else:
                print("Cannot detect format. Use --format.", file=sys.stderr)
                sys.exit(1)

        as_of = date.fromisoformat(args.as_of) if args.as_of else None
        if fmt == "json":
            count = export_json(conn, args.file, as_of=as_of)
        else:
            count = export_csv(conn, args.file, as_of=as_of)
        print(f"Exported {count} assets.")
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="pat",
        description="Personal Asset Tracker",
    )
    subparsers = parser.add_subparsers(dest="command")

    # init
    subparsers.add_parser("init", help="Initialize the database")

    # asset
    asset_parser = subparsers.add_parser("asset", help="Manage assets")
    asset_sub = asset_parser.add_subparsers(dest="asset_command")

    # asset add
    add_p = asset_sub.add_parser("add", help="Add an asset")
    add_p.add_argument(
        "--category",
        required=True,
        choices=[c.value for c in AssetCategory],
    )
    add_p.add_argument("--name", required=True)
    add_p.add_argument("--description")
    add_p.add_argument("--acquired-date")

    # asset list
    list_p = asset_sub.add_parser("list", help="List assets")
    list_p.add_argument("--category")

    # asset show
    show_p = asset_sub.add_parser("show", help="Show asset details")
    show_p.add_argument("id", type=int)

    # asset update
    upd_p = asset_sub.add_parser("update", help="Update an asset")
    upd_p.add_argument("id", type=int)
    upd_p.add_argument("--name")
    upd_p.add_argument("--description")
    upd_p.add_argument("--disposed-date")

    # asset delete
    del_p = asset_sub.add_parser("delete", help="Delete an asset")
    del_p.add_argument("id", type=int)

    # value
    value_parser = subparsers.add_parser("value", help="Manage asset values")
    value_sub = value_parser.add_subparsers(dest="value_command")

    # value add
    vadd_p = value_sub.add_parser("add", help="Record a value")
    vadd_p.add_argument("asset_id", type=int)
    vadd_p.add_argument("--date", required=True)
    vadd_p.add_argument("--amount", required=True, type=float)
    vadd_p.add_argument("--currency", default="USD")
    vadd_p.add_argument("--note")

    # value list
    vlist_p = value_sub.add_parser("list", help="List values")
    vlist_p.add_argument("asset_id", type=int)
    vlist_p.add_argument("--start")
    vlist_p.add_argument("--end")

    # value delete
    vdel_p = value_sub.add_parser("delete", help="Delete a value")
    vdel_p.add_argument("id", type=int)

    # report
    report_parser = subparsers.add_parser("report", help="View reports")
    report_sub = report_parser.add_subparsers(dest="report_command")

    nw_p = report_sub.add_parser("net-worth", help="Net worth summary")
    nw_p.add_argument("--as-of")

    hist_p = report_sub.add_parser("history", help="Value history")
    hist_p.add_argument("--category")
    hist_p.add_argument("--asset-id", type=int)

    # import
    imp_p = subparsers.add_parser("import", help="Import from file")
    imp_p.add_argument("file")
    imp_p.add_argument("--format", choices=["json", "csv"])

    # export
    exp_p = subparsers.add_parser("export", help="Export to file")
    exp_p.add_argument("file")
    exp_p.add_argument("--format", choices=["json", "csv"])
    exp_p.add_argument("--as-of")

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    dispatch = {
        "init": cmd_init,
        "import": cmd_import,
        "export": cmd_export,
    }

    if args.command in dispatch:
        dispatch[args.command](args)
    elif args.command == "asset":
        asset_dispatch = {
            "add": cmd_asset_add,
            "list": cmd_asset_list,
            "show": cmd_asset_show,
            "update": cmd_asset_update,
            "delete": cmd_asset_delete,
        }
        if args.asset_command in asset_dispatch:
            asset_dispatch[args.asset_command](args)
        else:
            parser.parse_args(["asset", "--help"])
    elif args.command == "value":
        value_dispatch = {
            "add": cmd_value_add,
            "list": cmd_value_list,
            "delete": cmd_value_delete,
        }
        if args.value_command in value_dispatch:
            value_dispatch[args.value_command](args)
        else:
            parser.parse_args(["value", "--help"])
    elif args.command == "report":
        report_dispatch = {
            "net-worth": cmd_report_net_worth,
            "history": cmd_report_history,
        }
        if args.report_command in report_dispatch:
            report_dispatch[args.report_command](args)
        else:
            parser.parse_args(["report", "--help"])
