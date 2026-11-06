# products.py Small Owners - Inventory Tool

A small command-line inventory tool for a shop owner. Products are stored in a
plain JSON file, so there is no database and no setup, just Python.

Every product has four fields: an `id`, a `name`, a `price`, and a `quantity`.

## Requirements

- Python 3 (standard library only, nothing to install)

## The data file

Products are stored in `products.json` in the same folder as the script. The
file is created automatically when the first product is added; until then the
tool treats a missing file as an empty store. Ids are never reused, even after
a delete, so an id always refers to the same product.

```json
{
  "next_id": 3,
  "products": [
    {
      "id": 1,
      "name": "Notebook",
      "price": "4.50",
      "quantity": 12
    }
  ]
}
```

To work with a different file, pass `--file` before the command:

```
python3 products.py --file mydata.json list
```

## Commands

### Add a product

```
python3 products.py add --name Notebook --price 4.5 --quantity 10
```

```json
{
  "id": 1,
  "name": "Notebook",
  "price": "4.50",
  "quantity": 10
}
```

The new product is printed as JSON. Prices are always saved and shown as
strings with two decimals, and ids are assigned automatically.

### List all products

```
python3 products.py list
```

```json
[
  {
    "id": 1,
    "name": "Notebook",
    "price": "4.50",
    "quantity": 10
  },
  {
    "id": 2,
    "name": "Pencil",
    "price": "1.25",
    "quantity": 5
  }
]
```

### Get one product by id

```
python3 products.py get 1
```

```json
{
  "id": 1,
  "name": "Notebook",
  "price": "4.50",
  "quantity": 10
}
```

### Update a product by id

Only the fields you pass are changed; the rest stay as they are.

```
python3 products.py update 1 --quantity 12
```

```json
{
  "id": 1,
  "name": "Notebook",
  "price": "4.50",
  "quantity": 12
}
```

### Delete a product by id

Deleting needs a `--yes` flag to confirm.

```
python3 products.py delete 2 --yes
```

```json
{"deleted_id": 2}
```

Only the id of the deleted product is printed. After this, `list` shows only
the Notebook:

```json
[
  {
    "id": 1,
    "name": "Notebook",
    "price": "4.50",
    "quantity": 12
  }
]
```

## Low stock alerts

In my practicum I worked on a supply chain risk project. The whole idea was to
catch a supply problem early, before it turns into real damage. This tool uses
the same idea for a small shop owner: instead of finding out a product is gone
when a customer asks for it, `lowstock` points at the products that are running
out, so they can reorder while it is still cheap and easy.

The command prints every product whose quantity is at or below the threshold,
sorted by quantity first and then by id — the most urgent products appear
first. The file is never changed by this command.

```
python3 products.py lowstock --threshold 5
```

```json
[
  {
    "id": 3,
    "name": "Eraser",
    "price": "0.99",
    "quantity": 0
  },
  {
    "id": 2,
    "name": "Pencil",
    "price": "1.25",
    "quantity": 4
  }
]
```

The Notebook (quantity 12) is above the threshold, so it is not listed. If
nothing is low on stock, the command prints `[]`.

## Input rules

- **price** — 0 or more, at most 2 decimal places, no `$` sign; stored and
  displayed as a string with two decimals (`4.5` becomes `"4.50"`)
- **quantity** — a whole number, 0 or more, no decimals, no negatives
- **name** — must not be empty; spaces at the ends are trimmed and the rest is
  stored exactly as typed

## Errors and exit codes

Every failure prints one short `error:` line and never modifies the data file.

| Exit code | Meaning                                                       |
| --------- | ------------------------------------------------------------- |
| 0         | success                                                        |
| 1         | product id not found, or the data file is missing or broken   |
| 2         | wrong command or wrong values (bad price, quantity, name, id) |

Examples:

```
$ python3 products.py get 99
error: product 99 not found          (exit 1)

$ python3 products.py add --name Bad --price -5 --quantity 1
error: argument --price: price must be 0 or a positive number with at most 2 decimal places        (exit 2)

$ python3 products.py delete 1
error: use --yes to confirm deleting product 1        (exit 2)
```
