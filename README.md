# 금천 VIP 마사지 — 금천 출장마사지·홈타이 사이트

순수 정적 HTML(인라인 CSS/JS, 런타임 의존성 0) + Python 단일 생성기로 만든
지역 SEO 사이트입니다. 굿데이 강서 프로젝트의 재사용 블루프린트(BLUEPRINT.md)를 기반으로 제작했습니다.

- 상호: **금천 VIP 마사지** · 예약전화: **0508-202-4719**
- 배포 도메인(예정): `https://geumcheon-massage.pages.dev` (Cloudflare Pages)
- 총 56페이지

## 사이트 구조 (도어웨이 회피 원칙)

| 구분 | 페이지 | 비고 |
|---|---|---|
| 홈 | `/` | 허브(메인) — H1 "금천 출장마사지·홈타이 예약 안내", 본문 2,000자+ |
| 금천 대표 | `/geumcheon-gu/` + 홈타이/전지역/시간/확인/안전/FAQ | 공통 정보 전용 페이지(링크아웃 대상) |
| 지역 | `/geumcheon-gu/{gasan,doksan,siheung}-dong/` | **대표 동 3개만.** 독산1~4동→독산동, 시흥1~5동→시흥동 통합 |
| 역세권 | `/geumcheon-gu/stations/…` 3개 | 가산디지털단지역(1·7호선 환승, URL 1개)·독산역·금천구청역. 출구별 페이지 없음 |
| 테마 | `/themes/` + 14개 | 독립 페이지. **지역·역·테마 조합 페이지 생성 금지** |
| 코스 | `/course/` + 8개 | 피로회복·아로마·스포츠·홈타이·커플·단체·가격·가이드 |
| 매거진 | `/magazine/` + 글 8편 | 글당 2,000~2,500자. 지역·역·테마·코스·블로그 상호 내부링크(롱테일 앵커), BlogPosting 스키마 |
| 기타 | 예약안내·이용가이드·후기·고객센터·정책 3종 | |

## 빌드 / 점검

```bash
python3 tools/build.py    # 전체 사이트 생성 (HTML + sitemap + robots + manifest)
python3 tools/gen_icons.py  # 파비콘·PWA·OG 이미지 (Pillow 필요)
python3 tools/check.py    # 도어웨이 유사도·title 고유성·JSON-LD·본문 분량·링크 점검
```

`tools/` 구성: `core.py`(프레임워크·데이터 모델) / `build.py`(페이지 빌더) /
`data_themes.py`·`data_courses.py`·`data_magazine.py`(테마·코스·매거진 콘텐츠) / `check.py`(QA) /
`indexnow.py`·`google_indexing.py`(색인 통보) / `gen_icons.py`(브랜드 이미지)

## 배포 전 점검 결과 (tools/check.py — 전 항목 PASS)

- 도어웨이 유사도: 동 31% / 역 28% / 테마 11% / 매거진 10% (목표 ≤ ~40%)
- **전 페이지(57) 본문 2,000~2,500자** (공백 포함, 정책 3종은 법적 고지문서로 예외 — 억지 패딩 금지)
- title·description 100% 고유 + 쌍별 유사도 검사(title ≤75%, desc ≤70%) 통과
- JSON-LD 파싱 0오류, 내부 링크 깨짐 0

## E-E-A-T / 구글 가이드라인 대응

- **저자 소개 페이지** `/about/` — Who(운영 주체)·How(예약 데이터 기반 제작·검수 방식)·Why(운영 철학) 공개, 전 페이지 바이라인에서 링크
- 바이라인(작성·감수·업데이트 일자) 전 페이지, Article/BlogPosting `author.url` → `/about/`
- **선호 이미지 지정**: og:image + Organization `logo`/`image`, publisher `logo` (ImageObject)
- 현장 운영 메모(1차 데이터: 도착 시간·시간대별 이용 패턴) 전 콘텐츠 페이지 배치
- 비의료 고지·만 19세 기준·정찰 요금 원칙 명시, 정책 3종 실질 조항으로 확충

## 배포 후 TODO

- [ ] `tools/core.py`의 `COMPANY` 실제 사업자 정보로 교체 (대표자명·사업자번호·통신판매신고)
- [ ] 실제 도메인 확정 시 `core.py`/`indexnow.py`/`google_indexing.py`의 `BASE_URL`·`HOST` 교체 후 재빌드
- [ ] Cloudflare Pages 연결, Search Console·네이버 서치어드바이저·Bing 등록 + sitemap 제출
- [ ] IndexNow 키 파일(`<KEY>.txt`)이 도메인 루트에서 열리는지 확인
