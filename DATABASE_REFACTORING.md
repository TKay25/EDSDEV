# Database Connection Refactoring Guide for LMSuniversal.py

## Overview
This guide provides a step-by-step approach to refactor all database connections in `LMSuniversal.py` to use the new context manager pattern from `db_helper.py`. This will eliminate the "out of ports" error on Render.

## Quick Start

### Already Done
✅ Created `db_helper.py` with context manager utilities  
✅ Updated imports in `LMSuniversal.py`  
✅ Refactored database initialization code  
✅ Updated first connection in `/webhook` route  

### Pattern to Apply Everywhere Else

**OLD CODE (BAD - causes connection leaks):**
```python
connection = psycopg2.connect(external_database_url)
cursor = connection.cursor()
try:
    cursor.execute("SELECT * FROM table WHERE id = %s", (123,))
    result = cursor.fetchone()
    connection.commit()
except Exception as e:
    print(f"Error: {e}")
```

**NEW CODE (GOOD - safe and clean):**
```python
try:
    with get_db() as (cursor, connection):
        cursor.execute("SELECT * FROM table WHERE id = %s", (123,))
        result = cursor.fetchone()
        connection.commit()
except Exception as e:
    print(f"Error: {e}")
```

## Critical Routes to Refactor (Priority Order)

### 1. `/webhook` Route (LINE ~190)
**Status**: PARTIALLY DONE
**What to do**: 
- Remove all standalone `connection = psycopg2.connect(...)` lines
- Wrap entire database operations in `with get_db() as (cursor, connection):`
- Ensure `connection.commit()` is called after INSERT/UPDATE

**Example locations in webhook:**
- Line ~320: Customer details SELECT
- Line ~340: Customer details INSERT/UPDATE  
- Line ~660: cagwatick2 INSERT
- Line ~750: cagwatickcustomerdetails SELECT
- Multiple other locations

### 2. `/leave_application` Route (LINE ~17220)
**Status**: NOT STARTED
**What to do**: 
Replace all database operations (typically 10-15 per route)

### 3. `/login` Route (LINE ~17002)
**Status**: NOT STARTED
**What to do**: 
Replace database SELECT operations

## How to Use Search & Replace

### VS Code Find & Replace (Ctrl+H)

**Pattern 1**: Remove standalone connection creation
```
Find:  connection = psycopg2\.connect\(external_database_url\)\ncursor = connection\.cursor\(\)
Replace: with get_db() as (cursor, connection):
```

**Pattern 2**: Fix indentation after replacement
Manually indent the next 3-5 lines after replacement

**Pattern 3**: Remove orphaned finally blocks
```
Find:  finally:\n\s+cursor\.close\(\)\n\s+connection\.close\(\)
Replace: (delete - no longer needed)
```

## Validation Checklist

After refactoring each route, verify:

- [ ] All `cursor.execute()` calls are inside `with get_db()` block
- [ ] All `connection.commit()` calls are inside the block (before `with` exits)
- [ ] No orphaned `cursor.close()` or `connection.close()` calls remain
- [ ] No exceptions are silently caught without proper handling
- [ ] Syntax is correct (no indent errors)

## Testing

After making changes, test with:

```bash
# Check for syntax errors
python -m py_compile LMSuniversal.py

# Test by running Flask
python LMSuniversal.py
```

## Most Common Database Patterns in This Codebase

### SELECT (Read-only)
```python
with get_db() as (cursor, connection):
    cursor.execute("SELECT * FROM table WHERE col = %s", (value,))
    result = cursor.fetchone()  # or fetchall()
    # No commit needed for SELECTs
```

### INSERT
```python
with get_db() as (cursor, connection):
    cursor.execute(
        "INSERT INTO table (col1, col2) VALUES (%s, %s)",
        (val1, val2)
    )
    connection.commit()
```

### UPDATE
```python
with get_db() as (cursor, connection):
    cursor.execute(
        "UPDATE table SET col1 = %s WHERE id = %s",
        (new_value, id)
    )
    connection.commit()
```

### DELETE
```python
with get_db() as (cursor, connection):
    cursor.execute("DELETE FROM table WHERE id = %s", (id,))
    connection.commit()
```

## Files to Refactor

1. ✅ **Initialization code** (lines 50-185)
2. ⏳ **`/webhook` route** (lines ~190-6000+)
3. ⏳ **`/paynow/return` & `/paynow/result/update`** (lines ~15196-15235)
4. ⏳ **`/upload-excel` route** (lines ~16443)
5. ⏳ **`/admin_sign_up` route** (lines ~16583)
6. ⏳ **`/dashboard` route** (lines ~16873)
7. ⏳ **`/run_som_company_tables` route** (lines ~16929)
8. ⏳ **`/delete_company_tables` route** (lines ~16961)
9. ⏳ **`/login` route** (lines ~17002)
10. ⏳ **`/login_first_time` route** (lines ~17125)
11. ⏳ **`/leave_application` route** (lines ~17220)
12. ⏳ **All other routes** (remaining)

## Commands to Find All Issues

```bash
# Find standalone connection assignments
grep -n "connection = psycopg2.connect" LMSuniversal.py

# Find cursor.close() calls that need removal
grep -n "cursor.close()" LMSuniversal.py

# Find connection.close() calls that need removal  
grep -n "connection.close()" LMSuniversal.py
```

## When to Use `execute_query()` Helper

For simple, single queries (not part of a transaction):

```python
# Old way
with get_db() as (cursor, connection):
    cursor.execute("SELECT * FROM users WHERE id = %s", (123,), fetch_one=True)
    user = cursor.fetchone()

# New way (shorter)
user = execute_query("SELECT * FROM users WHERE id = %s", (123,), fetch_one=True)
```

But for **routes with multiple queries**, always use the context manager to keep the connection open:

```python
with get_db() as (cursor, connection):
    cursor.execute("SELECT ...")  # Query 1
    result1 = cursor.fetchone()
    
    cursor.execute("UPDATE ...")  # Query 2
    connection.commit()  # One commit after all queries
```

## Environment Variables (Future)

Update `db_helper.py` to support environment variables:

```bash
# On Render, set:
DATABASE_URL=postgresql://user:pass@host:port/db
```

This way, no hardcoded credentials in the code.

## Estimated Impact

- **Connections before fix**: Unlimited (causes exhaustion)
- **Connections after fix**: 1 per request, automatically cleaned
- **Expected result on Render**: No more "out of ports" errors
- **Refactoring time**: ~2 hours for complete codebase

---

**Last Updated**: November 11, 2025  
**Status**: In Progress - 1/82 routes completed
