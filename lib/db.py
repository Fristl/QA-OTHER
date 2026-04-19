"""Db lib."""

TABLE = "oc_customer"

CREATE_COLUMNS = [
    "firstname",
    "lastname",
    "email",
    "telephone",
    "password",
    "status",
    "customer_group_id",
    "store_id",
    "language_id",
]

class DbClient:
    def __init__(self, connection):
        self._conn = connection

    def _cursor(self):
        return self._conn.cursor()

    def create_customer(self, customer_data):
        cols = CREATE_COLUMNS
        placeholders = ", ".join(["%s"] * len(cols))
        colnames = ", ".join(f"`{c}`" for c in cols)
        sql = f"INSERT INTO `{TABLE}` ({colnames}) VALUES ({placeholders})"
        values = [customer_data[c] for c in cols]

        with self._cursor() as cursor:
            cursor.execute(sql, values)
            return int(cursor.lastrowid)


    def get_customer_by_id(self, customer_id):
        sql = f"SELECT * FROM `{TABLE}` WHERE `customer_id`=%s"
        with self._cursor() as cursor:
            cursor.execute(sql, (customer_id,))
            return cursor.fetchone()


    def update_customer_basic_fields(
        self,
        customer_id,
        *,
        firstname=None,
        lastname=None,
        email=None,
        telephone=None,
    ):
        updates = []
        values = []

        if firstname is not None:
            updates.append("`firstname`=%s")
            values.append(firstname)
        if lastname is not None:
            updates.append("`lastname`=%s")
            values.append(lastname)
        if email is not None:
            updates.append("`email`=%s");
            values.append(email)
        if telephone is not None:
            updates.append("`telephone`=%s")
            values.append(telephone)

        if not updates:
            return 0

        set_clause = ", ".join(updates)
        sql = f"UPDATE `{TABLE}` SET {set_clause} WHERE `customer_id`=%s"
        values.append(customer_id)

        with self._cursor() as cursor:
            cursor.execute(sql, values)
            return cursor.rowcount


    def delete_customer_by_id(self, customer_id):
        sql = f"DELETE FROM `{TABLE}` WHERE `customer_id`=%s"
        with self._cursor() as cursor:
            cursor.execute(sql, (customer_id,))
            return cursor.rowcount
