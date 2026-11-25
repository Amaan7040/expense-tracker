import sqlite3
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

DB_PATH = Path("expenses.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Personal Expense Tracker", lifespan=lifespan)


class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the expense")
    amount: float = Field(..., gt=0, description="Expense amount must be positive")
    category: str = Field(..., min_length=1, description="Category of expense")


@app.get("/expenses")
def get_expenses():
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, amount, category, created_at FROM expenses ORDER BY id DESC"
        ).fetchall()
        expenses = [dict(row) for row in rows]
        total_spent = sum(item["amount"] for item in expenses)
    return {"expenses": expenses, "total_spent": round(total_spent, 2)}


@app.post("/expenses", status_code=status.HTTP_201_CREATED)
def create_expense(expense: ExpenseCreate):
    title = expense.title.strip()
    category = expense.category.strip()
    if not title or not category:
        raise HTTPException(
            status_code=400, detail="Title and category cannot be empty strings."
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (title, amount, category) VALUES (?, ?, ?)",
            (title, round(expense.amount, 2), category),
        )
        conn.commit()
        expense_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, title, amount, category, created_at FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()

    return dict(row)


@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT id FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Expense not found")
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
    return {"message": "Expense deleted successfully", "id": expense_id}


@app.get("/", response_class=HTMLResponse)
def get_ui():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal Expense Tracker</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --danger: #ef4444;
            --danger-hover: #dc2626;
            --success: #10b981;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem 1rem;
            display: flex;
            justify-content: center;
        }

        .container {
            width: 100%;
            max-width: 800px;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        header {
            text-align: center;
            margin-bottom: 0.5rem;
        }

        header h1 {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        header p {
            color: var(--text-muted);
            font-size: 0.95rem;
            margin-top: 0.3rem;
        }

        .summary-card {
            background: linear-gradient(135deg, #1e1b4b, #312e81);
            border: 1px solid #4338ca;
            border-radius: 1rem;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }

        .summary-card h2 {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #a5b4fc;
            margin-bottom: 0.5rem;
        }

        .summary-card .total-amount {
            font-size: 2.5rem;
            font-weight: 700;
            color: #ffffff;
        }

        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }

        .card h3 {
            font-size: 1.1rem;
            margin-bottom: 1rem;
            color: var(--text-main);
        }

        form {
            display: grid;
            grid-template-columns: 2fr 1fr 1.5fr auto;
            gap: 0.75rem;
        }

        @media (max-width: 640px) {
            form {
                grid-template-columns: 1fr;
            }
        }

        input, select {
            background-color: #0f172a;
            border: 1px solid var(--card-border);
            color: var(--text-main);
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }

        input:focus, select:focus {
            border-color: var(--accent);
        }

        button.btn-add {
            background-color: var(--accent);
            color: white;
            font-weight: 600;
            border: none;
            padding: 0.75rem 1.25rem;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        button.btn-add:hover {
            background-color: var(--accent-hover);
        }

        .expense-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .expense-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: #0f172a;
            border: 1px solid var(--card-border);
            padding: 1rem;
            border-radius: 0.75rem;
            transition: transform 0.1s;
        }

        .expense-item:hover {
            transform: translateY(-2px);
        }

        .expense-info {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .expense-title {
            font-weight: 600;
            font-size: 1rem;
        }

        .expense-meta {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .badge {
            padding: 0.2rem 0.5rem;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge-food { background-color: #3b82f620; color: #60a5fa; border: 1px solid #3b82f640; }
        .badge-transport { background-color: #f59e0b20; color: #fbbf24; border: 1px solid #f59e0b40; }
        .badge-utilities { background-color: #10b98120; color: #34d399; border: 1px solid #10b98140; }
        .badge-entertainment { background-color: #ec489920; color: #f472b6; border: 1px solid #ec489940; }
        .badge-shopping { background-color: #8b5cf620; color: #a78bfa; border: 1px solid #8b5cf640; }
        .badge-default { background-color: #64748b20; color: #cbd5e1; border: 1px solid #64748b40; }

        .expense-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .expense-amount {
            font-size: 1.1rem;
            font-weight: 700;
            color: #ffffff;
        }

        .btn-delete {
            background-color: transparent;
            color: var(--danger);
            border: 1px solid var(--danger);
            padding: 0.4rem 0.75rem;
            border-radius: 0.375rem;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-delete:hover {
            background-color: var(--danger);
            color: white;
        }

        .empty-state {
            text-align: center;
            color: var(--text-muted);
            padding: 2rem 0;
            font-size: 0.95rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Personal Expense Tracker</h1>
            <p>Track your daily spending easily & efficiently</p>
        </header>

        <div class="summary-card">
            <h2>Total Spent</h2>
            <div class="total-amount" id="totalSpent">$0.00</div>
        </div>

        <div class="card">
            <h3>Add New Expense</h3>
            <form id="expenseForm">
                <input type="text" id="title" placeholder="Title (e.g. Groceries)" required />
                <input type="number" id="amount" placeholder="Amount ($)" step="0.01" min="0.01" required />
                <select id="category" required>
                    <option value="" disabled selected>Select Category</option>
                    <option value="Food">Food</option>
                    <option value="Transport">Transport</option>
                    <option value="Utilities">Utilities</option>
                    <option value="Entertainment">Entertainment</option>
                    <option value="Shopping">Shopping</option>
                    <option value="Other">Other</option>
                </select>
                <button type="submit" class="btn-add">Add</button>
            </form>
        </div>

        <div class="card">
            <h3>Expense History</h3>
            <div id="expenseList" class="expense-list">
                <div class="empty-state">Loading expenses...</div>
            </div>
        </div>
    </div>

    <script>
        const getBadgeClass = (category) => {
            const cat = category.toLowerCase();
            if (['food', 'groceries', 'dining'].includes(cat)) return 'badge-food';
            if (['transport', 'travel', 'gas', 'car'].includes(cat)) return 'badge-transport';
            if (['utilities', 'bills', 'rent'].includes(cat)) return 'badge-utilities';
            if (['entertainment', 'movies', 'games'].includes(cat)) return 'badge-entertainment';
            if (['shopping', 'clothes'].includes(cat)) return 'badge-shopping';
            return 'badge-default';
        };

        const escapeHtml = (str) => {
            if (!str) return '';
            return String(str).replace(/[&<>"']/g, function(m) {
                return {
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#039;'
                }[m];
            });
        };

        const fetchExpenses = async () => {
            try {
                const res = await fetch('/expenses');
                const data = await res.json();
                
                document.getElementById('totalSpent').textContent = `$` + data.total_spent.toFixed(2);
                
                const listEl = document.getElementById('expenseList');
                if (!data.expenses || data.expenses.length === 0) {
                    listEl.innerHTML = '<div class="empty-state">No expenses recorded yet. Add one above!</div>';
                    return;
                }

                listEl.innerHTML = data.expenses.map(exp => `
                    <div class="expense-item">
                        <div class="expense-info">
                            <div class="expense-title">` + escapeHtml(exp.title) + `</div>
                            <div class="expense-meta">
                                <span class="badge ` + getBadgeClass(exp.category) + `">` + escapeHtml(exp.category) + `</span>
                                <span>` + (exp.created_at ? exp.created_at.split(' ')[0] : '') + `</span>
                            </div>
                        </div>
                        <div class="expense-right">
                            <span class="expense-amount">$` + exp.amount.toFixed(2) + `</span>
                            <button class="btn-delete" onclick="deleteExpense(` + exp.id + `)">Delete</button>
                        </div>
                    </div>
                `).join('');
            } catch (err) {
                console.error('Failed to fetch expenses:', err);
            }
        };

        document.getElementById('expenseForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = document.getElementById('title').value;
            const amount = parseFloat(document.getElementById('amount').value);
            const category = document.getElementById('category').value;

            if (!title || !amount || !category) return;

            try {
                const res = await fetch('/expenses', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, amount, category })
                });

                if (res.ok) {
                    document.getElementById('expenseForm').reset();
                    fetchExpenses();
                } else {
                    alert('Error adding expense');
                }
            } catch (err) {
                console.error('Error:', err);
            }
        });

        const deleteExpense = async (id) => {
            if (!confirm('Are you sure you want to delete this expense?')) return;
            try {
                const res = await fetch('/expenses/' + id, { method: 'DELETE' });
                if (res.ok) {
                    fetchExpenses();
                } else {
                    alert('Failed to delete expense');
                }
            } catch (err) {
                console.error('Error deleting expense:', err);
            }
        };

        fetchExpenses();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
