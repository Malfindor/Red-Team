import os
import sys
import subprocess
self = sys.argv[0]
dirIgnoreList = ['/bin', '/boot', '/dev', '/etc', '/lib', '/proc', '/run', '/sbin', '/sys', '/tmp', '/usr', '/var']
excludedFiles = [self, "/bin/cat", "/bin/echo"]
origin = "/"
def main():
    fileList = findFiles(origin)
    for file in fileList:
        print(file)
    
def findFiles(origin):
    ignore_dirs = set(_norm_path(p) for p in dirIgnoreList)
    exclude_files = set(_norm_path(p) for p in excludedFiles)

    start_real = _norm_path(origin)
    results = []
    for root, dirs, files in os.walk(start_real, topdown=True, followlinks=False):
        root_real = _norm_path(root)

        pruned = []
        for d in dirs:
            full = _norm_path(os.path.join(root_real, d))
            if full in ignore_dirs:
                continue
            pruned.append(d)
        dirs[:] = pruned

        for fname in files:
            fpath_real = _norm_path(os.path.join(root_real, fname))
            if fpath_real in exclude_files:
                continue
            results.append(fpath_real)

    return results
def _norm_path(p):
        try:
            return os.path.realpath(os.path.abspath(p))
        except Exception:
            return os.path.abspath(p)
if(os.getuid() == 0):
    main()