import os
import sqlite3
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import app as app_module
from app import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_expenses.db"
    monkeypatch.setattr(app_module, "DB_PATH", test_db)
    app_module.init_db()
    yield test_db

def test_get_root_ui():
    response = client.get("/")
    assert response.status_code == 200
    assert "<title>Personal Expense Tracker</title>" in response.text

def test_get_expenses_empty():
    response = client.get("/expenses")
    assert response.status_code == 200
    data = response.json()
    assert data["expenses"] == []
    assert data["total_spent"] == 0.0

def test_add_expense_valid():
    payload = {"title": "Groceries", "amount": 45.50, "category": "Food"}
    response = client.post("/expenses", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Groceries"
    assert data["amount"] == 45.50
    assert data["category"] == "Food"
    assert "id" in data
    assert "created_at" in data

def test_list_expenses_with_total_calculation():
    client.post("/expenses", json={"title": "Lunch", "amount": 15.25, "category": "Food"})
    client.post("/expenses", json={"title": "Bus Pass", "amount": 24.75, "category": "Transport"})

    response = client.get("/expenses")
    assert response.status_code == 200
    data = response.json()
    assert len(data["expenses"]) == 2
    assert data["total_spent"] == 40.00

def test_delete_expense():
    res = client.post("/expenses", json={"title": "Book", "amount": 19.99, "category": "Shopping"})
    expense_id = res.json()["id"]

    # Delete existing expense
    del_res = client.delete(f"/expenses/{expense_id}")
    assert del_res.status_code == 200
    assert del_res.json()["id"] == expense_id

    # Verify expense list updated
    get_res = client.get("/expenses")
    assert len(get_res.json()["expenses"]) == 0
    assert get_res.json()["total_spent"] == 0.0

def test_invalid_input_handling():
    # Negative amount
    res_neg = client.post("/expenses", json={"title": "Item", "amount": -10.0, "category": "Other"})
    assert res_neg.status_code == 422

    # Zero amount
    res_zero = client.post("/expenses", json={"title": "Item", "amount": 0.0, "category": "Other"})
    assert res_zero.status_code == 422

    # Missing field
    res_missing = client.post("/expenses", json={"title": "Item", "amount": 10.0})
    assert res_missing.status_code == 422

    # Empty string title
    res_empty_title = client.post("/expenses", json={"title": "   ", "amount": 10.0, "category": "Other"})
    assert res_empty_title.status_code == 400

    # Delete non-existent expense ID
    res_del_404 = client.delete("/expenses/999999")
    assert res_del_404.status_code == 404
