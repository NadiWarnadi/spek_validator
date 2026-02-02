import platform
import psutil
import cpuinfo
import wmi
import GPUtil
from datetime import datetime

class SystemSpecs:
    def __init__(self):
        self.c = wmi.WMI()  # WMI untuk Windows-specific
        self.specs = {}
        
    def get_all_info(self):
        """Kumpulkan semua informasi"""
        self.get_basic_info()
        self.get_cpu_info()
        self.get_ram_info()
        self.get_disk_info()
        self.get_gpu_info()
        self.get_network_info()
        self.get_bios_info()
        return self.specs
    
    def get_basic_info(self):
        """Informasi dasar sistem"""
        self.specs['Basic'] = {
            'Sistem Operasi': f"{platform.system()} {platform.release()}",
            'Versi OS': platform.version(),
            'Arsitektur': platform.architecture()[0],
            'Hostname': platform.node(),
            'Waktu Sistem': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Python Version': platform.python_version()
        }
    
    def get_cpu_info(self):
        """Detail CPU"""
        try:
            # Menggunakan cpuinfo untuk detail lengkap
            cpu_info = cpuinfo.get_cpu_info()
            
            # Info dari WMI (lebih akurat untuk Windows)
            for processor in self.c.Win32_Processor():
                cpu_wmi = {
                    'Nama': processor.Name.strip(),
                    'Manufacturer': processor.Manufacturer,
                    'Jumlah Core': processor.NumberOfCores,
                    'Jumlah Thread': processor.NumberOfLogicalProcessors,
                    'Kecepatan Base': f"{processor.MaxClockSpeed} MHz",
                    'Cache L2': f"{processor.L2CacheSize} KB" if processor.L2CacheSize else "N/A",
                    'Cache L3': f"{processor.L3CacheSize} KB" if processor.L3CacheSize else "N/A",
                    'CPU ID': processor.ProcessorId
                }
                break  # Ambil processor pertama saja
            
            # Gabungkan informasi
            self.specs['CPU'] = {
                **cpu_wmi,
                'Brand': cpu_info.get('brand_raw', 'N/A'),
                'Architecture': cpu_info.get('arch_string_raw', 'N/A'),
                'Bits': cpu_info.get('bits', 'N/A'),
                'CPU Pakai Sekarang': f"{psutil.cpu_percent()}%",
                'Frekuensi Max': f"{psutil.cpu_freq().max:.2f} MHz" if psutil.cpu_freq() else "N/A",
            }
        except Exception as e:
            self.specs['CPU'] = {'Error': f"Gagal membaca CPU: {str(e)}"}
    
    def get_ram_info(self):
        """Detail RAM"""
        try:
            mem = psutil.virtual_memory()
            
            # Ambil info dari WMI untuk detail RAM stick
            ram_modules = []
            for mem_module in self.c.Win32_PhysicalMemory():
                ram_modules.append({
                    'Kapasitas': f"{int(mem_module.Capacity) / (1024**3):.2f} GB",
                    'Speed': f"{mem_module.Speed} MHz",
                    'Manufacturer': mem_module.Manufacturer or 'Unknown',
                    'Part Number': mem_module.PartNumber or 'Unknown',
                    'Type': mem_module.MemoryType
                })
            
            self.specs['RAM'] = {
                'Total RAM': f"{mem.total / (1024**3):.2f} GB",
                'Available': f"{mem.available / (1024**3):.2f} GB",
                'Used Percentage': f"{mem.percent}%",
                'Used': f"{mem.used / (1024**3):.2f} GB",
                'RAM Modules': ram_modules if ram_modules else "Tidak terdeteksi"
            }
        except Exception as e:
            self.specs['RAM'] = {'Error': f"Gagal membaca RAM: {str(e)}"}
    
    def get_disk_info(self):
        """Detail Disk/Storage"""
        try:
            disks = []
            
            # Partisi dari psutil
            for partition in psutil.disk_partitions():
                if 'cdrom' in partition.opts or partition.fstype == '':
                    continue
                
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'Drive': partition.device,
                    'Mount Point': partition.mountpoint,
                    'File System': partition.fstype,
                    'Total Size': f"{usage.total / (1024**3):.2f} GB",
                    'Used': f"{usage.used / (1024**3):.2f} GB",
                    'Free': f"{usage.free / (1024**3):.2f} GB",
                    'Percentage Used': f"{usage.percent}%"
                })
            
            # Info fisik disk dari WMI
            physical_disks = []
            for disk in self.c.Win32_DiskDrive():
                size_gb = int(disk.Size) / (1024**3) if disk.Size else 0
                physical_disks.append({
                    'Model': disk.Model or 'Unknown',
                    'Size': f"{size_gb:.2f} GB",
                    'Interface': disk.InterfaceType or 'Unknown',
                    'Serial': disk.SerialNumber or 'N/A'
                })
            
            self.specs['Storage'] = {
                'Partitions': disks,
                'Physical Disks': physical_disks
            }
        except Exception as e:
            self.specs['Storage'] = {'Error': f"Gagal membaca storage: {str(e)}"}
    
    def get_gpu_info(self):
        """Detail GPU"""
        try:
            gpus = []
            
            # Coba GPU NVIDIA dengan GPUtil
            try:
                nvidia_gpus = GPUtil.getGPUs()
                for gpu in nvidia_gpus:
                    gpus.append({
                        'Name': gpu.name,
                        'Driver': gpu.driver,
                        'Memory Total': f"{gpu.memoryTotal} MB",
                        'Memory Free': f"{gpu.memoryFree} MB",
                        'Memory Used': f"{gpu.memoryUsed} MB",
                        'GPU Load': f"{gpu.load * 100}%",
                        'Temperature': f"{gpu.temperature} °C"
                    })
            except:
                pass
            
            # Cek GPU dari WMI (untuk semua GPU)
            for gpu in self.c.Win32_VideoController():
                if gpu.Name and 'Microsoft Basic' not in gpu.Name:
                    gpus.append({
                        'Name': gpu.Name,
                        'Adapter RAM': f"{int(gpu.AdapterRAM) / (1024**2):.2f} MB" if gpu.AdapterRAM else "N/A",
                        'Driver Version': gpu.DriverVersion or 'N/A',
                        'Resolution': f"{gpu.CurrentHorizontalResolution}x{gpu.CurrentVerticalResolution}" 
                                    if gpu.CurrentHorizontalResolution else "N/A"
                    })
            
            self.specs['GPU'] = gpus if gpus else "Tidak ada GPU dedicated terdeteksi"
            
        except Exception as e:
            self.specs['GPU'] = {'Error': f"Gagal membaca GPU: {str(e)}"}
    
    def get_network_info(self):
        """Info Network"""
        try:
            net_info = psutil.net_if_addrs()
            interfaces = []
            
            for interface_name, interface_addresses in net_info.items():
                for address in interface_addresses:
                    if str(address.family) == 'AddressFamily.AF_INET':  # IPv4
                        interfaces.append({
                            'Interface': interface_name,
                            'IP Address': address.address,
                            'Netmask': address.netmask
                        })
            
            self.specs['Network'] = {
                'Interfaces': interfaces,
                'Hostname': platform.node()
            }
        except Exception as e:
            self.specs['Network'] = {'Error': f"Gagal membaca network: {str(e)}"}
    
    def get_bios_info(self):
        """Info BIOS"""
        try:
            for bios in self.c.Win32_BIOS():
                self.specs['BIOS'] = {
                    'Manufacturer': bios.Manufacturer or 'Unknown',
                    'Version': bios.Version or 'N/A',
                    'Release Date': bios.ReleaseDate.split('T')[0] if bios.ReleaseDate else 'N/A',
                    'SMBIOS Version': bios.SMBIOSBIOSVersion or 'N/A'
                }
                break
        except:
            self.specs['BIOS'] = "Informasi BIOS tidak tersedia"

