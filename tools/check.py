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
    from core import DONGS, STATIONS, THEMES, POSTS  # noqa
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    dongs = [f"/geumcheon-gu/{d['slug']}/" for d in DONGS]
    stations = [f"/geumcheon-gu/stations/{s['slug']}/" for s in STATIONS]
    themes = [f"/themes/{t['slug']}/" for t in THEMES]
    posts = [f"/magazine/{p['slug']}/" for p in POSTS]
    for name, grp in [("동 페이지", dongs), ("역 페이지", stations),
                      ("테마 페이지", themes), ("매거진 글", posts)]:
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

    # 3) 전 페이지 본문 분량 감사 (목표 2,000~2,500자, 공백 포함 / 홈은 카드·히어로 포함 상한 완화)
    # 법적 고지 문서(정책 3종)는 분량 예외 — 억지 패딩 금지 원칙(필요 조항만 명시)
    POLICY_EXEMPT = {"/privacy/", "/terms/", "/youth/"}
    short_pages, long_pages, total = [], [], 0
    for f in files:
        rel = os.path.relpath(f, ROOT).replace(os.sep, "/")
        p = "/" if rel == "index.html" else "/" + rel[: -len("index.html")]
        n = len(main_text(f))
        total += 1
        if p in POLICY_EXEMPT:
            if n < 500:
                short_pages.append((n, p))
            continue
        hi = 3000 if p == "/" else 2600
        if n < 2000:
            short_pages.append((n, p))
        elif n > hi:
            long_pages.append((n, p))
    for n, p in sorted(short_pages):
        print(f"[FAIL] 분량 미달 {p}: {n:,}자 (<2,000)")
    for n, p in sorted(long_pages):
        print(f"[FAIL] 분량 초과 {p}: {n:,}자")
    fails += len(short_pages) + len(long_pages)
    if not short_pages and not long_pages:
        print(f"[OK] 전 페이지({total}) 본문 분량 2,000자 이상 (공백 포함)")

    # 3b) title/description 유사도 감사 (그룹 내 과도한 템플릿 복제 탐지)
    def tri(t):
        t = re.sub(r"\s+", "", t)
        return {t[i:i + 3] for i in range(len(t) - 2)}

    def txt_sim(a, b):
        A, B = tri(a), tri(b)
        return len(A & B) / len(A | B) if A | B else 0.0

    metas = []
    for f in files:
        h = open(f, encoding="utf-8").read()
        t = re.search(r"<title>(.*?)</title>", h, re.S).group(1)
        d = re.search(r'name="description" content="(.*?)"', h).group(1)
        metas.append((f, t, d))
    warn = 0
    for i in range(len(metas)):
        for j in range(i + 1, len(metas)):
            st = txt_sim(metas[i][1], metas[j][1])
            sd = txt_sim(metas[i][2], metas[j][2])
            if st > 0.75 or sd > 0.7:
                print(f"[FAIL] 메타 유사 {st:.0%}/{sd:.0%}: "
                      f"{os.path.relpath(metas[i][0], ROOT)} ↔ {os.path.relpath(metas[j][0], ROOT)}")
                warn += 1
    fails += warn
    if warn == 0:
        print("[OK] title/description 쌍별 유사도 — 과도한 템플릿 복제 없음 (title ≤75%, desc ≤70%)")

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
