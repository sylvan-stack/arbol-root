# Mid-tier source from scripts/check_build.py; see MID_TIER.md.
# Shared helpers and refusal entry points remain at the original path.

# TEST-TIER-DISABLED-BEGIN scripts/check_build.py::main
# def main() -> int:
#     try:
#         verify(ROOT)
#         python = ROOT / 'runtime/python/bin/python3.14'
#         for start, top in [('tests', 'tests'), ('contract/conformance/tests', 'contract/conformance')]:
#             result = subprocess.run([str(python), '-I', '-B', '-m', 'unittest', 'discover', '-s', start, '-t', top, '-v'],
#                                     cwd=ROOT, check=False)
#             if result.returncode:
#                 return 1
#         verify(ROOT)
#     except (OSError, ValueError, KeyError) as error:
#         print(f'Root Build unit check failed: {error}', file=sys.stderr)
#         return 1
#     return 0
# TEST-TIER-DISABLED-END scripts/check_build.py::main

# TEST-TIER-IMPORTS-BEGIN scripts/check_build.py:5
# import subprocess
# TEST-TIER-IMPORTS-END scripts/check_build.py:5

# TEST-TIER-IMPORTS-BEGIN scripts/check_build.py:11
# from scripts.package_support import verify  # noqa: E402
# TEST-TIER-IMPORTS-END scripts/check_build.py:11

raise RuntimeError("Mid-tier checks require an explicitly requested testing task; see MID_TIER.md.")
