"""
SPEKSCANNER v2.0 - Windows System Scanner
Dengan error reporting yang lebih baik
"""

import platform
import sys
import os
from datetime import datetime

def install_dependencies():
    """Install dependencies dengan feedback lebih baik"""
    print("📦 Menginstal dependencies...")
    
    deps = [
        ('psutil', 'psutil'),
        ('wmi', 'wmi'),
        ('cpuinfo', 'py-cpuinfo'),
        ('GPUtil', 'GPUtil')
    ]
    
    for import_name, pip_name in deps:
        try:
            __import__(import_name)
            print(f"  ✅ {import_name} sudah terinstall")
        except ImportError:
            print(f"  ⏳ Menginstall {import_name}...")
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "--quiet"])
                print(f"  ✅ {import_name} berhasil diinstall")
            except:
                print(f"  ❌ Gagal install {import_name}")
                return False
    return True

def get_cpu_info():
    """Info CPU dengan multiple fallback"""
    info = {}
    try:
        import cpuinfo
        import psutil
        
        # Method 1: cpuinfo
        cpu_data = cpuinfo.get_cpu_info()
        info.update({
            'Nama Processor': cpu_data.get('brand_raw', 'Tidak diketahui'),
            'Arsitektur': cpu_data.get('arch_string_raw', platform.machine()),
            'Bits': cpu_data.get('bits', platform.architecture()[0]),
            'Vendor': cpu_data.get('vendor_id_raw', 'Tidak diketahui')
        })
        
        # Method 2: psutil
        if psutil.cpu_freq():
            info['Kecepatan'] = f"{psutil.cpu_freq().current:.2f} MHz"
            info['Kecepatan Max'] = f"{psutil.cpu_freq().max:.2f} MHz"
        
        info.update({
            'Core Fisik': psutil.cpu_count(logical=False),
            'Core Logikal': psutil.cpu_count(logical=True),
            'Pemakaian CPU': f"{psutil.cpu_percent()}%"
        })
        
    except Exception as e:
        info = {
            'Processor': platform.processor(),
            'Error Detail': str(e)
        }
    
    return info

def get_ram_info():
    """Info RAM dengan fallback ke WMIC"""
    info = {}
    try:
        import psutil
        mem = psutil.virtual_memory()
        info.update({
            'Total RAM': f"{mem.total / (1024**3):.2f} GB",
            'Tersedia': f"{mem.available / (1024**3):.2f} GB",
            'Terpakai': f"{mem.used / (1024**3):.2f} GB",
            'Persentase Terpakai': f"{mem.percent}%"
        })
    except Exception as e:
        # Fallback ke WMIC command
        try:
            import subprocess
            result = subprocess.run(
                'wmic memorychip get Capacity',
                capture_output=True,
                text=True,
                shell=True
            )
            # Parse hasil wmic
            lines = result.stdout.strip().split('\n')
            total_bytes = 0
            for line in lines[1:]:  # Skip header
                if line.strip().isdigit():
                    total_bytes += int(line.strip())
            
            if total_bytes > 0:
                info['Total RAM'] = f"{total_bytes / (1024**3):.2f} GB"
            else:
                info['Error'] = 'Tidak bisa membaca RAM'
                
        except:
            info['Error'] = f'Gagal membaca RAM: {str(e)}'
    
    return info

def get_disk_info():
    """Info Disk dengan berbagai metode"""
    disks = []
    
    # Method 1: psutil
    try:
        import psutil
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'Drive': partition.device,
                    'Tipe': partition.fstype or 'Unknown',
                    'Total': f"{usage.total / (1024**3):.2f} GB",
                    'Terpakai': f"{usage.used / (1024**3):.2f} GB",
                    'Kosong': f"{usage.free / (1024**3):.2f} GB",
                    'Persentase': f"{usage.percent}%"
                })
            except:
                disks.append({
                    'Drive': partition.device,
                    'Status': 'Tidak bisa diakses'
                })
    except:
        # Method 2: Cek drive manual
        import string
        for drive_letter in string.ascii_uppercase:
            drive = f"{drive_letter}:\\"
            if os.path.exists(drive):
                try:
                    import shutil
                    total, used, free = shutil.disk_usage(drive)
                    disks.append({
                        'Drive': drive,
                        'Total': f"{total / (1024**3):.2f} GB",
                        'Terpakai': f"{used / (1024**3):.2f} GB",
                        'Kosong': f"{free / (1024**3):.2f} GB"
                    })
                except:
                    continue
    
    return disks if disks else [{'Status': 'Tidak ada disk terdeteksi'}]

