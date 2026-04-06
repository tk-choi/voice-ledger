"""py2app 패키징 설정"""
from setuptools import setup

APP = ["src/main.py"]
DATA_FILES = [
    ("bin", ["vendor/ffmpeg"]),
]
OPTIONS = {
    "argv_emulation": False,
    "packages": ["PyQt6", "whisper", "torch"],
    "includes": [
        "src.engine",
        "src.ui",
    ],
    "plist": {
        "CFBundleName": "Voice Ledger",
        "CFBundleDisplayName": "Voice Ledger",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleIdentifier": "com.voiceledger.app",
        "NSMicrophoneUsageDescription": "오디오 파일 변환에 사용합니다.",
        "NSHighResolutionCapable": True,
    },
    "excludes": ["tkinter", "unittest", "email", "html", "http", "xml"],
}

setup(
    name="VoiceLedger",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
