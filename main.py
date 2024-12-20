__author__ = "8030456, Schuppan, 8404886, Kraus"

from dataclasses import dataclass, field
from datetime import datetime

import shell
from util import Util


@dataclass
class FoodItem:
    name: str
    type: str
    categories: set[str]
    price: int  # In cents.


class FoodItems:
    def __init__(self, filename: str):
        self.__items = []
        with open(filename, "r") as file:
            for i, line in enumerate(file):
                if i == 0 or line == "":
                    continue
                cols = line.removesuffix("\n").split(";")
                if len(cols) != 4:
                    raise Exception(
                        f"line {i}: expected semicolon- separated \
    CSV with 4 columns (name, type, category, price)"
                    )
                categories = set(s.strip() for s in cols[2].split(","))
                price = 0.0
                try:
                    price = float(cols[3].replace(",", ".")) * 100
                except ValueError:
                    raise Exception(
                        f"line {i}: expected price \
    (3rd column) to be a floating-point number"
                    )
                if price % 1 != 0:
                    raise Exception(
                        f"line {i}: expected price (3rd column) to be \
    at most accurate to the 0.01 decimal place (cents)"
                    )
                price = int(price)
                self.__items.append(
                    FoodItem(cols[0], cols[1], categories, price)
                )

    def __iter__(self):
        return iter(self.__items)

    def __getitem__(self, i):
        return self.__items[i]

    def __len__(self):
        return len(self.__items)


@dataclass
class SpecialRequest:
    request: str
    charge: int  # In cents.


@dataclass
class Order:
    time: datetime
    food_item: FoodItem
    special_requests: list[SpecialRequest]

    def amount(self) -> int:
        """Returns the total amount in cents."""
        return self.food_item.price + sum(
            r.charge for r in self.special_requests
        )


@dataclass
class Rescindment:
    time: datetime
    item_id: int
    price: int

    def amount(self) -> int:
        """Returns the total amount in cents."""
        return -self.price


@dataclass
class Table:
    id: str
    orders: list[Order | Rescindment] = field(default_factory=list)

    def amount(self) -> int:
        """Returns the total amount in cents."""
        return sum(o.amount() for o in self.orders)

    def orders(self) -> str:
        res = ""
        for i, order in enumerate(self.orders):
            if isinstance(order, Order):
                res += f" {i+1}. {order.food_item.name} \
+{order.food_item.price/100}€\n"
                for req in order.special_requests:
                    res += f"  + {req.request} \
({req.charge/100}€)\n"
            elif isinstance(order, Rescindment):
                res += f" {i+1}. Rescind order no. \
{order.item_id+1} -{order.price/100}€\n"
            else:
                raise ValueError
        res += f"Total: {self.amount()/100}€\n"
        return res


class App(shell.Shell):
    def __init__(self, food_items_filename):
        super().__init__()
        self.food_items = FoodItems(food_items_filename)
        self.tables: dict[str, Table] = {}
        self.curr_table = None


