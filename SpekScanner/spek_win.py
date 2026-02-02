"""
SPEKSCANNER - Pembaca Spesifikasi Laptop/PC
Versi 1.0 - Windows
"""

import platform
import psutil
import cpuinfo
from datetime import datetime
import json

class SimpleSpecScanner:
    def __init__(self):
        self.specs = {}
    
    def scan_all(self):
        """Scan semua komponen"""
        print("🔍 Memulai pemindaian sistem...")
        
        self.specs['scan_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.specs['system'] = self.get_system_info()
        self.specs['cpu'] = self.get_cpu_info()
        self.specs['ram'] = self.get_ram_info()
        self.specs['disk'] = self.get_disk_info()
        self.specs['network'] = self.get_network_info()
        
        return self.specs
    
    def get_system_info(self):
        """Informasi sistem dasar"""
        return {
            'os': f"{platform.system()} {platform.release()}",
            'version': platform.version(),
            'architecture': platform.architecture()[0],
            'hostname': platform.node(),
            'python_version': platform.python_version()
        }
    
    def get_cpu_info(self):
        """Informasi CPU"""
        try:
            cpu_info = cpuinfo.get_cpu_info()
            return {
                'nama': cpu_info.get('brand_raw', 'Tidak terdeteksi'),
                'arch': cpu_info.get('arch_string_raw', 'Tidak terdeteksi'),
                'bits': cpu_info.get('bits', 'Tidak terdeteksi'),
                'kecepatan': f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "Tidak terdeteksi",
                'core_fisik': psutil.cpu_count(logical=False),
                'core_logikal': psutil.cpu_count(logical=True),
                'pemakaian': f"{psutil.cpu_percent()}%"
            }
        except:
            return {'error': 'Gagal membaca CPU'}
    
    def get_ram_info(self):
        """Informasi RAM"""
        try:
            mem = psutil.virtual_memory()
            return {
                'total': f"{mem.total / (1024**3):.2f} GB",
                'tersedia': f"{mem.available / (1024**3):.2f} GB",
                'terpakai': f"{mem.used / (1024**3):.2f} GB",
                'persentase': f"{mem.percent}%"
            }
        except:
            return {'error': 'Gagal membaca RAM'}
    
    def get_disk_info(self):
        """Informasi Disk"""
        try:
            disks = []
            for partition in psutil.disk_partitions():
                if 'cdrom' in partition.opts or not partition.fstype:
                    continue
                
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        'drive': partition.device,
                        'tipe': partition.fstype,
                        'total': f"{usage.total / (1024**3):.2f} GB",
                        'terpakai': f"{usage.used / (1024**3):.2f} GB",
                        'kosong': f"{usage.free / (1024**3):.2f} GB",
                        'persentase': f"{usage.percent}%"
                    })
                except:
                    continue
            
            return disks
        except:
            return [{'error': 'Gagal membaca disk'}]
    
    def get_network_info(self):
        """Informasi Network"""
        try:
            interfaces = []
            net_addrs = psutil.net_if_addrs()
            
            for interface, addresses in net_addrs.items():
                for addr in addresses:
                    if addr.family.name == 'AF_INET':  # IPv4
                        interfaces.append({
                            'interface': interface,
                            'ip': addr.address,
                            'netmask': addr.netmask
                        })
            
            return interfaces
        except:
            return [{'error': 'Gagal membaca network'}]
    
    def display_results(self):
        """Tampilkan hasil di console"""
        print("\n" + "="*60)
        print("LAPORAN SPESIFIKASI SISTEM CLI")
        print("="*60)
        
        print(f"\n📅 Waktu Scan: {self.specs.get('scan_time')}")
        
        print("\n🖥️ SISTEM:")
        for key, value in self.specs.get('system', {}).items():
            print(f"  {key}: {value}")
        
        print("\n⚡ CPU:")
        for key, value in self.specs.get('cpu', {}).items():
            print(f"  {key}: {value}")
        
        print("\n💾 RAM:")
        for key, value in self.specs.get('ram', {}).items():
            print(f"  {key}: {value}")
        
        print("\n💿 DISK:")
        for disk in self.specs.get('disk', []):
            if isinstance(disk, dict):
                print(f"  Drive: {disk.get('drive', 'N/A')}")
                for key, value in disk.items():
                    if key != 'drive':
                        print(f"    {key}: {value}")
        
        print("\n🌐 NETWORK:")
        for net in self.specs.get('network', []):
            if isinstance(net, dict):
                for key, value in net.items():
                    print(f"  {key}: {value}")
        
        print("\n" + "="*60)
    
    def save_to_file(self, filename="spek_laporan.txt"):
        """Simpan hasil ke file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("LAPORAN SPESIFIKASI SISTEM\n")
                f.write("="*60 + "\n\n")
                
                f.write(f"Waktu Scan: {self.specs.get('scan_time')}\n\n")
                
                f.write("SISTEM:\n")
                for key, value in self.specs.get('system', {}).items():
                    f.write(f"  {key}: {value}\n")
                
                f.write("\nCPU:\n")
                for key, value in self.specs.get('cpu', {}).items():
                    f.write(f"  {key}: {value}\n")
                
                f.write("\nRAM:\n")
                for key, value in self.specs.get('ram', {}).items():
                    f.write(f"  {key}: {value}\n")
                
                f.write("\nDISK:\n")
                for disk in self.specs.get('disk', []):
                    if isinstance(disk, dict):
                        f.write(f"  Drive: {disk.get('drive', 'N/A')}\n")
                        for key, value in disk.items():
                            if key != 'drive':
                                f.write(f"    {key}: {value}\n")
                
                f.write("\nNETWORK:\n")
                for net in self.specs.get('network', []):
                    if isinstance(net, dict):
                        for key, value in net.items():
                            f.write(f"  {key}: {value}\n")
                
                f.write("\n" + "="*60)
            
            # Simpan juga ke JSON untuk parsing mudah
            with open("spek_laporan.json", 'w', encoding='utf-8') as f:
                json.dump(self.specs, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Laporan disimpan sebagai:")
            print(f"   - {filename}")
            print(f"   - spek_laporan.json")
            
        except Exception as e:
            print(f"❌ Error menyimpan file: {e}")

def main():
    """Fungsi utama"""
    print("🔥 SPEKSCANNER - Pembaca Spesifikasi Sistem")
    print("Versi 1.0 - Windows\n")
    
    scanner = SimpleSpecScanner()
    scanner.scan_all()
    scanner.display_results()
    scanner.save_to_file()
    
    input("\nTekan Enter untuk keluar...")

if __name__ == "__main__":
    main()