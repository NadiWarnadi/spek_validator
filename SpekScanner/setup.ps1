# setup.ps1 - Auto Setup SpekScanner
Write-Host "🔥 SETUP SPEKSCANNER v3.0 - CLEAN INSTALL" -ForegroundColor Cyan

# Tentukan path
$projectPath = "C:\read_spek\SpekScanner"

# Buat folder jika belum ada
if (-not (Test-Path $projectPath)) {
    New-Item -ItemType Directory -Path $projectPath
}

# Pindah ke folder
cd $projectPath

# Hapus semua konten kecuali setup.ps1
Write-Host "🗑️  Membersihkan folder..." -ForegroundColor Yellow
Get-ChildItem -Path . -Exclude "setup.ps1" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Buat struktur folder
Write-Host "📁 Membuat struktur folder..." -ForegroundColor Yellow
$folders = @("src", "reports", "dist")
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force
}

# 1. Buat main.py
Write-Host "📝 Membuat main.py..." -ForegroundColor Green
$mainContent = @'
import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.scanner import SystemScanner
from src.utils import display_results, save_report

def main():
    print("🔥 SPEKSCANNER v3.0")
    print("="*60)
    scanner = SystemScanner()
    print("\n🔍 Memindai sistem...")
    specs = scanner.scan_all()
    display_results(specs)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_report(specs, f"reports/spek_laporan_{timestamp}")
    print("\n" + "="*60)
    input("Tekan Enter untuk keluar...")

if __name__ == "__main__":
    main()
'@
Set-Content -Path "src\main.py" -Value $mainContent -Encoding UTF8

# 2. Buat scanner.py (DENGAN FIX CPU BUG)
Write-Host "📝 Membuat scanner.py..." -ForegroundColor Green
$scannerContent = @'
import platform, psutil, cpuinfo, GPUtil, wmi, os, time
from datetime import datetime

