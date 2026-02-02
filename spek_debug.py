import psutil
import platform

print("🔍 DEBUG MODE - Cek library")

# Test RAM
try:
    mem = psutil.virtual_memory()
    print(f"✅ RAM OK: {mem.total / (1024**3):.2f} GB")
except Exception as e:
    print(f"❌ RAM ERROR: {e}")

# Test Disk
try:
    for part in psutil.disk_partitions():
        print(f"✅ Partition: {part.device} -> {part.mountpoint}")
except Exception as e:
    print(f"❌ DISK ERROR: {e}")

# Test Network
try:
    net = psutil.net_if_addrs()
    print(f"✅ Network interfaces: {len(net)} found")
except Exception as e:
    print(f"❌ NETWORK ERROR: {e}")

input("\nTekan Enter...")