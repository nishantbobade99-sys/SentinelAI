"""
Startup Health Check & Dependency Validator.

Run this before starting the application:
    python health_check.py

Or import and call startup_check() from app.py.
"""
import os
import sys
import json
import importlib
from pathlib import Path

# ── File paths to verify ───────────────────────────────────────────────────────
REQUIRED_WEIGHTS = {
    'Image Model (EfficientNet-B0)':  'weights/image_deepfake_efficientnet_best.pth',
    'Video Model':                    'weights/video_deepfake_model.pth',
    'Website Model':                  'weights/website_phishing_model.pkl',
    'Website Scaler':                 'weights/website_feature_scaler.pkl',
    'Image Threshold':                'weights/image_threshold.json',
}

REQUIRED_DIRS = {
    'Uploads':                        'uploads',
    'Logs':                           'logs',
    'Weights':                        'weights',
    'Data Corpus':                    'data/corpus',
    'Deepfake Images (train/real)':   'data/deepfake_images/train/real',
    'Deepfake Images (train/fake)':   'data/deepfake_images/train/fake',
    'Deepfake Images (val/real)':     'data/deepfake_images/val/real',
    'Deepfake Images (val/fake)':     'data/deepfake_images/val/fake',
}

REQUIRED_PACKAGES = [
    'torch', 'torchvision', 'timm', 'cv2', 'PIL', 'numpy',
    'flask', 'sklearn', 'sentence_transformers', 'tldextract',
    'validators', 'dns', 'yaml', 'joblib', 'tqdm',
]


def check_package(pkg_name: str) -> bool:
    """Returns True if package is importable."""
    try:
        importlib.import_module(pkg_name)
        return True
    except ImportError:
        return False


def count_images_in_dir(path: str) -> int:
    """Count image files in directory."""
    if not os.path.exists(path):
        return 0
    exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    return sum(1 for f in Path(path).iterdir() if f.suffix.lower() in exts)


def startup_check(verbose: bool = True) -> dict:
    """
    Run all health checks and return a structured report.
    Never raises — always returns a result dict.
    """
    report = {
        'overall_status': 'OK',
        'weights': {},
        'directories': {},
        'datasets': {},
        'packages': {},
        'warnings': [],
        'errors': [],
        'can_run_inference': False,
    }

    # ── 1. Check weight files ──────────────────────────────────────────────────
    for label, path in REQUIRED_WEIGHTS.items():
        exists = os.path.exists(path)
        size_kb = round(os.path.getsize(path) / 1024, 1) if exists else 0
        report['weights'][label] = {
            'path': path,
            'status': 'OK' if exists else 'MISSING',
            'size_kb': size_kb,
        }
        if not exists:
            report['errors'].append(f"Missing weight: {path}")
            report['overall_status'] = 'DEGRADED'

    # ── 2. Check directories ───────────────────────────────────────────────────
    for label, path in REQUIRED_DIRS.items():
        exists = os.path.exists(path)
        report['directories'][label] = {
            'path': path,
            'status': 'OK' if exists else 'MISSING',
        }
        if not exists:
            report['warnings'].append(f"Missing directory: {path}")

    # ── 3. Check dataset contents ─────────────────────────────────────────────
    dataset_dirs = {
        'train/real': 'data/deepfake_images/train/real',
        'train/fake': 'data/deepfake_images/train/fake',
        'val/real':   'data/deepfake_images/val/real',
        'val/fake':   'data/deepfake_images/val/fake',
        'test/real':  'data/deepfake_images/test/real',
        'test/fake':  'data/deepfake_images/test/fake',
        'corpus':     'data/corpus',
    }
    total_dataset_images = 0
    for label, path in dataset_dirs.items():
        if label == 'corpus':
            count = sum(1 for f in Path(path).rglob('*') if f.is_file()) if os.path.exists(path) else 0
            report['datasets'][label] = {'path': path, 'file_count': count,
                                          'status': 'OK' if count > 0 else 'EMPTY'}
        else:
            count = count_images_in_dir(path)
            total_dataset_images += count
            report['datasets'][label] = {'path': path, 'image_count': count,
                                          'status': 'OK' if count > 0 else 'EMPTY'}

    if total_dataset_images == 0:
        report['warnings'].append(
            "No training images found. Training will fail. "
            "Add images to data/deepfake_images/train/real and train/fake, "
            "or download a dataset (e.g. FaceForensics++, DFDC)."
        )

    # ── 4. Check Python packages ───────────────────────────────────────────────
    missing_packages = []
    for pkg in REQUIRED_PACKAGES:
        ok = check_package(pkg)
        report['packages'][pkg] = 'OK' if ok else 'NOT INSTALLED'
        if not ok:
            missing_packages.append(pkg)

    if missing_packages:
        report['errors'].append(
            f"Missing packages: {', '.join(missing_packages)}. "
            f"Run: pip install -r requirements.txt"
        )
        report['overall_status'] = 'DEGRADED'

    # ── 5. Check if inference is possible ─────────────────────────────────────
    image_model_ok = os.path.exists('weights/image_deepfake_efficientnet_best.pth')
    core_packages_ok = all(check_package(p) for p in ['torch', 'timm', 'PIL', 'cv2', 'numpy'])
    report['can_run_inference'] = image_model_ok and core_packages_ok

    if not report['can_run_inference']:
        report['overall_status'] = 'ERROR'
        if not image_model_ok:
            report['errors'].append(
                "CRITICAL: Image model weights missing. "
                "Run: python scripts/setup_and_repair.py"
            )

    return report