class SystemScanner:
    def __init__(self):
        self.specs = {}
        self.wmi_conn = None
    
    def get_wmi_connection(self):
        if self.wmi_conn is None:
            try: self.wmi_conn = wmi.WMI()
            except: self.wmi_conn = False
        return self.wmi_conn
    
    def get_accurate_cpu_usage(self):
        cpu_data = {'total': 0, 'per_core': [], 'user': 0, 'system': 0, 'idle': 0}
        try:
            c = self.get_wmi_connection()
            if c:
                for processor in c.Win32_Processor():
                    if processor.LoadPercentage: cpu_data['total'] = float(processor.LoadPercentage); break
                for perf in c.Win32_PerfFormattedData_PerfOS_Processor():
                    if perf.Name != "_Total" and perf.PercentProcessorTime:
                        cpu_data['per_core'].append(float(perf.PercentProcessorTime))
        except: pass
        
        if cpu_data['total'] == 0:
            psutil.cpu_percent(interval=0.1)
            time.sleep(0.1)
            cpu_data['total'] = psutil.cpu_percent(interval=0.2)
            cpu_data['per_core'] = psutil.cpu_percent(interval=0.2, percpu=True)
            times = psutil.cpu_times_percent(interval=0.2)
            cpu_data['user'] = getattr(times, 'user', 0)
            cpu_data['system'] = getattr(times, 'system', 0)
            cpu_data['idle'] = getattr(times, 'idle', 0)
        return cpu_data
    
    def scan_all(self):
        self.specs['scan_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._scan_system(); self._scan_cpu(); self._scan_ram(); self._scan_disk()
        self._scan_gpu(); self._scan_network(); self._scan_bios(); self._scan_battery()
        return self.specs
    
    def _scan_system(self):
        self.specs['system'] = {
            'OS': f"{platform.system()} {platform.release()}",
            'Version': platform.version(),
            'Architecture': platform.architecture()[0],
            'Hostname': platform.node(),
            'Python': platform.python_version()
        }
    
    def _scan_cpu(self):
        try:
            cpu_info = cpuinfo.get_cpu_info()
            cpu_usage = self.get_accurate_cpu_usage()
            cpu_result = {
                'Name': cpu_info.get('brand_raw', platform.processor()),
                'Architecture': cpu_info.get('arch_string_raw', 'Unknown'),
                'Cores (Physical)': psutil.cpu_count(logical=False),
                'Cores (Logical)': psutil.cpu_count(logical=True),
                'Frequency': f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else 'Unknown'
            }
            if cpu_usage['total'] > 0:
                cpu_result.update({
                    'Usage (Total)': f"{cpu_usage['total']:.1f}%",
                    'Usage (User)': f"{cpu_usage['user']:.1f}%" if cpu_usage['user'] > 0 else 'N/A',
                    'Usage (System)': f"{cpu_usage['system']:.1f}%" if cpu_usage['system'] > 0 else 'N/A'
                })
            self.specs['cpu'] = cpu_result
        except Exception as e:
            self.specs['cpu'] = {'Error': f"CPU scan failed: {str(e)[:50]}"}
    
    def _scan_ram(self):
        try:
            mem = psutil.virtual_memory()
            self.specs['ram'] = {
                'Total': f"{mem.total / (1024**3):.2f} GB",
                'Available': f"{mem.available / (1024**3):.2f} GB",
                'Used': f"{mem.used / (1024**3):.2f} GB",
                'Percentage': f"{mem.percent}%"
            }
        except: self.specs['ram'] = {'Error': 'Failed to read RAM'}
    
    def _scan_disk(self):
        try:
            disks = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        'Drive': partition.device, 'Mount': partition.mountpoint,
                        'Total': f"{usage.total / (1024**3):.2f} GB",
                        'Used': f"{usage.used / (1024**3):.2f} GB",
                        'Free': f"{usage.free / (1024**3):.2f} GB",
                        'Usage': f"{usage.percent}%"
                    })
                except: continue
            self.specs['disk'] = disks
        except: self.specs['disk'] = [{'Error': 'Failed to read Disk'}]
    
    def _scan_gpu(self):
        try:
            gpus = []
            try:
                for gpu in GPUtil.getGPUs():
                    gpus.append({
                        'Type': 'NVIDIA', 'Name': gpu.name,
                        'Memory': f"{gpu.memoryTotal} MB", 'Temperature': f"{gpu.temperature}°C"
                    })
            except: pass
            try:
                c = self.get_wmi_connection()
                if c:
                    for gpu in c.Win32_VideoController():
                        if gpu.Name and 'Microsoft Basic' not in gpu.Name:
                            gpus.append({
                                'Type': 'Generic', 'Name': gpu.Name,
                                'Driver': gpu.DriverVersion or 'Unknown'
                            })
            except: pass
            self.specs['gpu'] = gpus if gpus else [{'Status': 'No GPU detected'}]
        except: self.specs['gpu'] = [{'Error': 'Failed to read GPU'}]
    
    def _scan_network(self):
        try:
            interfaces = []
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family.name == 'AF_INET':
                        interfaces.append({'Interface': iface, 'IP': addr.address, 'Netmask': addr.netmask})
            self.specs['network'] = interfaces
        except: self.specs['network'] = [{'Error': 'Failed to read Network'}]
    
    def _scan_bios(self):
        try:
            c = self.get_wmi_connection()
            if c:
                for bios in c.Win32_BIOS():
                    self.specs['bios'] = {
                        'Manufacturer': bios.Manufacturer or 'Unknown',
                        'Version': bios.Version or 'Unknown'
                    }
                    break
        except: self.specs['bios'] = {'Status': 'BIOS info unavailable'}
    
    def _scan_battery(self):
        try:
            battery = psutil.sensors_battery()
            if battery:
                self.specs['battery'] = {
                    'Percentage': f"{battery.percent}%",
                    'Plugged': 'Yes' if battery.power_plugged else 'No'
                }
            else: self.specs['battery'] = {'Status': 'No battery or desktop'}
        except: self.specs['battery'] = {'Status': 'Battery info unavailable'}
'@
Set-Content -Path "src\scanner.py" -Value $scannerContent -Encoding UTF8

# 3. Buat utils.py
Write-Host "📝 Membuat utils.py..." -ForegroundColor Green
$utilsContent = @'
import json, os