def get_gpu_info():
    """Info GPU dengan multiple method"""
    gpus = []
    
    # Method 1: GPUtil (NVIDIA)
    try:
        import GPUtil
        nvidia_gpus = GPUtil.getGPUs()
        for gpu in nvidia_gpus:
            gpus.append({
                'Jenis': 'NVIDIA',
                'Nama': gpu.name,
                'Memory': f"{gpu.memoryTotal} MB",
                'Driver': gpu.driver,
                'Suhu': f"{gpu.temperature}°C"
            })
    except:
        pass
    
    # Method 2: WMI (all GPUs)
    try:
        import wmi
        c = wmi.WMI()
        for gpu in c.Win32_VideoController():
            if gpu.Name and 'Microsoft Basic' not in gpu.Name:
                gpus.append({
                    'Jenis': 'Generic',
                    'Nama': gpu.Name,
                    'Driver': gpu.DriverVersion or 'Unknown',
                    'Memory': f"{int(gpu.AdapterRAM) / (1024**2):.0f} MB" if gpu.AdapterRAM else 'Unknown'
                })
    except:
        pass
    
    return gpus if gpus else [{'Status': 'GPU tidak terdeteksi'}]

def get_network_info():
    """Info Network"""
    interfaces = []
    try:
        import psutil
        net_addrs = psutil.net_if_addrs()
        
        for iface, addrs in net_addrs.items():
            for addr in addrs:
                if addr.family.name == 'AF_INET':  # IPv4
                    interfaces.append({
                        'Interface': iface,
                        'IP Address': addr.address,
                        'Netmask': addr.netmask
                    })
    except Exception as e:
        interfaces.append({'Error': f'Tidak bisa membaca network: {str(e)}'})
    
    return interfaces

def get_bios_info():
    """Info BIOS"""
    info = {}
    try:
        import wmi
        c = wmi.WMI()
        for bios in c.Win32_BIOS():
            info = {
                'Manufacturer': bios.Manufacturer or 'Unknown',
                'Version': bios.Version or 'Unknown',
                'Release Date': bios.ReleaseDate.split('T')[0] if bios.ReleaseDate else 'Unknown'
            }
            break
    except:
        info = {'Status': 'Informasi BIOS tidak tersedia'}
    
    return info

def display_section(title, data):
    """Tampilkan section dengan format rapi"""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    
    if isinstance(data, dict):
        for key, value in data.items():
            print(f"  {key}: {value}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    print(f"  {key}: {value}")
                print()  # Spasi antar item
            else:
                print(f"  {item}")
    else:
        print(f"  {data}")

def save_report(specs, filename=None):
    """Simpan laporan ke file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"spek_laporan_{timestamp}"
    
    txt_file = f"{filename}.txt"
    json_file = f"{filename}.json"
    
    # Save as TXT
    try:
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("LAPORAN SPESIFIKASI SISTEM\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Tanggal: {specs.get('tanggal', 'N/A')}\n")
            f.write(f"Sistem: {specs.get('sistem', {}).get('OS', 'N/A')}\n")
            f.write(f"Hostname: {specs.get('sistem', {}).get('Hostname', 'N/A')}\n\n")
            
            for section in ['sistem', 'cpu', 'ram', 'disk', 'gpu', 'network', 'bios']:
                if section in specs:
                    f.write(f"[{section.upper()}]\n")
                    data = specs[section]
                    
                    if isinstance(data, dict):
                        for key, value in data.items():
                            f.write(f"  {key}: {value}\n")
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                for key, value in item.items():
                                    f.write(f"  {key}: {value}\n")
                                f.write("\n")
                            else:
                                f.write(f"  {item}\n")
                    f.write("\n")
        
        print(f"✅ Laporan disimpan: {txt_file}")
    except Exception as e:
        print(f"❌ Gagal menyimpan TXT: {e}")
    
    # Save as JSON
    try:
        import json
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(specs, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON disimpan: {json_file}")
    except:
        print("❌ Gagal menyimpan JSON")

def main():
    """Program utama"""
    print("🔥 SPEKSCANNER v2.0 - System Specification Scanner")
    print("="*60)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Ada masalah dengan dependencies.")
        print("Coba install manual: python -m pip install psutil wmi py-cpuinfo GPUtil")
        input("\nTekan Enter untuk keluar...")
        return
    
    print("\n🔍 Memindai sistem... Harap tunggu...")
    
    # Kumpulkan semua data
    specs = {
        'tanggal': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'sistem': {
            'OS': f"{platform.system()} {platform.release()}",
            'Versi': platform.version(),
            'Arsitektur': platform.architecture()[0],
            'Hostname': platform.node(),
            'Python': platform.python_version()
        },
        'cpu': get_cpu_info(),
        'ram': get_ram_info(),
        'disk': get_disk_info(),
        'gpu': get_gpu_info(),
        'network': get_network_info(),
        'bios': get_bios_info()
    }
    
    # Tampilkan hasil
    display_section("SISTEM OPERASI", specs['sistem'])
    display_section("PROCESSOR (CPU)", specs['cpu'])
    display_section("MEMORY (RAM)", specs['ram'])
    display_section("STORAGE (DISK)", specs['disk'])
    display_section("GRAPHICS (GPU)", specs['gpu'])
    display_section("NETWORK", specs['network'])
    display_section("BIOS", specs['bios'])
    
    # Simpan ke file
    print("\n" + "="*60)
    save = input("Simpan laporan ke file? (y/n): ").lower()
    if save == 'y':
        save_report(specs)
    
    print("\n" + "="*60)
    print("✅ Pemindaian selesai!")
    input("\nTekan Enter untuk keluar...")

if __name__ == "__main__":
    main()