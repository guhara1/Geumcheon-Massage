#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""색인 통보 올인원 — 글/페이지를 올릴 때 한 번에 모든 채널에 알립니다.

수행 순서:
  1) IndexNow            — 빙·네이버·얀덱스 즉시 통보 (변경 URL)
  2) Google Indexing API — 서비스계정이 설정된 경우에만 (보조)
  3) sitemap ping        — 구글·빙 레거시 엔드포인트 시도
                           (2023년 공식 폐지 → 404가 정상이며, 대체 수단인
                            sitemap <lastmod> + IndexNow + Search Console이 본선)

사용법:
  python3 tools/notify_all.py            # 직전 커밋 대비 변경분
  python3 tools/notify_all.py --all      # 전체 URL
  python3 tools/notify_all.py --dry-run  # 전송 없이 점검만
"""
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import indexnow  # noqa: E402

BASE = indexnow.BASE
SITEMAP = BASE + "/sitemap.xml"
LEGACY_PINGS = [
    "https://www.google.com/ping?sitemap=",
    "https://www.bing.com/ping?sitemap=",
]


def ping_sitemaps(dry=False):
    print("\n[3/3] sitemap ping (레거시 — 폐지된 엔드포인트, 404 = 정상)")
    for ep in LEGACY_PINGS:
        url = ep + urllib.parse.quote(SITEMAP, safe="")
        if dry:
            print(f"  (dry-run) {url}")
            continue
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                print(f"  [{r.status}] {url}")
        except urllib.error.HTTPError as e:
            note = " (2023년 폐지 — lastmod+IndexNow가 대체)" if e.code == 404 else ""
            print(f"  [{e.code}] {url}{note}")
        except Exception as e:
            print(f"  [ERR] {url} — {e}")


def google_api(scope_args, dry=False):
    print("\n[2/3] Google Indexing API")
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("  GOOGLE_APPLICATION_CREDENTIALS 미설정 → 건너뜀 "
              "(일반 페이지는 Search Console+sitemap이 정공법)")
        return
    if dry:
        print("  (dry-run) google_indexing.py", *scope_args)
        return
    import google_indexing
    google_indexing.main(list(scope_args))


def main(argv):
    dry = "--dry-run" in argv
    scope = ["--all"] if "--all" in argv else ["--changed"]
    print("[1/3] IndexNow (빙·네이버·얀덱스)")
    rc = indexnow.main(scope + (["--dry-run"] if dry else []))
    google_api(scope, dry)
    ping_sitemaps(dry)
    print("\n완료. 구글 색인의 본선은 Search Console 등록 + sitemap 제출이며, "
          "sitemap <lastmod>는 빌드 시 자동 갱신됩니다.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
