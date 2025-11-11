# Copilot Instructions for EDSDEVV

## Architecture Overview

This is a **Flask-based Enterprise LMS (Leave Management System) and Transport Management Platform** with WhatsApp integration.

### Core Components

1. **Main Application**: `LMSuniversal.py` (19,400+ lines)
   - Single Flask app serving both LMS and CAG Tours (transportation) systems
   - PostgreSQL database connection via `external_database_url`
   - Session-based authentication with company-specific multi-tenancy

2. **Database Design**
   - Multi-tenant architecture: Tables prefixed by company name (e.g., `cagmain`, `companynamemain`)
   - Dynamic table creation based on company registration
   - Related tables: `companyreg`, `cagwatickcustomerdetails`, `whatsapptempapplication`
   - Leave status tables: `{company}appspendingapproval`, `{company}appsapproved`

3. **Frontend**: Jinja2 templates in `/templates/`
   - DataTables.js for employee data display (e.g., `EDSDev.html`)
   - Multi-language support (English, Ndebele) hardcoded in WhatsApp responses

4. **External Integrations**
   - **WhatsApp**: Meta API (v18.0/v19.0) with webhook at `/webhook`
   - **Payment**: PayNow integration (`/paynow/return`, `/paynow/result/update`)
   - **PDF Generation**: WeasyPrint, xhtml2pdf, pdfkit

5. **Database Helper Module**: `db_helper.py` (NEW)
   - Context manager for safe connection handling
   - Prevents connection leaks on Render's "out of ports" errors
   - Use `with get_db() as (cursor, connection):` pattern everywhere

## Critical Patterns

### Database Connection Pattern (MUST USE)
```python
# Import at top of file:
from db_helper import get_db

# Use in routes:
try:
    with get_db() as (cursor, connection):
        cursor.execute("SELECT * FROM table WHERE id = %s", (123,))
        result = cursor.fetchone()
        connection.commit()  # Only after INSERT/UPDATE/DELETE
except Exception as e:
    print(f"Error: {e}")
    return jsonify({'success': False, 'message': str(e)}), 500
```

**Critical**: Every database operation MUST use this pattern. Do NOT use `psycopg2.connect()` directly.

## Database Connection Pattern (CRITICAL - Prevents "Out of Ports" Error)

**ALWAYS use this pattern for database operations**:
```python
from db_helper import get_db

with get_db() as (cursor, connection):
    cursor.execute("SELECT * FROM table WHERE id = %s", (123,))
    result = cursor.fetchone()
    connection.commit()  # Only for INSERT/UPDATE/DELETE
```

**Why**: This context manager guarantees connections close after use, preventing the "out of ports" error on Render. Without it, exceptions leave connections open, exhausting the 20-connection pool.

**DO NOT** use this pattern:
```python
# ❌ WRONG - Creates connection leaks
connection = psycopg2.connect(external_database_url)
cursor = connection.cursor()
cursor.execute(...)
```

See `MANUAL_REFACTORING_GUIDE.md` for refactoring existing code.

## Critical Patterns

### Session Management
```python
session['user_uuid'] = str(uuid.uuid4())
session['table_name'] = 'companyname_main'  # Multi-tenant key
session['empid'] = int(np.int64(empid))
session.permanent_session_lifetime = timedelta(minutes=30)
```
**Key Point**: Table name is the primary identifier for company-specific data. Always include `table_name` checks before database queries.

### Database Queries
- All queries use parameterized queries with `%s` placeholders
- No direct string interpolation except for dynamic table names (which are company-validated)
- Connections are automatically managed by `db_helper.py` context manager

### WhatsApp Integration Pattern
```python
def send_whatsapp_message(to, text, buttons=None):
    """Send text or interactive button messages"""
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text" or "interactive",
        "text": {"body": text}  # or "interactive": {...}
    }
    response = requests.post(f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages", 
                            headers=headers, json=data)
```
Webhook receiver at `/webhook` (POST) handles incoming messages and updates `cagwatickcustomerdetails.language` preference.

### Leave Application Workflow
1. User applies via `/leave_application` (POST)
2. Stored in `{company}appspendingapproval`
3. Approver reviews via `/approve_leave_application` or `/disapprove_leave_application`
4. Moves to `{company}appsapproved` on approval
5. PDF export via `/download_leave_app/<app_id>`
6. WhatsApp notifications sent at each stage

