#!/usr/bin/env python3
"""
Test MT5 Reconnect Logic
Kiểm tra logic connect/reconnect/ensure_connected
"""

import time
from engine.mt5_adapter import MT5Adapter

print("=" * 60)
print("TEST MT5 RECONNECT LOGIC")
print("=" * 60)

adapter = MT5Adapter()

# Test 1: Kết nối lần đầu
print("\n[Test 1] Kết nối lần đầu...")
result = adapter.connect()
print(f"✓ Connected: {result}")

# Test 2: Kiểm tra connection status
print("\n[Test 2] Kiểm tra connection status...")
is_connected = adapter.is_connected()
print(f"✓ Is connected: {is_connected}")

# Test 3: Connect lại khi đã connected (không nên shutdown)
print("\n[Test 3] Connect lại khi đã connected (không nên shutdown)...")
print("Expected: Sẽ detect đã connected và return True mà KHÔNG shutdown")
result = adapter.connect()
print(f"✓ Connect again: {result}")

# Test 4: Get account info (auto reconnect nếu cần)
print("\n[Test 4] Get account info...")
account = adapter.get_account_info()
if account:
    print(f"✓ Account: {account['login']}")
    print(f"  Balance: ${account['balance']:.2f}")
    print(f"  Equity: ${account['equity']:.2f}")
else:
    print("✗ Failed to get account info")

# Test 5: Ensure connected
print("\n[Test 5] Ensure connected...")
result = adapter.ensure_connected()
print(f"✓ Ensure connected: {result}")

# Test 6: Force reconnect
print("\n[Test 6] Force reconnect...")
print("Expected: Sẽ shutdown và reconnect lại")
result = adapter.connect(force_reconnect=True)
print(f"✓ Force reconnect: {result}")

# Test 7: Get symbol info (test reconnect nếu bị disconnect)
print("\n[Test 7] Get symbol info...")
symbol_info = adapter.get_symbol_info("XAUUSD")
if symbol_info:
    print(f"✓ Symbol: {symbol_info['name']}")
    print(f"  Bid: {symbol_info['bid']}")
    print(f"  Ask: {symbol_info['ask']}")
else:
    print("✗ Failed to get symbol info")

# Test 8: Disconnect
print("\n[Test 8] Disconnect...")
adapter.disconnect()
print("✓ Disconnected")

# Test 9: Ensure connected sau khi disconnect
print("\n[Test 9] Ensure connected sau khi disconnect...")
print("Expected: Sẽ tự động reconnect")
result = adapter.ensure_connected()
print(f"✓ Auto reconnect: {result}")

# Final cleanup
print("\n[Cleanup] Final disconnect...")
adapter.disconnect()
print("✓ Done")

print("\n" + "=" * 60)
print("✅ TẤT CẢ TEST HOÀN TẤT")
print("=" * 60)