def display_specs(specs):
    """Tampilkan spesifikasi secara rapi"""
    print("=" * 60)
    print("SYSTEM SPECIFICATION SCANNER")
    print("=" * 60)
    
    for category, data in specs.items():
        print(f"\n[{category}]")
        print("-" * 40)
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    print(f"  {key}:")
                    for item in value:
                        if isinstance(item, dict):
                            for subkey, subvalue in item.items():
                                print(f"    {subkey}: {subvalue}")
                        else:
                            print(f"    {item}")
                else:
                    print(f"  {key}: {value}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    for key, value in item.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {item}")
        else:
            print(f"  {data}")

def save_to_file(specs, filename="system_specs.txt"):
    """Simpan hasil ke file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("SYSTEM SPECIFICATION REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        for category, data in specs.items():
            f.write(f"[{category}]\n")
            f.write("-" * 40 + "\n")
            
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        f.write(f"  {key}:\n")
                        for item in value:
                            if isinstance(item, dict):
                                for subkey, subvalue in item.items():
                                    f.write(f"    {subkey}: {subvalue}\n")
                            else:
                                f.write(f"    {item}\n")
                    else:
                        f.write(f"  {key}: {value}\n")
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            f.write(f"  {key}: {value}\n")
                    else:
                        f.write(f"  {item}\n")
            else:
                f.write(f"  {data}\n")
            f.write("\n")
    
    print(f"\n✅ Hasil disimpan ke: {filename}")

if __name__ == "__main__":
    print("🔍 Memindai spesifikasi sistem... Harap tunggu...\n")
    
    scanner = SystemSpecs()
    specs = scanner.get_all_info()
    
    # Tampilkan di console
    display_specs(specs)
    
    # Simpan ke file
    save_to_file(specs)
    
    # Export ke JSON juga
    import json
    with open("system_specs.json", "w") as f:
        json.dump(specs, f, indent=2, default=str)
    
    print("\n" + "=" * 60)
    print("✅ Pemindaian selesai!")
    print("File tersimpan: system_specs.txt dan system_specs.json")