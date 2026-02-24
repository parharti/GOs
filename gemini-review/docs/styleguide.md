# TNeGA Coding Standards & Style Guide

> These rules are enforced automatically by Gemini Code Review on every PR.

---

## 1. Logging Requirements

### Rule: Every function MUST have logging

Every public function, method, route handler, and controller action **must** include
at least entry-level logging. Gemini will flag any function without it.

### Python
```python
import logging
logger = logging.getLogger(__name__)

def process_payment(order_id: str, amount: float) -> dict:
    logger.info("process_payment called", extra={"order_id": order_id, "amount": amount})
    try:
        result = gateway.charge(order_id, amount)
        logger.info("Payment processed", extra={"order_id": order_id, "status": "success"})
        return result
    except PaymentError as e:
        logger.error("Payment failed", extra={"order_id": order_id, "error": str(e)})
        raise
```

### PHP
```php
use Psr\Log\LoggerInterface;

class PaymentController {
    public function processPayment(Request $request): JsonResponse {
        Log::info('processPayment called', ['order_id' => $request->order_id]);
        try {
            $result = $this->gateway->charge($request->order_id, $request->amount);
            Log::info('Payment processed', ['order_id' => $request->order_id]);
            return response()->json($result);
        } catch (PaymentException $e) {
            Log::error('Payment failed', ['order_id' => $request->order_id, 'error' => $e->getMessage()]);
            throw $e;
        }
    }
}
```

### Node.js / Express
```javascript
const logger = require('./utils/logger'); // winston or pino

async function processPayment(req, res) {
    logger.info('processPayment called', { orderId: req.body.orderId });
    try {
        const result = await gateway.charge(req.body.orderId, req.body.amount);
        logger.info('Payment processed', { orderId: req.body.orderId });
        res.json(result);
    } catch (error) {
        logger.error('Payment failed', { orderId: req.body.orderId, error: error.message });
        res.status(500).json({ error: 'Payment failed' });
    }
}
```

### Log Levels
| Level   | Use for                                      |
|---------|----------------------------------------------|
| `debug` | Detailed diagnostic info (dev only)          |
| `info`  | Function entry, successful operations        |
| `warn`  | Recoverable issues, deprecations             |
| `error` | Failed operations, caught exceptions         |

### NEVER log
- Passwords or tokens
- Full credit card numbers
- Personal identifiable information (PII) — mask or omit
- Database connection strings with credentials

---

## 2. Loop Safety

### Rule: No unbounded loops

Every loop must have a guaranteed exit condition.

```python
# ❌ BAD — potential infinite loop
while True:
    data = fetch_next()
    if data:
        process(data)

# ✅ GOOD — bounded with max iterations
MAX_RETRIES = 100
for attempt in range(MAX_RETRIES):
    data = fetch_next()
    if not data:
        break
    process(data)
else:
    logger.warning("Reached max iterations", extra={"max": MAX_RETRIES})
```

### Rules
- `while True` must have explicit `break` + max iteration guard
- Recursive functions must have base case + max depth
- Nested loops on large datasets require justification in comments
- Prefer `.map()` / `.filter()` / `.forEach()` over manual loops in JS/React
- Database queries inside loops are forbidden — use batch/bulk operations

---

## 3. Logical Error Prevention

### Required patterns
- Always handle `null` / `undefined` / `None` before accessing properties
- Use strict equality (`===`) in JavaScript, never `==`
- All `switch` / `match` statements must have a `default` case
- Avoid negated conditions in `if-else` — prefer positive logic
- All async operations must have error handling (`try/catch` or `.catch()`)

```javascript
// ❌ BAD
if (!user.isNotActive) { ... }

// ✅ GOOD
if (user.isActive) { ... }
```

---

## 4. PostgreSQL Standards

### Naming
- Tables: `snake_case`, plural (`user_accounts`)
- Columns: `snake_case` (`created_at`, `order_id`)
- Functions: `snake_case`, verb prefix (`fn_calculate_total`)
- Procedures: `snake_case`, verb prefix (`sp_process_refund`)
- Triggers: `trg_<table>_<event>` (`trg_orders_after_insert`)
- Indexes: `idx_<table>_<columns>` (`idx_users_email`)

### Required for all functions/procedures
```sql
CREATE OR REPLACE FUNCTION fn_example(p_user_id BIGINT)
RETURNS TABLE(id BIGINT, name TEXT)
LANGUAGE plpgsql
SECURITY INVOKER          -- ← Required: explicit security context
STABLE                    -- ← Required: volatility marker
AS $$
BEGIN
    -- Function body
EXCEPTION
    WHEN OTHERS THEN      -- ← Required: error handling
        RAISE WARNING 'fn_example failed: %', SQLERRM;
        RETURN;
END;
$$;

COMMENT ON FUNCTION fn_example(BIGINT) IS 'Brief description of purpose';
```

### SQL Injection prevention
```sql
-- ❌ NEVER — string concatenation
EXECUTE 'SELECT * FROM users WHERE id = ' || p_id;

-- ✅ ALWAYS — parameterized
EXECUTE 'SELECT * FROM users WHERE id = $1' USING p_id;
```

### Required in application code
```python
# ❌ NEVER
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ ALWAYS
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

---

## 5. React / Frontend Standards

### Component structure
```jsx
// 1. Imports
import React, { useState, useEffect } from 'react';
import logger from '../utils/logger';

// 2. Component
export default function UserProfile({ userId }) {
    logger.debug('UserProfile rendered', { userId });

    const [user, setUser] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        logger.info('Fetching user profile', { userId });
        fetchUser(userId)
            .then(data => {
                logger.info('User profile loaded', { userId });
                setUser(data);
            })
            .catch(err => {
                logger.error('Failed to load user profile', { userId, error: err.message });
                setError(err.message);
            });
    }, [userId]);

    if (error) return <ErrorBanner message={error} />;
    if (!user) return <Spinner />;

    return <div>{/* ... */}</div>;
}
```

### Rules
- No `dangerouslySetInnerHTML` without sanitization
- All API calls must have error handling
- Loading and error states required for async data
- Props must have TypeScript types or PropTypes
- No inline styles — use CSS modules or styled-components

---

## 6. Git & PR Standards

- PR title: `[TYPE] Brief description` (e.g., `[FIX] Resolve payment timeout`)
- Types: `FEAT`, `FIX`, `REFACTOR`, `DOCS`, `CHORE`, `TEST`
- Max 400 lines changed per PR (split larger changes)
- All PRs must pass Gemini review before merge
- Squash-merge to main

---

## 7. File Organization

```
project/
├── src/
│   ├── controllers/     # Route handlers
│   ├── services/        # Business logic
│   ├── models/          # DB models / queries
│   ├── middleware/       # Auth, logging, validation
│   ├── utils/           # Helpers, logger setup
│   └── config/          # Environment config
├── sql/
│   ├── migrations/      # Schema changes (numbered)
│   ├── functions/       # PostgreSQL functions
│   ├── procedures/      # PostgreSQL procedures
│   └── seeds/           # Test/default data
├── tests/
└── .github/workflows/   # CI/CD including Gemini reviews
```