def display_results(specs):
    print("\n" + "="*60)
    print("SYSTEM SPECIFICATION REPORT")
    print("="*60)
    sections = ['system', 'cpu', 'ram', 'disk', 'gpu', 'network', 'bios', 'battery']
    titles = {'system':'🖥️  SYSTEM','cpu':'⚡ CPU','ram':'💾 RAM','disk':'💿 STORAGE',
              'gpu':'🎮 GRAPHICS','network':'🌐 NETWORK','bios':'🔧 BIOS','battery':'🔋 BATTERY'}
    for section in sections:
        if section in specs:
            print(f"\n{titles.get(section, section.upper())}:")
            data = specs[section]
            if isinstance(data, dict):
                for key, value in data.items(): print(f"  {key}: {value}")
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for key, value in item.items(): print(f"  {key}: {value}")
                    else: print(f"  {item}")
            else: print(f"  {data}")

def save_report(specs, base_path):
    os.makedirs(os.path.dirname(base_path), exist_ok=True)
    try:
        txt_file = f"{base_path}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\nSYSTEM SPECIFICATION REPORT\n" + "="*60 + "\n\n")
            f.write(f"Scan Time: {specs.get('scan_time', 'N/A')}\n\n")
            for section in ['system','cpu','ram','disk','gpu','network','bios','battery']:
                if section in specs:
                    f.write(f"[{section.upper()}]\n")
                    data = specs[section]
                    if isinstance(data, dict):
                        for key, value in data.items(): f.write(f"  {key}: {value}\n")
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                for key, value in item.items(): f.write(f"  {key}: {value}\n")
                            else: f.write(f"  {item}\n")
                    f.write("\n")
        print(f"✅ Report saved: {txt_file}")
    except Exception as e: print(f"❌ Error saving TXT: {e}")
    try:
        json_file = f"{base_path}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(specs, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ JSON saved: {json_file}")
    except Exception as e: print(f"❌ Error saving JSON: {e}")
'@
Set-Content -Path "src\utils.py" -Value $utilsContent -Encoding UTF8

# 4. Buat run.bat
Write-Host "📝 Membuat run.bat..." -ForegroundColor Green
$runBatContent = @'
@echo off
chcp 65001 >nul
title SpekScanner v3.0
echo ========================================
echo         SPEKSCANNER v3.0
echo ========================================
echo.
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Install Python from python.org
    pause
    exit /b 1
)
if not exist reports mkdir reports
if not exist dist mkdir dist
echo Installing fixed dependencies...
python -m pip install --upgrade pip --quiet
python -m pip uninstall psutil -y --quiet
python -m pip install psutil==5.9.6 --quiet
python -m pip install wmi py-cpuinfo GPUtil --quiet
echo.
echo Starting system scan...
python src/main.py
pause
'@
Set-Content -Path "run.bat" -Value $runBatContent -Encoding ASCII

# 5. Buat requirements.txt
Write-Host "📝 Membuat requirements.txt..." -ForegroundColor Green
$requirementsContent = @'
psutil==5.9.6
wmi>=1.5.1
py-cpuinfo>=9.0.0
GPUtil>=1.4.0
'@
Set-Content -Path "requirements.txt" -Value $requirementsContent -Encoding UTF8

# 6. Buat README.txt
Write-Host "📝 Membuat README.txt..." -ForegroundColor Green
$readmeContent = @'
SPEKSCANNER v3.0
System Specification Scanner for Windows

HOW TO USE:
1. Run 'run.bat'
2. System will be scanned automatically
3. Reports are saved in 'reports/' folder

FEATURES:
- Accurate CPU usage (fixed psutil bug)
- RAM, Disk, GPU detection
- Network, BIOS, Battery info
- Saves TXT & JSON reports

Created with ❤️ using Python
'@
Set-Content -Path "README.txt" -Value $readmeContent -Encoding UTF8

Write-Host "✅ SETUP SELESAI!" -ForegroundColor Green
Write-Host "📂 Struktur folder:" -ForegroundColor Cyan
Get-ChildItem -Recurse | Format-Table Name, Directory

Write-Host "`n🚀 Jalankan aplikasi dengan: run.bat" -ForegroundColor Yellow
pause
