from cx_Freeze import setup, Executable
import sys
base = 'Win32GUI'
target = Executable(
    script="main.py",
    icon="icon.ico",
    base=base
)

setup(
    name="CYCU-Score-Plus",
    version="1.0",
    description="cycu-score-plus",
    author="MO7YW4NG",
    options={'build_exe': {
        'packages': ['aiohttp','fastapi','uvicorn','parsel','jinja2'],
        'include_files': ['icon.ico', 'templates'],
    },'bdist_msi': {'initial_target_dir': r'[DesktopFolder]\\CYCU-Score-Plus'},
      'bdist_mac': {
            'bundle_name': 'CYCU-Score-Plus',
            'iconfile': 'icon.ico',
        },},
    executables=[target],
)
