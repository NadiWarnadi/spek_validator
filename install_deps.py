import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    packages = ["psutil", "wmi", "py-cpuinfo", "GPUtil"]
    print("Menginstall dependencies...")
    for package in packages:
        try:
            print(f"Installing {package}...")
            install(package)
            print(f"✅ {package} berhasil diinstall")
        except Exception as e:
            print(f"❌ Gagal install {package}: {e}")
    
    print("\n✅ Selesai! Tekan Enter untuk keluar...")
    input()