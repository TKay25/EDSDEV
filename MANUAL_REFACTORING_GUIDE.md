# Manual Refactoring Guide: Connection Management

## Why Manual Refactoring?

The code has large blocks with nested indentation (200-500 lines per route). Automated editing risks breaking logic. **Manual refactoring in VS Code is faster and safer.**

---

## Quick Reference: Context Manager Pattern

**Before (Current - Creates Connection Leaks)**:
```python
connection = psycopg2.connect(external_database_url)
cursor = connection.cursor()
cursor.execute("SELECT...")
result = cursor.fetchone()
connection.commit()
cursor.close()
connection.close()
```

**After (Fixed - No Leaks)**:
```python
with get_db() as (cursor, connection):
    cursor.execute("SELECT...")
    result = cursor.fetchone()
    connection.commit()  # Only for INSERT/UPDATE/DELETE
```

**Key Points**:
- ✅ Connection auto-closes (no forgotten `.close()` calls)
- ✅ Exceptions trigger rollback automatically
- ✅ Data from `fetchone()`/`fetchall()` can be used outside the with block

---

## Task 1: `/admin_sign_up` Route (Line 16580)

### Step 1: Find the Function
**Ctrl+G** → Go to line 16583 (the @app.route line)

### Step 2: Identify the Block
```
Lines 16583-16590: @app.route + function def
Lines 16591-16650: try block START
    Line 16592: Remove "external_database_url = ..." (not needed, db_helper handles it)
    Line 16593: database = 'lmsdatabase_8ag3'
    Line 16595: connection = psycopg2.connect(...) ← DELETE THIS
    Line 16597: cursor = connection.cursor() ← DELETE THIS
    Lines 16599-16853: All the CREATE TABLE and INSERT operations
Lines 16854-16856: except/finally blocks
```

### Step 3: Execute Refactoring

**Step 3a**: Delete lines 16592, 16595, 16597 (remove `external_database_url`, `connection`, `cursor` declarations)

**Step 3b**: Find the line with:
```python
database = 'lmsdatabase_8ag3'
```

Add a `with get_db()` block BEFORE the check_table_query:

```python
            database = 'lmsdatabase_8ag3'

            with get_db() as (cursor, connection):
                check_table_query = f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s;
                """
                cursor.execute(check_table_query, (database, table_name))
                table_exists = cursor.fetchone()[0]

                if table_exists:
                    print(f"Table `{table_name}` already exists. Skipping creation.")
                    return render_template('index.html')  
                
                else:
                    try:
                        # ... all CREATE TABLE statements ...
                        # ... all INSERT statements ...
                        cursor.execute(...)
                        connection.commit()
                        # ... etc ...
                    except ...:
                        # ... error handling ...
```

**Step 3c**: Indent everything from `if table_exists:` to the end of the `try` block (before `except Error`) to be inside the `with get_db()` block.

**Quick indent in VS Code**: 
1. Select all lines to indent
2. Press **Tab** to indent (or Shift+Tab to unindent)

### Step 4: Validate
- Run syntax check: **Ctrl+Shift+B** or terminal: `python -m py_compile LMSuniversal.py`
- No errors = success!

---

## Task 2: `/login` Route (Line 17002)

### Step 1: Go to Line
**Ctrl+G** → 17002

### Step 2: Find the Connection Block
Look for:
```python
connection = psycopg2.connect(external_database_url)
cursor = connection.cursor()
```

### Step 3: Apply Pattern
Wrap all SELECT operations:
```python
with get_db() as (cursor, connection):
    cursor.execute("SELECT * FROM companyreg WHERE...")
    result = cursor.fetchone()
    # Use result inside or outside - data is fetched

# Now you can use 'result' here - connection is closed but data persists
```

### Step 4: Find and Remove
- Remove `external_database_url = "..."` line
- Remove `connection = psycopg2.connect(...)`
- Remove `cursor = connection.cursor()`
- Remove any final `cursor.close()` and `connection.close()`

---

## Task 3: `/login_first_time` Route (Line 17125)

### Same Process as Task 2
- Find line 17125
- Locate `psycopg2.connect()` 
- Wrap with `get_db()` context manager
- Remove connection management code

---

## Task 4: `/export_all_tables` Route (Line 18505)

### Same Process as Tasks 2-3

---

## Task 5: `/webhook` Route (Line 6457) ⚠️ MOST COMPLEX

**DO THIS LAST** - After Tasks 1-4 work.

This route has:
- Multiple `psycopg2.connect()` calls
- Nested message loops
- Complex branching logic
- Cursor operations scattered across 300+ lines

**Recommendation**: 
1. Identify each direct `psycopg2.connect()` call
2. Replace each with `with get_db()` context manager
3. Move ALL cursor operations into their respective with blocks
4. Use **Find and Replace** (Ctrl+H) with regex for efficiency

### Sub-task 5a: First Connection (Line 6457)
```python
# Find:
try:
    connection = psycopg2.connect(...)
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT table_name...")
```

Replace with:
```python
try:
    with get_db() as (cursor, connection):
        cursor.execute("SELECT DISTINCT table_name...")
        # ... keep all cursor operations inside ...
```

---

## Testing After Each Task

### Syntax Check
```bash
python -m py_compile LMSuniversal.py
```

### Run Locally
```bash
python LMSuniversal.py
```

### Test Specific Route
- For `/admin_sign_up`: Submit form → should create tables
- For `/login`: Log in → should fetch user
- For `/webhook`: Send WhatsApp message → should process

---

## Verification Checklist

After refactoring all 5 tasks:

- [ ] No `psycopg2.connect(external_database_url)` lines remain (use grep: Ctrl+Shift+F)
- [ ] No `cursor = connection.cursor()` outside `with get_db()` blocks
- [ ] All `cursor.execute()` calls are inside `with get_db()` blocks
- [ ] `connection.commit()` is called INSIDE the with block for writes
- [ ] No syntax errors: `python -m py_compile LMSuniversal.py`
- [ ] Runs locally without errors: `python LMSuniversal.py`

---

## Why This Matters

**Connection Pool Exhaustion** (Current Problem):
```
Request 1: open connection → exception → connection stays open
Request 2: open connection → exception → connection stays open
Request 3: open connection → exception → connection stays open
... (repeat 20 times)
PostgreSQL connection pool full (20 limit on Render)
❌ "Out of Ports" error - app crashes
```

**After Refactoring** (Fixed):
```
Request 1: with get_db() → exception → finally block closes connection
Request 2: with get_db() → exception → finally block closes connection
Request 3: with get_db() → exception → finally block closes connection
... (repeat 1000 times)
✅ All connections closed properly - stable operation
```

---

## If You Get Stuck

1. **Check indentation**: Python is indentation-sensitive. Use VS Code's "View Whitespace" (Ctrl+Shift+P → "whitespace")
2. **Compare with working code**: Look at `initialize_database_tables()` (lines 48-162) for a good example of `with get_db()` pattern
3. **Use Find**: Ctrl+Shift+F to search for all `psycopg2.connect` calls - should be 0 after refactoring
4. **Validate each task**: Don't skip syntax checks between tasks

---

## Expected Result

✅ App runs on Render without "out of ports" errors
✅ PostgreSQL connection count stays below 10 (vs. climbing to 20+)
✅ Better error handling - exceptions don't leak connections
✅ Cleaner code - no more manual close() calls
