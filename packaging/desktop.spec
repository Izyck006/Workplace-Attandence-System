from pathlib import Path
import os

root = Path(SPECPATH).parent
sdk = Path(os.getenv('IBSCAN_SDK_DIR', r'C:\Program Files\Integrated Biometrics\IBScanUltimateSDK_x64\Bin'))
if not (sdk / 'IBScanUltimate.dll').exists():
    raise RuntimeError('Install the x64 IBScan SDK or set IBSCAN_SDK_DIR before building.')
# The capture runtime does not require the SDK's Java bindings, demo logger or old matcher.
binaries = [(str(sdk / name), 'scanner_runtime') for name in
            ('IBScanUltimate.dll', 'ACamSDK.dll', 'IBScanNFIQ2.dll')]
a = Analysis([str(root / 'main.py')], pathex=[str(root)], binaries=binaries,
    datas=[(str(root / 'icon.ico'), '.'), (str(root / 'randaframes logo.jpg'), '.'), (str(root / 'assets'), 'assets')],
    hiddenimports=[], excludes=['fastapi', 'uvicorn', 'mongomock', 'pytest', 'src.server', 'src.data.database'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='RandaframesAttendance',
    console=False, icon=str(root / 'icon.ico'), version=str(root / 'packaging' / 'version_info.txt'), upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name='RandaframesAttendance', upx=False)
