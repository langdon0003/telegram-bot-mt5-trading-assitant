#!/usr/bin/env python3
"""
Script kiểm tra kết nối MT5
Chạy để debug vấn đề IPC timeout
"""

import MetaTrader5 as mt5
import os
import time

print("=" * 60)
print("KIỂM TRA KẾT NỐI MT5")
print("=" * 60)

# Bước 1: Kiểm tra MT5 có đang chạy không
print("\n1. Kiểm tra MT5 terminal...")
print("   Vui lòng đảm bảo MetaTrader 5 đang MỞ!")
input("   Nhấn Enter để tiếp tục...")

# Bước 2: Thử shutdown trước (clear any existing connections)
print("\n2. Dọn dẹp connections cũ...")
try:
    mt5.shutdown()
    print("   ✓ Shutdown OK")
    time.sleep(2)  # Đợi 2 giây để tránh IPC timeout
except Exception as e:
    print(f"   ⚠️  Shutdown warning: {e}")

# Bước 3: Initialize với retry logic
print("\n3. Initialize MT5 (với retry logic)...")
max_retries = 3
retry_delay = 2

for attempt in range(1, max_retries + 1):
    print(f"   Attempt {attempt}/{max_retries}...", end=" ")

    if mt5.initialize():
        print("✓ OK")
        break
    else:
        error = mt5.last_error()
        print(f"✗ FAILED: {error}")

        if attempt < max_retries:
            print(f"   Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print("\n" + "=" * 60)
            print("INITIALIZE FAILED AFTER 3 ATTEMPTS")
            print("=" * 60)
            print("NGUYÊN NHÂN CÓ THỂ:")
            print("1. MT5 terminal không mở")
            print("2. MT5 bị block bởi antivirus/firewall")
            print("3. MT5 đang bị crash hoặc freeze")
            print("4. Thiếu quyền truy cập MT5")
            print("5. MT5 terminal đang busy (đang connect/disconnect)")
            print("\nGIẢI PHÁP:")
            print("- Đóng MT5 hoàn toàn")
            print("- Đợi 10 giây")
            print("- Mở lại MT5")
            print("- Chờ MT5 load xong (thấy chart hiển thị)")
            print("- Đợi thêm 5 giây")
            print("- Chạy lại script này")
            exit(1)

# Bước 4: Load env variables
print("\n4. Đọc credentials từ .env...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("   ✓ Loaded .env")
except:
    print("   ⚠️  No .env, using system env")

login = os.getenv("MT5_LOGIN")
password = os.getenv("MT5_PASSWORD")
server = os.getenv("MT5_SERVER")

print(f"   Login: {login}")
print(f"   Server: {server}")
print(f"   Password: {'***' if password else 'NOT SET'}")

# Bước 5: Thử login
if login and password and server:
    print("\n5. Thử login vào MT5...")
    authorized = mt5.login(login=int(login), password=password, server=server)

    if not authorized:
        error = mt5.last_error()
        print(f"   ✗ Login FAILED: {error}")
        print("\n" + "=" * 60)
        print("LOGIN FAILED - KIỂM TRA:")
        print("=" * 60)
        print("1. Login số có đúng không?")
        print("2. Password có đúng không?")
        print("3. Server name có đúng không?")
        print("4. Tài khoản có bị khóa không?")
        print("5. Internet có kết nối không?")
        mt5.shutdown()
        exit(1)

    print("   ✓ Login OK")
else:
    print("\n5. Không có credentials, dùng session hiện tại")

# Bước 6: Lấy account info
print("\n6. Lấy thông tin account...")
account_info = mt5.account_info()

if account_info is None:
    print("   ✗ Không lấy được account info")
    print("   MT5 có đang login không?")
    mt5.shutdown()
    exit(1)

print("   ✓ Account info OK")
print(f"\n{'=' * 60}")
print("✅ KẾT NỐI THÀNH CÔNG!")
print("=" * 60)
print(f"Account: {account_info.login}")
print(f"Name: {account_info.name}")
print(f"Server: {account_info.server}")
print(f"Balance: ${account_info.balance:.2f}")
print(f"Equity: ${account_info.equity:.2f}")
print(f"Margin: ${account_info.margin:.2f}")
print(f"Currency: {account_info.currency}")
print(f"Leverage: 1:{account_info.leverage}")
print("=" * 60)

# Bước 7: Shutdown
print("\n7. Ngắt kết nối...")
mt5.shutdown()
print("   ✓ Disconnected")

print("\n" + "=" * 60)
print("✅ TẤT CẢ OK - Bot có thể kết nối MT5!")
print("=" * 60)
