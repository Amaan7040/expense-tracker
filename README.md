# Personal Expense Tracker 💰

A modern, fast, and clean **Personal Expense Tracker** web application built using **Python FastAPI** and **SQLite3**.

This project provides both a JSON REST API and a responsive single-page web interface with live updates for tracking daily expenses.

---

## Features

- **Live Summary Card**: Displays the calculated **Total Spent** dynamically across all logged expenses.
- **Add Expense Form**: Input title, amount ($), and choose a category (Food, Transport, Utilities, Entertainment, Shopping, Other).
- **Category Badges**: Visual badges styled according to expense categories.
- **Delete Functionality**: Instantly delete expenses with automatic total calculation updates.
- **FastAPI & SQLite3**: Lightweight, zero-config backend persistence using built-in `sqlite3`.

---

## API Endpoints

### 1. `GET /expenses`
Retrieves all logged expenses along with the total amount spent.

**Response Example:**
```json
{
  "expenses": [
    {
      "id": 1,
      "title": "Groceries",
      "amount": 45.50,
      "category": "Food",
      "created_at": "2025-02-23 12:00:00"
    }
  ],
  "total_spent": 45.50
}
```

### 2. `POST /expenses`
Creates a new expense record.

**Request Body:**
```json
{
  "title": "Coffee & Bagel",
  "amount": 8.75,
  "category": "Food"
}
```

**Response Example (Status: `201 Created`):**
```json
{
  "id": 2,
  "title": "Coffee & Bagel",
  "amount": 8.75,
  "category": "Food",
  "created_at": "2025-02-23 12:05:00"
}
```

### 3. `DELETE /expenses/{id}`
Deletes an expense item by ID.

**Response Example:**
```json
{
  "message": "Expense deleted successfully",
  "id": 2
}
```

### 4. `GET /`
Serves the clean single-page HTML/CSS/JS frontend dashboard.

---

## Setup & Running Locally

1. **Install Dependencies**:
   ```bash
   pip install fastapi uvicorn pytest httpx
   ```

2. **Run the Application**:
   ```bash
   uvicorn app:app --reload --port 8001
   ```
   Open [http://127.0.0.1:8001](http://127.0.0.1:8001) in your browser.

3. **Run Automated Tests**:
   ```bash
   pytest -v
   ```