def run():
    app = App("food.csv")

    def cmd_table(self, params: list[object]) -> None:
        """Switches to a table with the specified ID. Creates
        a new table if necessary."""
        table = params[0]
        if (
            self.curr_table is not None
            and self.tables[self.curr_table] is not None
            and table == self.curr_table
        ):
            print(f"Table {table} already selected.")
            return
        new = ""
        if table not in self.tables:
            new = "new "
            self.tables[table] = Table(table)
        print(f'Switched to {new}table "{table}".')
        self.curr_table = table
        self.set_prompt_prefix([f"table={table}"])

    def cmd_tables(self, params: list[object]) -> None:
        """Lists all existing tables and their current orders
        and total amounts."""
        if len(self.tables) == 0:
            print("No tables.")
        else:
            print("Tables:")
            rows = []
            for name in sorted(self.tables.keys()):
                table = self.tables[name]
                orders = len(table.orders) if table.orders else "no"
                plural = "" if len(table.orders) == 1 else "s"
                rows.append(
                    [
                        f" * {name}",
                        f"{orders} order{plural}",
                        f"{table.amount()/100}€",
                    ]
                )
            print(Util.column_align(rows, sep="  "))

    def cmd_list(self, params: list[object]) -> None:
        """Lists all food items."""
        print("Food items:")
        rows = [["No.", "Name", "Type", "Tags", "Price"]]
        for i, item in enumerate(self.food_items):
            search_str = f"{item.name} {item.type} {item.categories}"
            if params[0] is not None:
                if params[0].lower() not in search_str.lower():
                    continue
            rows.append(
                [
                    f" {i+1}.",
                    item.name,
                    item.type,
                    ",".join(item.categories),
                    f"{item.price/100}€",
                ]
            )
        print(Util.column_align(rows, sep="  "))

    def cmd_order(self, params: list[object]) -> None:
        """Places an order for the current table. Allows
        for specifying a special request, which can be specified
        to optionally add a 1 EUR charge or not."""
        if self.curr_table is None or self.tables[self.curr_table] is None:
            print("Must select a table before placing an order.")
            print('Use the "table" command to create/select a table.')
            return
        curr_table = self.tables[self.curr_table]

        item = self.food_items[params[0] - 1]
        special_requests = []
        while True:
            print(
                f"Ordering {item.name} for \
table {curr_table.id}."
            )
            if len(special_requests) > 0:
                print("Special requests:")
                for req in special_requests:
                    print(f" * {req.request} ({req.charge/100}€)")
            print("Options:")
            print("  y: Confirm")
            print("  n: Cancel")
            print("  s: Add special request")
            sel = input("Selection [Yns]: ").lower()
            if sel == "y" or sel == "":
                curr_table.orders.append(
                    Order(
                        datetime.now(),
                        item,
                        special_requests,
                    )
                )
                print("Order placed.")
                break
            elif sel == "n":
                print("Order cancelled.")
                break
            elif sel == "s":
                req = input("Special request: ")
                charge = (
                    input("Charge for 1€ for special request? [yN]: ").lower()
                    == "y"
                )
                special_requests.append(
                    SpecialRequest(req, 100 if charge else 0)
                )
            else:
                print("Invalid option.")
            print()

    def cmd_orders(self, params: list[object]) -> None:
        """Lists the current table's orders and the total amount."""
        if self.curr_table is None or self.tables[self.curr_table] is None:
            print("No table selected.")
            return
        curr_table = self.tables[self.curr_table]

        if len(curr_table.orders) == 0:
            print(f"No orders for table {curr_table.id}.")
            return

        print(f"Orders for table {curr_table.id}:")
        print(curr_table.orders(), end='')

    def cmd_rescind(self, params: list[object]) -> None:
        """Rescinds an existing order."""
        if self.curr_table is None or self.tables[self.curr_table] is None:
            print("No table selected.")
            return
        curr_table = self.tables[self.curr_table]

        order_id = params[0] - 1
        if order_id >= len(curr_table.orders):
            print(
                'Invalid order ID. Use "orders" \
to list orders.'
            )
            return
        order = curr_table.orders[order_id]
        if not isinstance(order, Order):
            print("Can only rescind orders.")
            return
        curr_table.orders.append(
            Rescindment(datetime.now(), order_id, order.amount())
        )
        print(f"Rescinded order {order_id+1} \
({order.food_item.name}) for {order.amount()/100}€.")

    def cmd_invoice(self, params: list[object]):
        """Finalize an order, creating an invoice and writing it to a file."""
        if self.curr_table is None or self.tables[self.curr_table] is None:
            print("No table selected.")
            return
        curr_table = self.tables[self.curr_table]

        if len(curr_table.orders) == 0:
            print(f"No orders for table {curr_table.id}.")
            return

        invoice = f"Table: {curr_table.id}\n"
        invoice += f"Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n"
        invoice += "Orders:\n"
        invoice += curr_table.orders()
        print(invoice)
        sel = input(f"Delete table {curr_table.id} and save invoice to file? [yN]: ").lower()
        if sel == "y":
            FILENAME = "invoices.txt"
            with open(FILENAME, "a") as f:
                f.write(invoice+"\n")
            del self.tables[self.curr_table]
            self.curr_table = None
            print(f"Saved table {curr_table.id}'s orders to {FILENAME} and deleted the table from memory.")

        else:
            return

    app.add_command(
        shell.Command(
            "table",
            "create and/or switch active table",
            [shell.StringParam("table_name")],
            cmd_table,
        )
    )
    app.add_command(shell.Command("tables", "list tables", [], cmd_tables))
    app.add_command(
        shell.Command(
            "list",
            "list available food items and their IDs",
            [shell.StringParam("filter", optional=True)],
            cmd_list,
        )
    )
    app.add_command(
        shell.Command(
            "order",
            "place an order for the current table",
            [
                shell.IntParam(
                    "item_id",
                    min=1,
                    max=len(app.food_items),
                )
            ],
            cmd_order,
        )
    )
    app.add_command(
        shell.Command(
            "orders",
            "list current table's orders",
            [],
            cmd_orders,
        )
    )
    app.add_command(
        shell.Command(
            "rescind",
            "rescind one of the current table's orders",
            [shell.IntParam("order_id", min=1)],
            cmd_rescind,
        )
    )
    app.add_command(
        shell.Command(
            "invoice",
            "finalize the current table's orders and generate/save invoice",
            [],
            cmd_invoice,
        )
    )

    app.run("Welcome to the RESTAURANT SHELL 9000!")


if __name__ == "__main__":
    run()
