# -*- coding: utf-8 -*-
"""배포 전 점검 — 도어웨이 유사도 / 제목 고유성 / JSON-LD 유효성 / 본문 분량.

Run: python3 tools/check.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main_text(f):
    """헤더/푸터 제외한 본문 텍스트만 추출."""
    h = open(f, encoding="utf-8").read()
    body = h.split("</header>", 1)[1].split("<footer", 1)[0]
    body = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()


def shingles(t, n=4):
    k = t.split()
    return {tuple(k[i:i + n]) for i in range(len(k) - n + 1)}


def sim(a, b):
    A, B = shingles(a), shingles(b)
    return len(A & B) / len(A | B) if A | B else 0.0


def group_sim(name, paths):
    texts = {p: main_text(os.path.join(ROOT, p.strip("/"), "index.html")) for p in paths}
    pairs = []
    keys = list(texts)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            pairs.append((sim(texts[keys[i]], texts[keys[j]]), keys[i], keys[j]))
    if not pairs:
        return True
    mx = max(pairs)
    avg = sum(p[0] for p in pairs) / len(pairs)
    ok = mx[0] <= 0.45
    print(f"[{'OK' if ok else 'WARN'}] {name}: 평균 {avg:.0%}, 최대 {mx[0]:.0%} ({mx[1]} ↔ {mx[2]})")
    return ok


def run():
    fails = 0

    # 1) 그룹별 유사도 (목표 ≤ ~40-45%)
    from core import DONGS, STATIONS, THEMES  # noqa
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    dongs = [f"/geumcheon-gu/{d['slug']}/" for d in DONGS]
    stations = [f"/geumcheon-gu/stations/{s['slug']}/" for s in STATIONS]
    themes = [f"/themes/{t['slug']}/" for t in THEMES]
    for name, grp in [("동 페이지", dongs), ("역 페이지", stations), ("테마 페이지", themes)]:
        if not group_sim(name, grp):
            fails += 1

    # 2) 제목/설명 고유성 + JSON-LD 파싱
    titles, descs = {}, {}
    files = glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True) + \
            [os.path.join(ROOT, "index.html")]
    files = sorted(set(f for f in files if "/tools/" not in f))
    for f in files:
        h = open(f, encoding="utf-8").read()
        t = re.search(r"<title>(.*?)</title>", h, re.S).group(1)
        d = re.search(r'name="description" content="(.*?)"', h).group(1)
        titles.setdefault(t, []).append(f)
        descs.setdefault(d, []).append(f)
        for m in re.findall(r'application/ld\+json">(.*?)</script>', h, re.S):
            try:
                json.loads(m)
            except json.JSONDecodeError as e:
                print(f"[FAIL] JSON-LD 오류: {f}: {e}")
                fails += 1
    for t, fs in titles.items():
        if len(fs) > 1:
            print(f"[FAIL] 중복 title: {t} → {fs}")
            fails += 1
    for d, fs in descs.items():
        if len(fs) > 1:
            print(f"[FAIL] 중복 description: {d[:40]}… → {fs}")
            fails += 1
    print(f"[OK] 페이지 {len(files)}개 — title/description 고유성, JSON-LD 파싱 점검 완료"
          if fails == 0 else f"… 위 항목 확인 필요")

    # 3) 인덱스(허브) 페이지 본문 분량 (목표 2,000~2,500자, 공백 포함)
    index_pages = ["/", "/geumcheon-gu/", "/geumcheon-gu/area/",
                   "/geumcheon-gu/stations/", "/themes/", "/course/"]
    for p in index_pages:
        f = os.path.join(ROOT, "index.html") if p == "/" else \
            os.path.join(ROOT, p.strip("/"), "index.html")
        n = len(main_text(f))
        flag = "OK" if n >= 2000 else "WARN"
        print(f"[{flag}] 본문 분량 {p}: {n:,}자 (공백 포함)")
        if n < 2000:
            fails += 1

    # 4) 내부 링크 무결성 (생성된 경로 대비)
    valid = set()
    for f in files:
        rel = os.path.relpath(f, ROOT).replace(os.sep, "/")
        valid.add("/" if rel == "index.html" else "/" + rel[:-len("index.html")])
    broken = 0
    for f in files:
        h = open(f, encoding="utf-8").read()
        for href in re.findall(r'href="(/[^"#]*?/)"', h):
            if href not in valid:
                print(f"[FAIL] 깨진 링크 {href} in {f}")
                broken += 1
    if broken == 0:
        print(f"[OK] 내부 링크 무결성 — 깨진 링크 0")
    fails += broken

    print("\n결과:", "PASS" if fails == 0 else f"FAIL ({fails}건)")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    raise SystemExit(run())
