#!/usr/bin/env python3
"""test_vouchers.py [owner's codes csv] -- MT2009_PLUS_VOUCHER_CODES_V1.

Checks the promo codes ("/kod", overlay playerbot_voucher.h) without a server:
  1. the salt of playerbot_voucher_rules.h is the one apply.sh documents;
  2. the C++ Normalize() (compiled from playerbot_voucher_rules.h with g++)
     gives what this script's normalize() gives, on a set of typed variants;
  3. apply.sh's REPLACE rows and its DELETE keep-list are the same set, every
     hash is 64 hex characters;
  4. with the owner's list (default /opt/metin2/cache/voucher/kody.csv, kept
     outside the repository; first column the code): every hash in apply.sh is
     SHA-256(salt + normalized code) of a code of that list - printed with its
     reward - and no code of the list appears in plain text in a tracked file.
Exit 0 when all pass."""
import hashlib
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RULES = os.path.join(REPO, "linux-port/overlays/playerbot/src/game/src/playerbot_voucher_rules.h")
APPLY = os.path.join(REPO, "linux-port/docker/mariadb/playerbot/apply.sh")
DEFAULT_CODES = "/opt/metin2/cache/voucher/kody.csv"

failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def normalize(typed):
    out = ""
    for c in typed:
        if c in " \t-_\r\n":
            continue
        if "a" <= c <= "z":
            out += c.upper()
        elif "A" <= c <= "Z" or "0" <= c <= "9":
            out += c
        else:
            return ""
        if len(out) > 32:
            return ""
    return out


def main():
    rules = open(RULES, encoding="ascii").read()
    apply_sh = open(APPLY, encoding="utf-8").read()
    salt = re.search(r'VOUCHER_SALT = "([^"]*)"', rules).group(1)
    check("SHA2(CONCAT('%s'," % salt in apply_sh, "apply.sh documents the salt of playerbot_voucher_rules.h (%s)" % salt)

    # 2. C++ vs Python normalization.
    samples = ["MT2009-PLUS-AB12", "mt2009 plus ab12", " Mt2009_Plus-aB12 ", "MT2009PLUSAB12",
               "MT2009-PLUS-AB1!", "", "   ", "MT2009-PLUS-ĄB12", "A" * 32, "A" * 33, "x-y-z"]
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "n.cpp")
        exe = os.path.join(tmp, "n")
        open(src, "w").write('#include "playerbot_voucher_rules.h"\n#include <iostream>\n#include <string>\n'
                             'int main(){std::string l;while(std::getline(std::cin,l)){std::string o;'
                             'bool ok=mt2009_voucher_rules::Normalize(l.c_str(),o);std::cout<<(ok?o:std::string("-"))<<"\\n";}}\n')
        try:
            subprocess.check_call(["g++", "-std=c++17", "-I", os.path.dirname(RULES), src, "-o", exe])
            res = subprocess.run([exe], input="\n".join(samples) + "\n", capture_output=True, text=True).stdout.split("\n")
            for s, r in zip(samples, res):
                want = normalize(s) or "-"
                check(r == want, "Normalize(%r) C++ %r == Python %r" % (s, r, want))
        except (OSError, subprocess.CalledProcessError) as e:
            check(False, "compile the C++ Normalize (%s)" % e)

    # 3. apply.sh rows.
    rows = re.findall(r"\('([0-9a-f]{64})', (\d+), (\d+), (\d+)\)", apply_sh)
    keep = set(re.findall(r"\('([0-9a-f]{64})', (\d+)\)", apply_sh))
    check(len(rows) > 0, "apply.sh has %d reward rows" % len(rows))
    check({(h, n) for h, n, _, _ in rows} == keep, "the REPLACE rows and the DELETE keep-list are the same set")
    rewards = {}
    for h, n, v, c in rows:
        rewards.setdefault(h, []).append((int(n), int(v), int(c)))

    # 4. The owner's list.
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CODES
    if not os.path.exists(path):
        print("skip the owner's list (%s not here)" % path)
    else:
        codes = [ln.split(";")[0].strip() for ln in open(path, encoding="utf-8") if ln.strip()]
        codes = [c for c in codes if c and c.lower() != "kod"]
        by_hash = {hashlib.sha256((salt + normalize(c)).encode()).hexdigest(): c for c in codes}
        for h in sorted(rewards, key=lambda h: by_hash.get(h, "~")):
            code = by_hash.get(h)
            check(code is not None, "%s... is a code of the owner's list%s" % (h[:12], (": %s -> %s" % (
                code, ", ".join("%d x%d" % (v, c) for _, v, c in sorted(rewards[h])))) if code else ""))
            if code:
                check(normalize(code.lower().replace("-", " ")) == normalize(code), "%s typed lower-case with spaces is the same code" % code)
        print("%d of %d codes of the list are active" % (len(rewards), len(codes)))
        tracked = subprocess.run(["git", "-C", REPO, "grep", "-I", "-l", "-i", "-F"] + sum([["-e", c] for c in codes] +
                                 [["-e", normalize(c)] for c in codes], []), capture_output=True, text=True).stdout.strip()
        check(tracked == "", "no code of the list in plain text in a tracked file%s" % (": " + tracked if tracked else ""))

    print("\n%s" % ("ALL OK" if not failures else "%d FAILED" % len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
