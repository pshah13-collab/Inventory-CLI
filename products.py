import argparse
import json
import os
import re
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

PRICE_RE = re.compile(r"\d+(\.\d{1,2})?")


def parse_price(value):
    text = value.strip()
    if "$" in text:
        raise argparse.ArgumentTypeError("price must not include a $ sign")
    if not PRICE_RE.fullmatch(text):
        raise argparse.ArgumentTypeError(
            "price must be 0 or a positive number with at most 2 decimal places"
        )
    return str(Decimal(text).quantize(Decimal("0.01")))


def parse_quantity(value):
    text = value.strip()
    if not re.fullmatch(r"\d+", text):
        raise argparse.ArgumentTypeError(
            "quantity must be a whole number, 0 or more, with no decimals"
        )
    return int(text)


def parse_name(value):
    text = value.strip()
    if not text:
        raise argparse.ArgumentTypeError("name must not be empty")
    return text


def load_store(db_file):
    if not db_file.exists():
        return {"next_id": 1, "products": []}
    try:
        with db_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except OSError:
        print(f"error: cannot read {db_file.name}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"error: {db_file.name} is not valid JSON", file=sys.stderr)
        sys.exit(1)
    if isinstance(data, list):
        return {
            "next_id": max((p["id"] for p in data), default=0) + 1,
            "products": data,
        }
    if (
        isinstance(data, dict)
        and isinstance(data.get("next_id"), int)
        and isinstance(data.get("products"), list)
    ):
        return data
    print(f"error: {db_file.name} is not a valid products file", file=sys.stderr)
    sys.exit(1)


def save_store(db_file, store):
    payload = json.dumps(store, indent=2) + "\n"
    fd = None
    tmp_name = None
    try:
        fd, tmp_name = tempfile.mkstemp(
            dir=db_file.parent, prefix=db_file.name + ".", suffix=".tmp"
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            fd = None
            f.write(payload)
        if db_file.exists():
            os.chmod(tmp_name, db_file.stat().st_mode & 0o777)
        else:
            os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, db_file)
        tmp_name = None
    except OSError:
        print(f"error: cannot write {db_file.name}", file=sys.stderr)
        sys.exit(1)
    finally:
        if fd is not None:
            os.close(fd)
        if tmp_name is not None:
            Path(tmp_name).unlink(missing_ok=True)


def find_product(products, product_id):
    for p in products:
        if p["id"] == product_id:
            return p
    return None


def print_json(data):
    print(json.dumps(data, indent=2))


def fail(message, code=1):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        print(f"error: {message}", file=sys.stderr)
        sys.exit(2)


def cmd_add(args):
    store = load_store(args.db_file)
    product = {
        "id": store["next_id"],
        "name": args.name,
        "price": args.price,
        "quantity": args.quantity,
    }
    store["products"].append(product)
    store["next_id"] += 1
    save_store(args.db_file, store)
    print_json(product)


def cmd_list(args):
    print_json(load_store(args.db_file)["products"])


def cmd_get(args):
    store = load_store(args.db_file)
    product = find_product(store["products"], args.id)
    if product is None:
        fail(f"product {args.id} not found")
    print_json(product)


def cmd_update(args):
    store = load_store(args.db_file)
    product = find_product(store["products"], args.id)
    if product is None:
        fail(f"product {args.id} not found")
    if args.name is not None:
        product["name"] = args.name
    if args.price is not None:
        product["price"] = args.price
    if args.quantity is not None:
        product["quantity"] = args.quantity
    save_store(args.db_file, store)
    print_json(product)


def cmd_delete(args):
    store = load_store(args.db_file)
    product = find_product(store["products"], args.id)
    if product is None:
        fail(f"product {args.id} not found")
    if not args.yes:
        fail(f"use --yes to confirm deleting product {args.id}", code=2)
    store["products"].remove(product)
    save_store(args.db_file, store)
    print(json.dumps({"deleted_id": product["id"]}))


def cmd_lowstock(args):
    store = load_store(args.db_file)
    low = [p for p in store["products"] if p["quantity"] <= args.threshold]
    low.sort(key=lambda p: (p["quantity"], p["id"]))
    print_json(low)


def build_parser():
    parser = Parser(description="Simple JSON inventory tool")
    parser.add_argument(
        "--file",
        default="products.json",
        help="path to the JSON data file (default: products.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a new product")
    add.add_argument("--name", type=parse_name, required=True)
    add.add_argument("--price", type=parse_price, required=True)
    add.add_argument("--quantity", type=parse_quantity, required=True)
    add.set_defaults(func=cmd_add)

    list_cmd = sub.add_parser("list", help="list all products")
    list_cmd.set_defaults(func=cmd_list)

    get = sub.add_parser("get", help="get a product by id")
    get.add_argument("id", type=int)
    get.set_defaults(func=cmd_get)

    update = sub.add_parser("update", help="update a product by id")
    update.add_argument("id", type=int)
    update.add_argument("--name", type=parse_name)
    update.add_argument("--price", type=parse_price)
    update.add_argument("--quantity", type=parse_quantity)
    update.set_defaults(func=cmd_update)

    delete = sub.add_parser("delete", help="delete a product by id")
    delete.add_argument("id", type=int)
    delete.add_argument("--yes", action="store_true")
    delete.set_defaults(func=cmd_delete)

    lowstock = sub.add_parser(
        "lowstock", help="list products with quantity at or below a threshold"
    )
    lowstock.add_argument("--threshold", type=parse_quantity, required=True)
    lowstock.set_defaults(func=cmd_lowstock)

    return parser


def main():
    args = build_parser().parse_args()
    args.db_file = Path(args.file)
    args.func(args)


if __name__ == "__main__":
    main()
