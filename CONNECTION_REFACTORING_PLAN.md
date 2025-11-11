# Connection Refactoring Plan for EDSDEVV

## Overview
The codebase has 5 direct `psycopg2.connect()` calls that need to be replaced with the `get_db()` context manager to fix the "out of ports" error on Render.

## Infrastructure Ready
✅ `db_helper.py` created with `get_db()` context manager  
✅ Import statement added: `from db_helper import get_db, execute_query` (line 15)  
✅ `initialize_database_tables()` already uses `get_db()`

## Remaining Refactoring Tasks

### Task 1: `/webhook` Route - Line 6457
**Current Issue**: Complex nested loops with database operations scattered across the scope.

**Location**: Line 6457 - Inside nested message loop, needs entire section refactored

**Pattern to Apply**:
```python
# BEFORE (current):
try:
    connection = psycopg2.connect(external_database_url)
    cursor = connection.cursor()
    cursor.execute("SELECT ... WHERE whatsapp::TEXT LIKE %s")
    # ... cursor operations ...
finally:
    if connection:
        print('DONE')

# AFTER (desired):
try:
    with get_db() as (cursor, connection):
        cursor.execute("SELECT ... WHERE whatsapp::TEXT LIKE %s")
        tables = cursor.fetchall()
        # ... all cursor operations must stay INSIDE with block ...
        # ... fetchone(), execute(), commit() all inside ...
```

**Key Refactoring Rules**:
1. Move all `cursor.execute()` calls INSIDE the `with get_db() as (cursor, connection):` block
2. For SELECT queries: No need to call `connection.commit()`
3. For INSERT/UPDATE/DELETE: Call `connection.commit()` INSIDE the with block before accessing results
4. The for loop at line 6470 that uses `cursor.execute(query, (f"%{sender_number}",))` MUST move inside the with block
5. All subsequent lines that call `cursor.fetchall()` or `cursor.fetchone()` must stay inside the with block

**Affected Code Section**: Lines 6454-6650+ (the entire "if role_foc_8 == 'Ordinary User'" section)

**Estimated Complexity**: HIGH - Multiple nested loops, branching logic, and cursor operations spanning 200+ lines

---

### Task 2: `/admin_sign_up` Route - Line 16580
**Location**: Line 16580 in `/admin_sign_up` route

**Current Pattern**:
```python
connection = psycopg2.connect(external_database_url)
cursor = connection.cursor()
cursor.execute(...)
connection.commit()
cursor.close()
connection.close()
```

**Replace With**:
```python
with get_db() as (cursor, connection):
    cursor.execute(...)
    connection.commit()
```

**Affected Code**: Insert/update operations for company registration

---

### Task 3: `/login` Route - Line 16998
**Location**: Line 16998 in `/login` route

**Current Pattern**:
```python
connection = psycopg2.connect(external_database_url)
cursor = connection.cursor()
cursor.execute("SELECT ...")
result = cursor.fetchone()
# ... later ...
connection.close()
```

**Replace With**:
```python
with get_db() as (cursor, connection):
    cursor.execute("SELECT ...")
    result = cursor.fetchone()
    # Can use result outside with block - data is already fetched
```

**Critical Point**: Data fetched with `fetchone()` or `fetchall()` CAN be used outside the with block. The connection closes, but the data persists.

---

### Task 4: `/login_first_time` Route - Line 17121
**Location**: Line 17121 in `/login_first_time` route

**Same pattern as Task 3** - SELECT + fetched data use

---

### Task 5: `/export_all_tables` Route - Line 18505
**Location**: Line 18505 in `/export_all_tables` route

**Similar pattern** - likely SELECT operations for exporting data

---

## Refactoring Strategy

### Quick Wins (20 minutes)
1. Replace Tasks 2, 3, 4, 5 - All are straightforward `psycopg2.connect()` → `with get_db()` replacements
2. These don't have complex nesting, just standard try/except blocks

### Complex Task (1-2 hours)
1. **Task 1**: The `/webhook` route refactoring
   - Requires careful indentation changes
   - Multiple nested for/if blocks
   - Cursor operations scattered across the section
   - **Recommendation**: Tackle this AFTER verifying other tasks work

## Testing After Refactoring

1. **Local Testing**:
   ```bash
   python -m py_compile LMSuniversal.py  # Check syntax
   python LMSuniversal.py  # Run locally
   ```

2. **Monitor on Render**:
   - Deploy to Render
   - Watch logs: `render.com > Dashboard > Your App > Logs`
   - Send test WhatsApp messages to `/webhook`
   - Check PostgreSQL connection count:
     ```sql
     SELECT count(*) FROM pg_stat_activity;
     ```
   - Should stabilize below 20 connections instead of climbing

## Why This Fixes "Out of Ports"

- **Before**: Each request → `psycopg2.connect()` → connection stays open if exception occurs → connection pool fills up → error
- **After**: Each request → `with get_db()` context manager → connection GUARANTEED to close in finally block → ports freed → stable operation

## Files to Edit

1. `/admin_sign_up` (line 16580)
2. `/login` (line 16998)  
3. `/login_first_time` (line 17121)
4. `/export_all_tables` (line 18505)
5. `/webhook` (line 6457) - **Most complex, do last**

## Validation Checklist

After each task:
- [ ] No `connection = psycopg2.connect()` lines remain in that route
- [ ] All cursor operations are inside `with get_db() as (cursor, connection):` block
- [ ] INSERT/UPDATE/DELETE calls `connection.commit()` inside the with block
- [ ] No syntax errors: `python -m py_compile LMSuniversal.py`
