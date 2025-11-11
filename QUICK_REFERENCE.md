# Quick Reference: Connection Refactoring

## Problem
App crashes with "out of ports" error on Render due to unclosed database connections.

## Solution
Use `get_db()` context manager instead of direct `psycopg2.connect()` calls.

---

## Pattern Reference

### ✅ CORRECT (Use This)
```python
with get_db() as (cursor, connection):
    cursor.execute("SELECT * FROM table WHERE id = %s", (123,))
    result = cursor.fetchone()
    connection.commit()  # Only for INSERT/UPDATE/DELETE
```

### ❌ WRONG (Don't Use This)
```python
connection = psycopg2.connect(external_database_url)
cursor = connection.cursor()
cursor.execute("SELECT * FROM table WHERE id = %s", (123,))
result = cursor.fetchone()
connection.commit()
connection.close()  # ← Forget this line once = connection leak
```

---

## 5 Routes to Refactor

| # | Route | Line | Time | Do First? |
|---|-------|------|------|-----------|
| 1 | `/admin_sign_up` | 16583 | 30 min | After 2-4 |
| 2 | `/login` | 17002 | 10 min | ✅ YES |
| 3 | `/login_first_time` | 17125 | 10 min | ✅ YES |
| 4 | `/export_all_tables` | 18505 | 10 min | ✅ YES |
| 5 | `/webhook` | 6457 | 1-2 hrs | Last |

---

## Step-by-Step for Each Route

### 1. Find the Connection Line
```python
Ctrl+G → [line number]
# Find: connection = psycopg2.connect(external_database_url)
```

### 2. Remove Hardcoded URL
Delete the line:
```python
external_database_url = "postgresql://..."
```

### 3. Wrap in Context Manager
Before:
```python
connection = psycopg2.connect(...)
cursor = connection.cursor()
```

After:
```python
with get_db() as (cursor, connection):
```

### 4. Indent Database Operations
All `cursor.execute()` calls must be inside the `with` block.

### 5. Remove Manual Close
Delete:
```python
cursor.close()
connection.close()
```

### 6. Test
```bash
python -m py_compile LMSuniversal.py
```

---

## Common Mistakes to Avoid

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| `connection.commit()` outside with block | `connection.commit()` inside with block |
| `cursor.execute()` outside with block | All cursor operations inside with block |
| Trying to use `cursor` after with block | Use `result` from `fetchone()`/`fetchall()` |
| Forgetting to pass both `cursor, connection` | `with get_db() as (cursor, connection):` |
| Having multiple connections per route | One `with get_db()` block per operation |

---

## Testing Commands

```bash
# Check syntax
python -m py_compile LMSuniversal.py

# Search for remaining problematic code
grep "psycopg2.connect" LMSuniversal.py
grep "cursor.close()" LMSuniversal.py
grep "connection.close()" LMSuniversal.py

# Run locally
python LMSuniversal.py
```

---

## Key Remember Points

1. ✅ Connection **auto-closes** - no need for `.close()` calls
2. ✅ Exceptions **auto-rollback** - no transaction leaks
3. ✅ Data persists after context - `result` from `fetchone()` works outside
4. ✅ `connection.commit()` is only inside the `with` block for writes
5. ❌ Don't try to use `cursor` or `connection` variables outside the `with` block

---

## Order of Operations

1. Do Tasks 2, 3, 4 first (quick wins - 30 min)
2. Then Task 1 (medium - 30 min)
3. Finally Task 5 (complex - 1-2 hours)
4. Deploy to Render when all 5 complete
5. Monitor logs for connection stability

---

## Need Help?

1. Compare with working example: `initialize_database_tables()` (lines 48-162)
2. Read detailed guide: `MANUAL_REFACTORING_GUIDE.md`
3. Check plan: `CONNECTION_REFACTORING_PLAN.md`
4. Review patterns: `.github/copilot-instructions.md`

---

**Start with `/login` - it's the simplest!**
