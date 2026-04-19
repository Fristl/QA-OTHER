"""Db tests."""


def test_create_customer_and_select_by_id(db_client, customer_payload):
    cust_id = db_client.create_customer(customer_payload)
    row = db_client.get_customer_by_id(cust_id)
    assert row is not None
    assert row["customer_id"] == cust_id

    assert db_client.delete_customer_by_id(cust_id) == 1
    assert db_client.get_customer_by_id(cust_id) is None

def test_update_existing_customer_basic_fields(
    db_client,
    created_customer_id,
    update_payload,
):
    cust_id = created_customer_id

    affected = db_client.update_customer_basic_fields(
        cust_id,
        firstname=update_payload["firstname"],
        lastname=update_payload["lastname"],
        email=update_payload["email"],
        telephone=update_payload["telephone"],
    )
    assert affected == 1

    row = db_client.get_customer_by_id(cust_id)
    assert row is not None
    assert row["firstname"] == update_payload["firstname"]
    assert row["lastname"] == update_payload["lastname"]
    assert row["email"] == update_payload["email"]
    assert row["telephone"] == update_payload["telephone"]


def test_update_nonexistent_customer(db_client, update_payload):
    affected = db_client.update_customer_basic_fields(
        999_999_999,
        firstname=update_payload["firstname"],
        lastname=update_payload["lastname"],
        email=update_payload["email"],
        telephone=update_payload["telephone"],
    )
    assert affected == 0


def test_delete_existing_customer(db_client, created_customer_id):
    assert db_client.get_customer_by_id(created_customer_id) is not None
    affected = db_client.delete_customer_by_id(created_customer_id)
    assert affected == 1
    assert db_client.get_customer_by_id(created_customer_id) is None


def test_delete_nonexistent_customer(db_client):
    affected = db_client.delete_customer_by_id(999_999_998)
    assert affected == 0
