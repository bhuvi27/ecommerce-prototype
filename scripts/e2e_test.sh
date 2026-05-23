#!/bin/bash
set -e
API="http://localhost:3000/api/v1"
WEB="http://localhost:3001"
COOKIE_JAR=$(mktemp)
PASS=0
FAIL=0

check() {
  local name="$1"
  local ok="$2"
  if [ "$ok" = "1" ]; then
    echo "  PASS: $name"
    PASS=$((PASS+1))
  else
    echo "  FAIL: $name"
    FAIL=$((FAIL+1))
  fi
}

echo "=== Beauty Store E2E Test ==="

# Health
READY=$(curl -sf http://localhost:3000/health/ready | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "fail")
check "API health/ready" "$([ "$READY" = "ready" ] && echo 1 || echo 0)"

# Catalog
CATS=$(curl -sf "$API/catalog/categories" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
check "List categories (>=3)" "$([ "${CATS:-0}" -ge 3 ] && echo 1 || echo 0)"

PRODS=$(curl -sf "$API/catalog/products" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['items']))")
check "List products (>=5)" "$([ "${PRODS:-0}" -ge 5 ] && echo 1 || echo 0)"

PROD=$(curl -sf "$API/catalog/products/coconut-oil" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('slug',''))")
check "Product detail coconut-oil" "$([ "$PROD" = "coconut-oil" ] && echo 1 || echo 0)"

PRODUCT_ID=$(curl -sf "$API/catalog/products/coconut-oil" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
SKU_ID=$(curl -sf "$API/catalog/products/coconut-oil" | python3 -c "import sys,json; print(json.load(sys.stdin)['skus'][0]['id'])")

# Guest cart
CART=$(curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" -X POST "$API/cart/items" \
  -H "Content-Type: application/json" \
  -d "{\"product_id\":\"$PRODUCT_ID\",\"sku_id\":\"$SKU_ID\",\"quantity\":1}")
ITEMS=$(echo "$CART" | python3 -c "import sys,json; print(json.load(sys.stdin)['item_count'])")
check "Add to guest cart" "$([ "${ITEMS:-0}" -ge 1 ] && echo 1 || echo 0)"

# Register or login
REG=$(curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e-user@example.com","password":"Test1234!","name":"E2E User"}')
TOKEN=$(echo "$REG" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null || true)
if [ -z "$TOKEN" ]; then
  REG=$(curl -sf -X POST "$API/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"e2e-user@example.com","password":"Test1234!"}')
  TOKEN=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
fi
check "User auth (register or login)" "$([ -n "$TOKEN" ] && echo 1 || echo 0)"

# Add to cart as logged-in user (guest cart is separate)
curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" -X POST "$API/cart/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"product_id\":\"$PRODUCT_ID\",\"sku_id\":\"$SKU_ID\",\"quantity\":1}" >/dev/null

# Saved address
ADDR=$(curl -sf -X POST "$API/auth/addresses" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"label":"E2E Home","line1":"123 Test St","city":"Mumbai","state":"MH","pincode":"400001","phone":"9999999999","is_default":true}')
ADDR_ID=$(echo "$ADDR" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || true)
check "Create saved address" "$([ -n "$ADDR_ID" ] && echo 1 || echo 0)"

ADDRS=$(curl -sf -H "Authorization: Bearer $TOKEN" "$API/auth/addresses" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
check "List saved addresses (>=1)" "$([ "${ADDRS:-0}" -ge 1 ] && echo 1 || echo 0)"

# Checkout (requires login)
IDEM=$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")
CHECKOUT=$(curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" -X POST "$API/orders/checkout" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: $IDEM" \
  -d "{\"address_id\":\"$ADDR_ID\",\"payment_method\":\"cod\"}")
ORDER_ID=$(echo "$CHECKOUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['order']['id'])")
ORDER_STATUS=$(echo "$CHECKOUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['order']['status'])")
PAY_METHOD=$(echo "$CHECKOUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('payment_method',''))")
check "Checkout creates order" "$([ -n "$ORDER_ID" ] && echo 1 || echo 0)"
check "COD checkout confirms order" "$([ "$ORDER_STATUS" = "confirmed" ] && [ "$PAY_METHOD" = "cod" ] && echo 1 || echo 0)"

# Order history
ORDERS=$(curl -sf -H "Authorization: Bearer $TOKEN" "$API/orders" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
check "Order history for user" "$([ "${ORDERS:-0}" -ge 1 ] && echo 1 || echo 0)"

# Idempotency replay
CHECKOUT2=$(curl -sf -c "$COOKIE_JAR" -b "$COOKIE_JAR" -X POST "$API/orders/checkout" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: $IDEM" \
  -d "{\"address_id\":\"$ADDR_ID\",\"payment_method\":\"cod\"}")
ORDER_ID2=$(echo "$CHECKOUT2" | python3 -c "import sys,json; print(json.load(sys.stdin)['order']['id'])")
check "Idempotency returns same order" "$([ "$ORDER_ID" = "$ORDER_ID2" ] && echo 1 || echo 0)"

# Web
WEB_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$WEB")
check "Web homepage (200)" "$([ "$WEB_STATUS" = "200" ] && echo 1 || echo 0)"

WEB_CART=$(curl -sf -o /dev/null -w "%{http_code}" "$WEB/cart")
check "Web cart page (200)" "$([ "$WEB_CART" = "200" ] && echo 1 || echo 0)"

WEB_ACCT=$(curl -sf -o /dev/null -w "%{http_code}" "$WEB/account")
check "Web account page (200)" "$([ "$WEB_ACCT" = "200" ] && echo 1 || echo 0)"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
rm -f "$COOKIE_JAR"
[ "$FAIL" -eq 0 ]
