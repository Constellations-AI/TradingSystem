# PostgreSQL Migration Guide for Railway

## What was implemented:

✅ **Database abstraction layer** - supports both SQLite (local) and PostgreSQL (Railway)
✅ **Automatic detection** - uses `DATABASE_URL` environment variable  
✅ **Zero downtime migration** - all existing code works unchanged
✅ **Schema compatibility** - PostgreSQL tables match SQLite structure

## Railway Setup Steps:

### 1. Add PostgreSQL Database
In Railway dashboard:
- Click "Add Database" 
- Select "PostgreSQL"
- Railway will create the database and provide `DATABASE_URL`

### 2. Environment Variables  
Railway automatically provides:
```
DATABASE_URL=${{ Postgres.DATABASE_URL }}
```

### 3. Code Changes Made:
- `database.py`: Added PostgreSQL support with fallback to SQLite
- `accounts.py`: Updated to use parameterized queries for both databases
- `requirements.txt`: Already has `psycopg2-binary` 

### 4. How it works:

**Local Development:**
- No `DATABASE_URL` → Uses SQLite (`trading_system.db`)
- Accounts: Warren, Camillo, Pavel portfolios persist locally

**Railway Production:**
- `DATABASE_URL` present → Uses PostgreSQL 
- Accounts: All portfolios persist in managed database
- **No more resets on deployment!**

### 5. Migration behavior:

```python
# Automatic database selection
db = Database()  # Uses DATABASE_URL if present, SQLite otherwise

# All existing code works unchanged
warren = get_trader_account('warren')
warren.buy_shares('AAPL', 10, 'Value investment')
```

### 6. Verification:
After Railway deployment with PostgreSQL:
- Traders should maintain their portfolios between deployments
- Warren should keep his 6+ stocks (MSFT, JNJ, PG, NVO, KO, AAPL, etc.)
- Camillo should keep his holdings
- No more "portfolio reset" issues

## Benefits:
- ✅ True database persistence on Railway
- ✅ No code changes needed in trading logic  
- ✅ Maintains local development with SQLite
- ✅ ACID compliance for concurrent trading
- ✅ Better performance for multiple traders