def print_report(report: dict):
    """Pretty-print the health check report to console."""
    GREEN  = '\033[92m'
    RED    = '\033[91m'
    YELLOW = '\033[93m'
    BOLD   = '\033[1m'
    RESET  = '\033[0m'

    status_color = {'OK': GREEN, 'DEGRADED': YELLOW, 'ERROR': RED}
    c = status_color.get(report['overall_status'], YELLOW)

    print(f"\n{'='*60}")
    print(f"  FakeGuard AI -- Startup Health Check")
    print(f"  Overall Status: {BOLD}{c}{report['overall_status']}{RESET}")
    print(f"{'='*60}")

    print(f"\n  Model Weights")
    print(f"  {'-'*55}")
    for label, info in report['weights'].items():
        ok = info['status'] == 'OK'
        sym = f"{GREEN}[OK]{RESET}" if ok else f"{RED}[MISSING]{RESET}"
        size = f"  ({info['size_kb']} KB)" if ok else ""
        print(f"  {sym}  {label:<40} {size}")

    print(f"\n  Datasets")
    print(f"  {'-'*55}")
    for label, info in report['datasets'].items():
        count = info.get('image_count', info.get('file_count', 0))
        ok = info['status'] == 'OK'
        sym = f"{GREEN}[OK]{RESET}" if ok else f"{YELLOW}[EMPTY]{RESET}"
        print(f"  {sym}  {label:<40} {count} files")

    print(f"\n  Python Packages")
    print(f"  {'-'*55}")
    for pkg, status in report['packages'].items():
        ok = status == 'OK'
        sym = f"{GREEN}[OK]{RESET}" if ok else f"{RED}[MISSING]{RESET}"
        print(f"  {sym}  {pkg}")

    if report['warnings']:
        print(f"\n  {YELLOW}Warnings:{RESET}")
        for w in report['warnings']:
            print(f"     - {w}")

    if report['errors']:
        print(f"\n  {RED}Errors:{RESET}")
        for e in report['errors']:
            print(f"     - {e}")

    inf_ok = report['can_run_inference']
    sym = f"{GREEN}[READY]{RESET}" if inf_ok else f"{RED}[NOT READY]{RESET}"
    print(f"\n  Inference:  {sym}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    report = startup_check()
    print_report(report)

    # Also save JSON report
    with open('health_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    print("Full report saved to health_report.json")

    if not report['can_run_inference']:
        print("\n💡 Quick fix: python scripts/setup_and_repair.py")
        sys.exit(1)
