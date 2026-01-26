#!/usr/bin/env python3
"""
Script để fix IPC timeout error với MT5
Chạy script này trước khi chạy bot nếu gặp IPC timeout
"""

import MetaTrader5 as mt5
import time
import sys

print("=" * 70)
print("FIX MT5 IPC TIMEOUT ERROR")
print("=" * 70)

print("\n📋 CHECKLIST:")
print("1. ☑️  MT5 terminal đang MỞ")
print("2. ☑️  Không có Python script nào khác đang kết nối MT5")
print("3. ☑️  MT5 không bị freeze hoặc crash")
print("")

input("Nhấn Enter khi đã sẵn sàng...")

# Step 1: Aggressive shutdown
print("\n[Step 1] Shutdown tất cả connections...")
try:
    for i in range(3):
        mt5.shutdown()
        time.sleep(1)
    print("✓ Shutdown hoàn tất")
except Exception as e:
    print(f"⚠️  Warning: {e}")

# Wait longer
print("\n[Step 2] Đợi MT5 giải phóng resources...")
for i in range(5, 0, -1):
    print(f"   {i} giây...", end="\r")
    time.sleep(1)
print("   ✓ Đã đợi 5 giây")

# Step 3: Try initialize with multiple attempts
print("\n[Step 3] Thử initialize với retry logic...")
max_attempts = 5
retry_delay = 3

for attempt in range(1, max_attempts + 1):
    print(f"\n   Attempt {attempt}/{max_attempts}:")

    # Try initialize
    print(f"      Calling mt5.initialize()...", end=" ")
    result = mt5.initialize()

    if result:
        print("✓ SUCCESS!")

        # Verify connection
        print(f"      Verifying connection...", end=" ")
        account_info = mt5.account_info()

        if account_info:
            print("✓ OK")
            print("\n" + "=" * 70)
            print("✅ FIX THÀNH CÔNG!")
            print("=" * 70)
            print(f"Account: {account_info.login}")
            print(f"Server: {account_info.server}")
            print(f"Balance: ${account_info.balance:.2f}")
            print("\nBây giờ bạn có thể chạy bot:")
            print("   python run_bot.py")
            print("=" * 70)

            # Cleanup
            mt5.shutdown()
            sys.exit(0)
        else:
            print("✗ FAILED")
            mt5.shutdown()
    else:
        error = mt5.last_error()
        print(f"✗ FAILED: {error}")

        if attempt < max_attempts:
            print(f"      Đợi {retry_delay} giây trước khi retry...")
            time.sleep(retry_delay)

# Failed after all attempts
print("\n" + "=" * 70)
print("❌ KHÔNG THỂ FIX - CẦN TROUBLESHOOT THỦ CÔNG")
print("=" * 70)
print("\nVẤN ĐỀ:")
print("- MT5 không phản hồi sau 5 attempts")
print("- Có thể MT5 đang bị lock bởi process khác")
print("\nGIẢI PHÁP:")
print("\n1. ĐÓNG HOÀN TOÀN MT5:")
print("   - Nhấn chuột phải vào MT5 icon ở taskbar")
print("   - Chọn 'Close' hoặc 'Exit'")
print("   - Đợi 10 giây")
print("\n2. KILL PROCESS (nếu cần):")
print("   - Mở Task Manager (Ctrl+Shift+Esc)")
print("   - Tìm 'terminal64.exe' hoặc 'MetaTrader'")
print("   - Nhấn 'End Task'")
print("   - Đợi 10 giây")
print("\n3. RESTART MT5:")
print("   - Mở MT5 lại")
print("   - Đợi login xong")
print("   - Đợi chart load xong")
print("   - Đợi thêm 5 giây")
print("\n4. CHẠY LẠI SCRIPT NÀY:")
print("   python fix_ipc_timeout.py")
print("\n5. NẾU VẪN LỖI:")
print("   - Restart Windows")
print("   - Reinstall MetaTrader5 Python package:")
print("     pip uninstall MetaTrader5")
print("     pip install MetaTrader5")
print("=" * 70)

sys.exit(1)