### File Upload Pattern
```python
@app.route('/upload-excel', methods=['POST'])
# Expects file in request.files['file']
# Uses openpyxl to parse .xlsx (not csv)
# Inserts rows into {company}main table with get_db() context
```

## Common Development Tasks

### Adding a New Company
1. Company registers via `/admin_sign_up` → creates `companyreg` entry
2. Triggers `/run_som_company_tables` → creates all required tables with dynamic prefixes
3. Uses SQL template: `CREATE TABLE IF NOT EXISTS {company_name}{table_suffix}`

### Modifying Leave Logic
- Leave day calculation in `/leave_application`: Iterates date range, includes Sundays (line ~17265)
- Balance update: Only subtract for "Annual" leave type, other types don't affect balance
- Modify `leave_days` calculation logic or conditional at line ~17296

### Adding WhatsApp Features
1. Add button/section to payload JSON
2. Update webhook handler to check `message.get("interactive")` → `interactive.get("type")`
3. Extract button ID: `interactive.get("button_reply", {}).get("id")`
4. Call `send_whatsapp_message()` with response text

### Exporting Data
- Excel: `/export_lms_book_excel` → Uses `openpyxl` with `PatternFill` and `Font` styling
- PDF: `/export_lms_book_pdf` → Uses WeasyPrint or xhtml2pdf (inline HTML to PDF)

### Fixing "Out of Ports" Errors on Render
This is a connection exhaustion issue. The refactoring is in progress:

1. **Database Helper**: Use `db_helper.py` context manager (REQUIRED)
2. **Refactoring Status**: See `DATABASE_REFACTORING.md` for progress
3. **Priority Routes**: `/webhook`, `/leave_application`, `/login`
4. **Validation**: Run `python -m py_compile LMSuniversal.py` to check syntax

For details on completing the refactoring, see `DATABASE_REFACTORING.md`.

## Project-Specific Conventions

### Naming
- Table names: snake_case, company-prefixed (e.g., `mycompany_main`, `mycompany_pending_approval`)
- Session keys: lowercase (e.g., `user_uuid`, `table_name`, `empid`)
- Routes: kebab-case for public (e.g., `/leave-application`), snake_case for admin (e.g., `/upload_excel`)

### Error Handling
- Try/except blocks wrap database operations and WhatsApp API calls
- Return JSON responses: `jsonify({'success': True/False, 'message': str}), 200/400/401/500`
- Use context manager to ensure connections always close, even on errors

### Secrets & Hardcoded Values
- WhatsApp API tokens in `/webhook` function (SECURITY ISSUE - should use environment variables)
- Session secret key: `app.secret_key = '011235'` (SHOULD BE ENVIRONMENT VARIABLE)
- **Action**: Before production, move all secrets to environment variables

## Required Dependencies
See `requirements.txt`: Flask, psycopg2, pandas, openpyxl, requests, weasyprint, pdfkit, paynow

## Running the App
```bash
python LMSuniversal.py  # Starts Flask on http://0.0.0.0:55 (debug=True)
# Uses PostgreSQL on Render (connection managed by db_helper.py)
```

## Common Gotchas
1. **Multi-tenancy**: Always check `session['table_name']` before queries; cross-company data leaks are possible
2. **Connection Leaks** (FIXED): Use `db_helper.py` context manager; never call `psycopg2.connect()` directly
3. **Type Conversions**: Inconsistent use of `np.int64()`, `int()`, `float()`; data from forms are strings
4. **WhatsApp Language Logic**: Hardcoded English/Ndebele; new languages require duplicating entire webhook section
5. **Pandas Usage**: Minimal; mostly for Excel export column mapping
6. **Nested Functions**: PDF/image generation functions defined inside route handlers; refactor to module-level if reusing

## Refactoring Progress

- [x] Create `db_helper.py` with context manager
- [x] Update imports in main file
- [x] Refactor initialization code
- [x] Update first `/webhook` connection
- [ ] Complete `/webhook` route (major refactoring needed)
- [ ] Refactor `/login` route
- [ ] Refactor `/leave_application` route
- [ ] Refactor remaining 79+ routes

**See `DATABASE_REFACTORING.md` for detailed progress and next steps.**

