# -*- coding: utf-8 -*-
"""금천 VIP 마사지 — static site generator core.

공유 프레임워크: 브랜드 상수, 데이터 모델(동·역·테마·코스), 디자인 시스템(CSS/JS),
페이지 셸, 내비게이션/푸터, 재사용 블록(FAQ·럭스 레이아웃·가격 메뉴), JSON-LD 빌더.

빌더(페이지 생성)는 tools/build.py 참고.  실행: python3 tools/build.py
"""

import os
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_themes import THEMES            # noqa: E402
from data_courses import COURSE_DETAIL    # noqa: E402
from data_magazine import POSTS           # noqa: E402

# ---------------------------------------------------------------------------
# Brand / business constants  (replace placeholders before going live)
# ---------------------------------------------------------------------------
BASE_URL    = "https://geumcheon-massage.pages.dev"  # 메인 도메인 (Cloudflare Pages)
BRAND       = "금천 VIP 마사지"
BRAND_SHORT = "금천 VIP"
PHONE_DISP  = "0508-202-4719"                        # 예약 전화번호
PHONE_TEL   = "+825082024719"                        # tel: 링크용
HOURS       = "연중무휴 · 24시간 상담"
INDEXNOW_KEY = "e2c006901be1468480084a855ad814af"    # IndexNow(빙·네이버 등) 인증 키
UPDATED     = "2026-06-10"

COMPANY = {
    "name": "금천 VIP 마사지",
    "ceo": "운영 대표",                  # TODO: 실제 대표자명
    "biz_no": "000-00-00000",            # TODO: 사업자등록번호
    "addr": "서울특별시 금천구",
    "sales_no": "2026-서울금천-0000",    # TODO: 통신판매업신고번호
    "privacy_officer": "운영 대표",      # TODO
}

# ---------------------------------------------------------------------------
# Data model — 대표 동 3개 (숫자 행정동은 대표 동으로 통합, 별도 페이지 금지)
# ---------------------------------------------------------------------------
DONGS = [
    {"slug": "gasan-dong", "name": "가산동", "arrival": 25,
     "landmarks": "가산디지털단지역(1·7호선), G밸리 지식산업센터, 아울렛 패션타운 일대",
     "character": "지식산업센터와 오피스텔이 밀집한 금천 대표 업무 권역",
     "station_slugs": ["gasan-digital-complex-station"]},
    {"slug": "doksan-dong", "name": "독산동", "arrival": 27,
     "landmarks": "독산역(1호선), 대단지 아파트, 독산동 전통 생활권 일대",
     "character": "대단지 아파트와 전통 생활권이 공존하는 주거 권역",
     "sub_note": "독산1동·독산2동·독산3동·독산4동은 별도 페이지를 만들지 않고 "
                 "독산동 페이지에서 통합 안내드립니다.",
     "station_slugs": ["doksan-station"]},
    {"slug": "siheung-dong", "name": "시흥동", "arrival": 30,
     "landmarks": "금천구청역(1호선), 시흥사거리, 호암산 자락 주거지 일대",
     "character": "금천구 남부를 아우르는 대표 주거 생활권",
     "sub_note": "시흥1동·시흥2동·시흥3동·시흥4동·시흥5동은 별도 페이지를 만들지 않고 "
                 "시흥동 페이지에서 통합 안내드립니다.",
     "station_slugs": ["geumcheon-gu-office-station"]},
]

# 동별 방문 가능 생활권 — 역명·생활권은 본문 H3로만 흡수(별도 페이지 금지)
DONG_ZONES = {
    "gasan-dong": [
        ("가산디지털단지역 인근", "1·7호선 환승역을 중심으로 오피스텔과 숙소가 모인 생활권입니다."),
        ("G밸리 지식산업단지 일대", "지식산업센터가 밀집한 업무 권역으로 야근 후 방문 문의가 많습니다."),
        ("아울렛 패션타운 인근", "대형 아울렛 상권 주변의 상업·숙소 생활권입니다."),
        ("가산동 주거 생활권", "업무 지구 배후의 오피스텔·빌라 주거지입니다.")],
    "doksan-dong": [
        ("독산역 인근", "1호선 독산역을 중심으로 한 주거·상업 생활권입니다."),
        ("대단지 아파트 일대", "역세권 대단지 아파트가 모인 정주형 생활권입니다."),
        ("독산동 전통 생활권", "시장과 골목 상권이 살아 있는 오래된 주거 밀집지입니다."),
        ("금천구청 방면", "구청 방향으로 이어지는 행정·주거 혼합 생활권입니다.")],
    "siheung-dong": [
        ("금천구청역 인근", "1호선 금천구청역을 중심으로 한 행정·주거 생활권입니다."),
        ("시흥사거리 일대", "버스 교통의 중심으로 상권과 주거가 모인 생활권입니다."),
        ("호암산 자락 주거지", "산자락을 따라 조용한 주거 단지가 이어지는 권역입니다."),
        ("시흥동 남부 생활권", "금천구 남쪽 끝까지 이어지는 주거 밀집 생활권입니다.")],
}

# ---------------------------------------------------------------------------
# Data model — 지하철역 3개 (환승역도 URL은 1개, 출구별·역+테마 페이지 금지)
# ---------------------------------------------------------------------------
STATIONS = [
    {"slug": "gasan-digital-complex-station", "name": "가산디지털단지역",
     "lines": "1호선·7호선 환승", "line_keys": ["line1", "line7"],
     "dong_slug": "gasan-dong", "arrival": 24,
     "character": "금천구 가산동에 있는 1·7호선 환승역으로, 지식산업센터와 오피스텔·숙소가 밀집한 금천 최대 업무 역세권"},
    {"slug": "doksan-station", "name": "독산역",
     "lines": "1호선", "line_keys": ["line1"],
     "dong_slug": "doksan-dong", "arrival": 26,
     "character": "금천구 독산동의 1호선 역으로, 역세권 대단지 아파트와 전통 생활권이 함께 있는 주거 역세권"},
    {"slug": "geumcheon-gu-office-station", "name": "금천구청역",
     "lines": "1호선", "line_keys": ["line1"],
     "dong_slug": "siheung-dong", "arrival": 29,
     "character": "금천구 시흥동의 1호선 역으로, 금천구청과 행정 시설, 주거 생활권이 모인 금천 남부 역세권"},
]

STATION_ZONES = {
    "gasan-digital-complex-station": [
        ("지식산업센터·오피스 권역", "역 주변으로 지식산업센터가 밀집해 야근 후 오피스텔 방문 문의가 많습니다."),
        ("아울렛 패션타운 방면", "대형 아울렛 상권과 숙소가 모여 있어 주말 방문 문의가 이어집니다."),
        ("역 인근 오피스텔·숙소", "환승역 특성상 오피스텔·비즈니스 숙소가 많아 늦은 시간 문의가 잦습니다."),
        ("가산동 주거 생활권", "업무 지구 배후 주거지로, 퇴근 후 자택 방문 예약이 많습니다.")],
    "doksan-station": [
        ("역세권 대단지 아파트", "독산역 인근 대단지 위주의 정주형 생활권으로 가족 단위 문의가 많습니다."),
        ("독산동 전통 생활권", "시장과 골목 상권이 이어진 오래된 주거지로 저녁 시간대 예약이 많습니다."),
        ("역 인근 오피스텔", "역 가까이의 오피스텔·원룸 생활권입니다."),
        ("금천구청 방면", "한 정거장 거리의 금천구청역 방면 생활권과 이어집니다.")],
    "geumcheon-gu-office-station": [
        ("금천구청·관공서 일대", "구청·경찰서 등 행정 시설이 모인 권역으로 평일 저녁 문의가 많습니다."),
        ("시흥사거리 방면", "버스 환승 거점인 시흥사거리 방향의 상권·주거 생활권입니다."),
        ("호암산 자락 주거지", "산자락의 조용한 주거 단지로 주말 자택 방문 문의가 이어집니다."),
        ("역 인근 주거 생활권", "역 주변 아파트·빌라 밀집지로 도착이 빠른 권역입니다.")],
}

# ---------------------------------------------------------------------------
# Data model — 코스(허브 카드) / 기본 요금
# ---------------------------------------------------------------------------
COURSES = [
    {"slug": "fatigue", "kicker": "RELAX · 피로 회복", "name": "피로 회복 관리",
     "desc": "전신의 긴장을 부드럽게 풀어주는 기본 방문 관리입니다."},
    {"slug": "aroma", "kicker": "AROMA · 아로마", "name": "아로마 관리",
     "desc": "블렌딩 오일의 향과 함께 심신을 이완하는 관리입니다.", "best": True},
    {"slug": "sports", "kicker": "SPORTS · 스포츠", "name": "스포츠 관리",
     "desc": "운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 관리입니다."},
    {"slug": "home-thai", "kicker": "HOME THAI · 홈타이", "name": "홈타이 코스",
     "desc": "건식 타이마사지를 자택·숙소에서 그대로 받는 코스입니다."},
    {"slug": "couple", "kicker": "COUPLE · 커플·가족", "name": "커플·가족 방문 관리",
     "desc": "두 분이 같은 공간에서 동시에 받는 동반 관리입니다."},
    {"slug": "group", "kicker": "GROUP · 기업·단체", "name": "기업·단체 방문 관리",
     "desc": "워크숍·행사 등 단체 인원을 위한 사전 협의형 관리입니다."},
]

TIME_PRICING = [
    {"name": "60분 코스", "price": "90,000", "dur": "60분", "desc": "기본 컨디션·릴랙스 케어"},
    {"name": "90분 코스", "price": "140,000", "dur": "90분", "desc": "가장 많이 선택하는 추천 구성", "best": True},
    {"name": "120분 코스", "price": "180,000", "dur": "120분", "desc": "전신 집중 프리미엄 케어"},
]

# ---------------------------------------------------------------------------
# Shared CSS  (다크 럭스 디자인 시스템 — BLUEPRINT 기준)
# ---------------------------------------------------------------------------
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0b0b0e;--surface:#13131a;--surface-2:#1a1a23;--line:rgba(255,255,255,.08);
  --text:#f3f3f5;--muted:#9a9aa3;--dim:#6c6c75;
  --gold:#d6b274;--rose:#e9b8a7;--copper:#c98a6b;
  --grad:linear-gradient(135deg,#f4d29c 0%,#e9b8a7 45%,#c98a6b 100%);
  --grad-soft:linear-gradient(135deg,rgba(244,210,156,.14),rgba(201,138,107,.06));
}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);line-height:1.65;letter-spacing:-.01em;
  font-family:"Pretendard","Apple SD Gothic Neo","Noto Sans KR",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  -webkit-font-smoothing:antialiased;overflow-x:hidden;
  word-break:keep-all;overflow-wrap:break-word}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}
.serif,.note-num,.step .n{font-family:"Cormorant Garamond","Noto Serif KR",Georgia,serif;font-weight:300;font-style:italic}
.grad{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}
section.block{padding:96px 0}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:11.5px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--gold);font-weight:700}
.pulse{width:7px;height:7px;border-radius:50%;background:var(--rose);box-shadow:0 0 0 0 rgba(233,184,167,.6);animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(233,184,167,.55)}70%{box-shadow:0 0 0 9px rgba(233,184,167,0)}100%{box-shadow:0 0 0 0 rgba(233,184,167,0)}}
h2.sec{font-size:clamp(28px,4vw,46px);letter-spacing:-.03em;font-weight:800;margin:14px 0 10px}
.sec-lead{color:var(--muted);max-width:660px;font-size:15px}
/* header */
header{position:sticky;top:0;z-index:60;backdrop-filter:blur(14px);
  background:rgba(11,11,14,.78);border-bottom:1px solid var(--line)}
.nav{max-width:1240px;margin:0 auto;padding:14px 20px;display:flex;align-items:center;gap:12px}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:18px;letter-spacing:-.02em;white-space:nowrap;flex-shrink:0}
.brand .mark{width:34px;height:34px;border-radius:10px;background:var(--grad);display:grid;place-items:center;
  color:#1a1208;font-weight:800;font-family:"Cormorant Garamond",serif;font-style:italic;font-size:20px}
.brand small{display:block;font-size:10.5px;letter-spacing:.16em;color:var(--gold);font-weight:700}
.menu{list-style:none;display:flex;align-items:center;gap:2px;margin-left:auto}
.menu>li{position:relative}
.menu>li>a{display:block;padding:10px 8px;font-size:13px;color:var(--text);border-radius:9px;font-weight:600;white-space:nowrap}
.menu>li>a:hover{background:rgba(255,255,255,.05)}
.menu>li>a.active{color:var(--gold)}
.submenu{position:absolute;top:calc(100% + 6px);left:0;min-width:212px;list-style:none;padding:8px;
  background:linear-gradient(160deg,var(--surface),var(--surface-2));border:1px solid var(--line);
  border-radius:14px;box-shadow:0 20px 48px rgba(0,0,0,.45);opacity:0;visibility:hidden;transform:translateY(6px);
  transition:.22s;z-index:70;max-height:72vh;overflow:auto}
.menu>li:hover>.submenu,.menu>li:focus-within>.submenu{opacity:1;visibility:visible;transform:none}
.submenu li{position:relative}
.submenu li a{display:block;padding:9px 12px;font-size:13.5px;color:var(--muted);border-radius:9px;white-space:nowrap}
.submenu li a:hover{background:rgba(255,255,255,.05);color:var(--text)}
.submenu li.has-sub>a::after{content:"›";float:right;color:var(--dim);font-weight:700}
.submenu .sub2{position:absolute;top:-9px;left:calc(100% + 7px);transform:translateX(6px)}
.submenu li.has-sub:hover>.sub2,.submenu li.has-sub:focus-within>.sub2{opacity:1;visibility:visible;transform:none}
.cta-pill{margin-left:4px;padding:10px 14px!important;background:var(--grad);color:#1a1208!important;
  border-radius:999px;font-weight:800!important;white-space:nowrap}
.toggle{display:none;margin-left:auto;background:none;border:1px solid var(--line);color:var(--text);
  font-size:20px;width:44px;height:44px;border-radius:11px;cursor:pointer}
/* hero */
.hero{position:relative;overflow:hidden;border-bottom:1px solid var(--line)}
.hero::before{content:"";position:absolute;inset:0;z-index:0;
  background:radial-gradient(60% 70% at 80% 10%,rgba(233,184,167,.16),transparent 60%),
             radial-gradient(50% 60% at 10% 90%,rgba(214,178,116,.12),transparent 60%),
             radial-gradient(40% 50% at 50% 50%,rgba(201,138,107,.08),transparent 70%)}
.hero-inner{position:relative;z-index:1;display:grid;grid-template-columns:1.12fr .88fr;gap:48px;
  align-items:center;max-width:1240px;margin:0 auto;padding:88px 24px}
.hero h1{font-size:clamp(34px,5.4vw,62px);font-weight:800;letter-spacing:-.038em;line-height:1.08;margin:18px 0}
.hero .lead{color:var(--muted);font-size:16px;max-width:520px;margin-bottom:26px}
.actions{display:flex;gap:12px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:8px;padding:14px 22px;border-radius:12px;font-weight:700;
  font-size:14.5px;transition:.25s;border:1px solid transparent}
.btn-primary{background:var(--grad);color:#1a1208}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 14px 34px rgba(201,138,107,.35)}
.btn-ghost{border-color:var(--line);color:var(--text)}
.btn-ghost:hover{border-color:rgba(244,210,156,.4);transform:translateY(-2px)}
.trust{margin-top:24px;display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--muted);font-size:13px}
.trust b{color:var(--text)}
.hero-visual{position:relative}
.glass{position:relative;z-index:2;border-radius:20px;padding:26px;
  background:linear-gradient(160deg,rgba(255,255,255,.06),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.12);backdrop-filter:blur(20px);transform:rotate(1.5deg)}
.glass h3{font-size:13px;color:var(--gold);letter-spacing:.04em;margin-bottom:14px}
.glass h3 b{display:block;font-size:21px;color:var(--text);letter-spacing:-.02em;margin-top:4px}
.book-row{display:flex;justify-content:space-between;padding:11px 0;border-top:1px solid var(--line);font-size:14px}
.book-row span:first-child{color:var(--muted)}
.bk{display:block;text-align:center;margin-top:16px;padding:13px;border-radius:12px;background:var(--grad);color:#1a1208;font-weight:800}
.floating{position:absolute;z-index:3;padding:11px 14px;border-radius:12px;font-size:12px;font-weight:600;
  background:linear-gradient(160deg,var(--surface),var(--surface-2));border:1px solid var(--line);
  box-shadow:0 14px 34px rgba(0,0,0,.4)}
.fl-1{top:-18px;left:-14px;transform:rotate(-4deg)}
.fl-2{bottom:-16px;right:-10px;transform:rotate(3deg)}
.fl-1 .dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#6fe3a1;margin-right:6px}
/* marquee */
.marquee{overflow:hidden;border-bottom:1px solid var(--line);background:var(--surface)}
.marquee-track{display:flex;gap:0;white-space:nowrap;width:max-content;animation:scroll 34s linear infinite}
.marquee-track span{padding:14px 26px;color:var(--muted);font-size:13px;letter-spacing:.04em}
.marquee-track span::after{content:"·";margin-left:26px;color:var(--dim)}
@keyframes scroll{to{transform:translateX(-50%)}}
/* cards grid */
.grid{display:grid;gap:16px}
.g4{grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.g2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.card{padding:24px;border-radius:16px;border:1px solid var(--line);
  background:linear-gradient(135deg,var(--surface),var(--surface-2));transition:.3s}
.card:hover{transform:translateY(-4px);border-color:rgba(244,210,156,.28);box-shadow:0 18px 40px rgba(0,0,0,.3)}
.card .k{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);font-weight:700}
.card h3{margin:10px 0 8px;font-size:19px;font-weight:800}
.card p{color:var(--muted);font-size:14px}
.card .more{display:inline-block;margin-top:14px;color:var(--rose);font-size:13.5px;font-weight:700}
.card:hover .more{transform:translateX(4px)}
/* note card */
.note-card{display:flex;gap:22px;padding:26px 28px;border-radius:18px;position:relative;overflow:hidden;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));border:1px solid var(--line);transition:.3s}
.note-card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--grad);opacity:0;transition:.3s}
.note-card:hover::before{opacity:1}
.note-card:hover{transform:translateY(-2px);box-shadow:0 18px 44px rgba(0,0,0,.32);border-color:rgba(244,210,156,.28)}
.note-num{font-size:44px;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent;flex-shrink:0;line-height:1}
.note-title{font-size:18px;font-weight:800;margin-bottom:10px}
.note-text{max-width:660px}
.note-text p{margin:0 0 9px;color:#c8c8d0;font-size:14.5px;line-height:1.78}
.note-stack{display:flex;flex-direction:column;gap:14px}
/* chips */
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
.chip{padding:9px 14px;border-radius:999px;border:1px solid var(--line);background:var(--surface);
  font-size:12.5px;color:var(--muted)}
.chip b{color:var(--gold)}
/* 코스별 기본 요금 메뉴 */
.pmenu{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:28px}
.pmenu-card{position:relative;text-align:center;padding:36px 24px 26px;border-radius:18px;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));border:1px solid var(--line);transition:.3s}
.pmenu-card:hover{transform:translateY(-4px);border-color:rgba(244,210,156,.3);box-shadow:0 18px 42px rgba(0,0,0,.32)}
.pmenu-card.best{border-color:rgba(244,210,156,.5);box-shadow:0 16px 42px rgba(201,138,107,.2)}
.pmenu-name{font-weight:800;font-size:17px;margin-bottom:16px}
.pmenu-price{font-size:clamp(30px,4vw,40px);font-weight:800;letter-spacing:-.035em;line-height:1}
.pmenu-price span{font-size:15px;font-weight:600;color:var(--muted);margin-left:3px;letter-spacing:0}
.pmenu-dur{color:var(--gold);font-size:13px;font-weight:700;margin-top:10px}
.pmenu-desc{color:var(--muted);font-size:13.5px;margin:8px 0 22px}
.pmenu-btn{display:block;padding:13px;border-radius:11px;border:1px solid var(--line);font-weight:700;font-size:14px;transition:.25s}
.pmenu-btn:hover{border-color:rgba(244,210,156,.5);transform:translateY(-1px)}
.pmenu-card.best .pmenu-btn{background:var(--grad);color:#1a1208;border-color:transparent}
.pmenu-badge{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--grad);color:#1a1208;
  font-size:11.5px;font-weight:800;padding:5px 15px;border-radius:999px;box-shadow:0 6px 16px rgba(201,138,107,.35)}
.pmenu-note{margin-top:20px;color:var(--muted);font-size:13px}
.pmenu-note a{color:var(--gold);font-weight:700;white-space:nowrap}
@media(max-width:760px){.pmenu{grid-template-columns:1fr}}
/* faq */
details{border:1px solid var(--line);border-radius:14px;padding:0;margin-bottom:12px;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));overflow:hidden}
summary{list-style:none;cursor:pointer;padding:18px 22px;font-weight:700;font-size:15px;
  display:flex;justify-content:space-between;align-items:center;gap:14px}
summary::-webkit-details-marker{display:none}
summary span{color:var(--gold);font-size:22px;transition:.25s;flex-shrink:0}
details[open] summary span{transform:rotate(45deg)}
details>div{padding:0 22px 20px;color:var(--muted);font-size:14.5px;line-height:1.78}
/* breadcrumb */
.crumb{font-size:12.5px;color:var(--dim);padding:18px 0}
.crumb a{color:var(--muted)}
.crumb a:hover{color:var(--gold)}
.crumb b{color:var(--text)}
/* review */
.review{padding:22px;border-radius:16px;border:1px solid var(--line);
  background:linear-gradient(135deg,var(--surface),var(--surface-2))}
.review .stars{color:var(--gold);font-size:13px;letter-spacing:2px}
.review p{margin:10px 0;font-size:14px;color:#c8c8d0;line-height:1.7}
.review .who{font-size:12.5px;color:var(--muted)}
/* cta band */
.cta-band{position:relative;overflow:hidden;text-align:center;padding:88px 24px;border-top:1px solid var(--line)}
.cta-band::before{content:"";position:absolute;inset:0;background:radial-gradient(50% 80% at 50% 0%,rgba(233,184,167,.16),transparent 60%)}
.cta-band>div{position:relative}
.cta-band h2{font-size:clamp(26px,4vw,42px);font-weight:800;letter-spacing:-.03em}
.cta-band p{color:var(--muted);margin:14px auto 26px;max-width:680px;line-height:1.85}
/* footer */
.site-footer{border-top:1px solid var(--line);background:var(--surface);padding:64px 0 36px;font-size:13.5px}
.footer-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:30px}
.footer-grid h4{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin-bottom:14px}
.footer-grid a{display:block;color:var(--muted);padding:5px 0}
.footer-grid a:hover{color:var(--text)}
.footer-brand b{font-size:17px}
.footer-brand p{color:var(--muted);margin-top:10px;max-width:280px;line-height:1.7}
.footer-ops{margin:34px 0;padding:22px;border-radius:14px;background:var(--grad-soft);
  border:1px solid var(--line);display:flex;flex-wrap:wrap;gap:14px 40px}
.footer-ops div b{color:var(--gold);display:block;font-size:11px;letter-spacing:.12em;margin-bottom:4px}
.company-info{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;color:var(--dim);font-size:12.5px;
  padding-top:24px;border-top:1px solid var(--line)}
.company-info b{color:var(--muted)}
.footer-policies{display:flex;flex-wrap:wrap;gap:8px 18px;margin:22px 0 14px}
.footer-policies a{color:var(--muted);font-size:12.5px}
.footer-bottom{color:var(--dim);font-size:12px;line-height:1.7;border-top:1px solid var(--line);padding-top:18px}
.legal-note{margin-top:8px;color:var(--dim)}
/* 콘텐츠 아티클 + 저자 표기(E-E-A-T) */
.byline{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:18px;color:var(--dim);font-size:12.5px}
.byline span{display:inline-flex;align-items:center}
.byline span+span::before{content:"·";margin-right:16px;color:var(--dim)}
.byline .au{color:var(--muted);font-weight:700}
.data-box{margin:24px 0;padding:20px 22px;border-radius:14px;background:var(--grad-soft);border:1px solid var(--line)}
.data-box b{color:var(--gold);display:block;font-size:11px;letter-spacing:.14em;margin-bottom:8px;text-transform:uppercase}
.data-box p{color:var(--muted);font-size:13.5px;margin:0;line-height:1.8}
/* 다크 럭스 — 콘텐츠 페이지 (네이비 패널 + 골드 + 좌측 TOC) */
.lux-hero{position:relative;overflow:hidden;border-bottom:1px solid rgba(244,210,156,.14);
  background:radial-gradient(70% 120% at 88% -10%,rgba(233,184,167,.14),transparent 60%),
             linear-gradient(180deg,#0d1018,#0b0b0e);padding:54px 0 40px}
.lux-h1{font-size:clamp(30px,5vw,52px);font-weight:800;letter-spacing:-.03em;line-height:1.1;margin:14px 0 12px;color:#fff}
.lux-lead{color:#cfd2da;font-size:16.5px;line-height:1.8;max-width:760px}
.lux-body{background:linear-gradient(180deg,#0b0b0e,#0c0e15 40%,#0b0b0e)}
.lux-grid{display:grid;grid-template-columns:240px 1fr;gap:46px;align-items:start}
.toc{position:sticky;top:86px}
.toc-inner{border:1px solid rgba(244,210,156,.2);border-radius:16px;padding:18px 14px;
  background:linear-gradient(165deg,#10131f,#0a0c13);box-shadow:0 18px 40px rgba(0,0,0,.35)}
.toc-label{display:block;font-size:10.5px;letter-spacing:.2em;color:var(--gold);font-weight:800;text-transform:uppercase;margin:0 0 12px 8px}
.toc ul{list-style:none;margin:0;padding:0}
.toc li a{display:block;padding:8px 12px;font-size:13px;line-height:1.4;color:var(--muted);
  border-left:2px solid transparent;border-radius:0 8px 8px 0;transition:.2s}
.toc li a:hover{color:var(--text);background:rgba(255,255,255,.05)}
.toc li a.active{color:var(--gold);border-left-color:var(--gold);background:rgba(244,210,156,.09);font-weight:700}
.lux-main{min-width:0}
.lux-sec{position:relative;overflow:hidden;background:linear-gradient(165deg,#121626,#0c0e16);
  border:1px solid rgba(255,255,255,.08);border-radius:18px;padding:28px 32px;margin-bottom:18px}
.lux-sec::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--grad)}
.lux-sec h2{font-size:clamp(20px,2.5vw,27px);font-weight:800;letter-spacing:-.02em;margin:0 0 14px;color:#fff}
.lux-sec h3{color:var(--gold);font-size:16.5px;font-weight:800;margin:20px 0 7px}
.lux-sec p{color:#e4e5ec;font-size:15.5px;line-height:1.9;margin:0 0 12px}
.lux-sec>ul{margin:6px 0 14px;padding:0;list-style:none}
.lux-sec>ul li{position:relative;padding:8px 0 8px 22px;color:#e4e5ec;font-size:15px;line-height:1.65;
  border-bottom:1px solid rgba(255,255,255,.06)}
.lux-sec>ul li::before{content:"";position:absolute;left:3px;top:15px;width:6px;height:6px;border-radius:50%;background:var(--grad)}
.lux-sec>ul li:last-child{border-bottom:none}
.lux-sec a{color:var(--rose);font-weight:600;border-bottom:1px solid rgba(233,184,167,.4)}
.lux-sec a:hover{color:var(--gold);border-bottom-color:var(--gold)}
.lux-sec strong{color:#fff}
.lux-sec .grid{margin-top:6px}
.lux-main .data-box{margin:4px 0 0;background:linear-gradient(135deg,rgba(244,210,156,.12),rgba(201,138,107,.05));
  border:1px solid rgba(244,210,156,.22)}
@media(max-width:980px){
  .lux-grid{grid-template-columns:1fr;gap:14px}
  .toc{position:static}
  .toc-inner{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:12px 14px}
  .toc-label{margin:0 4px 0 2px}
  .toc ul{display:flex;flex-wrap:wrap;gap:6px}
  .toc li a{border-left:none;border:1px solid var(--line);border-radius:999px;padding:6px 13px;font-size:12px}
  .toc li a.active{background:var(--grad);color:#1a1208;border-color:transparent}
  .lux-sec{padding:22px 20px}
}
/* 플로팅 전화예약 버튼 (전 페이지) */
.call-fab{position:fixed;right:20px;bottom:20px;z-index:90;display:inline-flex;align-items:center;gap:9px;
  padding:14px 20px 14px 16px;border-radius:999px;color:#fff;font-weight:800;font-size:14.5px;letter-spacing:-.01em;
  background:linear-gradient(135deg,#ffa23c,#ff7a18 55%,#f4600a);
  box-shadow:0 12px 30px rgba(255,122,24,.5);transition:transform .25s,box-shadow .25s}
.call-fab:hover{transform:translateY(-3px);box-shadow:0 16px 38px rgba(255,122,24,.6)}
.call-fab::before{content:"";position:absolute;inset:0;border-radius:999px;border:2px solid #ff7a18;
  animation:fabpulse 1.8s ease-out infinite;pointer-events:none}
.call-fab-ic{position:relative;display:grid;place-items:center;width:26px;height:26px;
  transform-origin:60% 60%;animation:fabring 1.5s ease-in-out infinite}
.call-fab-ic svg{width:21px;height:21px;fill:#fff}
.call-fab-tx{position:relative;white-space:nowrap}
.call-fab-tx small{display:block;font-size:11px;font-weight:700;opacity:.92;letter-spacing:.01em}
@keyframes fabring{0%,62%,100%{transform:rotate(0)}8%,26%{transform:rotate(-15deg)}17%,35%{transform:rotate(15deg)}}
@keyframes fabpulse{0%{transform:scale(1);opacity:.7}100%{transform:scale(1.55);opacity:0}}
@media(max-width:560px){.call-fab{right:14px;bottom:14px;padding:14px}.call-fab-tx{display:none}}
@media(prefers-reduced-motion:reduce){.call-fab-ic,.call-fab::before{animation:none}}
/* reveal */
.reveal{opacity:0;transform:translateY(20px);transition:.8s}
.reveal.in{opacity:1;transform:none}
/* perf */
#region,#process,#reviews,#about,#faq,.cta-band,.site-footer{content-visibility:auto;contain-intrinsic-size:auto 700px}
.card,.note-card,.review{contain:layout style}
@media(hover:none){.glass,.floating{backdrop-filter:none}}
@media(prefers-reduced-motion:reduce){.marquee-track,.pulse{animation:none}.reveal{opacity:1;transform:none}}
@media(max-width:1240px){
  .toggle{display:block}
  .menu{position:fixed;inset:64px 0 auto 0;flex-direction:column;align-items:stretch;gap:2px;margin:0;
    padding:14px;background:var(--bg);border-bottom:1px solid var(--line);max-height:calc(100vh - 64px);
    overflow:auto;transform:translateY(-12px);opacity:0;visibility:hidden;transition:.25s}
  .menu.open{transform:none;opacity:1;visibility:visible}
  .menu>li>a{padding:13px 12px}
  .submenu,.submenu .sub2{position:static;opacity:1;visibility:visible;transform:none;box-shadow:none;
    background:transparent;border:none;padding:0 0 6px 12px;min-width:0;left:auto;top:auto;max-height:none}
  .submenu .sub2{padding-left:14px}
  .submenu li.has-sub>a::after{content:""}
  .cta-pill{text-align:center}
  .hero-inner{grid-template-columns:1fr;gap:36px}
  .hero-visual{max-width:420px}
  .footer-grid{grid-template-columns:1fr 1fr}
  .company-info{grid-template-columns:1fr 1fr}
}
@media(max-width:560px){
  .footer-grid,.company-info{grid-template-columns:1fr}
  .note-card{flex-direction:column;gap:12px}
  .hero-inner{padding:56px 24px}
}
"""

# ---------------------------------------------------------------------------
# Navigation  (상단 메뉴 — 하위 메뉴에는 지역명·역명만, 키워드 반복 금지)
# ---------------------------------------------------------------------------
def menu_html(active):
    def li(key, href, label, sub=None, cta=False):
        cls = ' class="active"' if active == key else ""
        pop = ' aria-haspopup="true"' if sub else ""
        a = f'<a href="{href}"{cls}{pop}>{label}</a>'
        if cta:
            a = f'<a class="cta-pill" href="tel:{PHONE_TEL}">24시 예약</a>'
        sub_html = ""
        if sub:
            parts = []
            for item in sub:
                if len(item) == 3:  # 3단 항목 (노선 → 역)
                    h, t, kids = item
                    kids_html = "".join(f'<li><a href="{kh}">{kt}</a></li>' for kh, kt in kids)
                    parts.append(
                        f'<li class="has-sub"><a href="{h}" aria-haspopup="true">{t}</a>'
                        f'<ul class="submenu sub2">{kids_html}</ul></li>')
                else:
                    h, t = item
                    parts.append(f'<li><a href="{h}">{t}</a></li>')
            sub_html = f'<ul class="submenu">{"".join(parts)}</ul>'
        return f"<li>{a}{sub_html}</li>"

    st = {s["slug"]: s for s in STATIONS}
    line1 = [(f"/geumcheon-gu/stations/{k}/", st[k]["name"])
             for k in ["gasan-digital-complex-station", "doksan-station", "geumcheon-gu-office-station"]]
    line7 = [("/geumcheon-gu/stations/gasan-digital-complex-station/", "가산디지털단지역")]
    items = [
        li("home", "/", "홈"),
        li("geumcheon", "/geumcheon-gu/", "금천 출장마사지", [
            ("/geumcheon-gu/", "금천 출장마사지 안내"),
            ("/geumcheon-gu/home-thai/", "금천 홈타이 안내"),
            ("/geumcheon-gu/coverage/", "금천구 전지역 방문 가능 안내"),
            ("/geumcheon-gu/stations/", "금천 지하철역 인근 안내"),
            ("/geumcheon-gu/hours/", "예약 가능 시간"),
            ("/course/guide/", "코스 선택 안내"),
            ("/geumcheon-gu/checklist/", "이용 전 확인사항"),
            ("/geumcheon-gu/safety/", "위생 및 안전 안내"),
            ("/geumcheon-gu/faq/", "자주 묻는 질문"),
        ]),
        li("area", "/geumcheon-gu/area/", "지역별 안내", [
            ("/geumcheon-gu/area/", "금천구 전체"),
        ] + [(f"/geumcheon-gu/{d['slug']}/", d["name"]) for d in DONGS]),
        li("stations", "/geumcheon-gu/stations/", "지하철역별 안내", [
            ("/geumcheon-gu/stations/", "금천 지하철역 전체"),
            ("/geumcheon-gu/stations/#line1", "1호선 금천권", line1),
            ("/geumcheon-gu/stations/#line7", "7호선 금천권", line7),
        ]),
        li("themes", "/themes/", "테마별 안내", [
            ("/themes/", "전체 테마"),
        ] + [(f"/themes/{t['slug']}/", t["name"]) for t in THEMES]),
        li("course", "/course/", "코스안내", [
            ("/course/", "전체 코스"),
        ] + [(f"/course/{c['slug']}/", c["name"]) for c in COURSES] + [
            ("/course/price/", "가격 안내"),
            ("/course/guide/", "코스 선택 가이드"),
        ]),
        li("reservation", "/reservation/", "예약안내"),
        li("guide", "/guide/", "이용가이드"),
        li("magazine", "/magazine/", "매거진", [
            ("/magazine/", "전체 글"),
        ] + [(f"/magazine/{p['slug']}/", p["menu"]) for p in POSTS]),
        li("reviews", "/reviews/", "후기", [
            ("/reviews/#all", "전체 후기"),
            ("/reviews/#region", "지역별 후기"),
            ("/reviews/#station", "역세권 후기"),
            ("/reviews/#write", "후기 작성 안내"),
        ]),
        li("customer", "/customer/", "고객센터", [
            ("/customer/#notice", "공지사항"),
            ("/geumcheon-gu/faq/", "자주 묻는 질문"),
            ("/customer/#inquiry", "1:1 문의"),
            ("/customer/#partner", "제휴·기업 문의"),
            ("/privacy/", "개인정보처리방침"),
            ("/terms/", "이용약관"),
        ]),
        li("cta", "#", "", cta=True),
    ]
    return (
        '<header><nav class="nav" aria-label="주 메뉴">'
        '<a class="brand" href="/" aria-label="금천 VIP 마사지 홈">'
        '<span class="mark">V</span><span>금천 VIP<small>출장마사지 · 홈타이</small></span></a>'
        '<button class="toggle" aria-expanded="false" aria-controls="primary-menu" aria-label="메뉴 열기">☰</button>'
        f'<ul id="primary-menu" class="menu">{"".join(items)}</ul>'
        "</nav></header>"
    )

# ---------------------------------------------------------------------------
# Footer  (지역명·역명 대량 나열 금지 — 핵심 링크만)
# ---------------------------------------------------------------------------
def footer_html():
    dong_links = "".join(f'<a href="/geumcheon-gu/{d["slug"]}/">{d["name"]}</a>' for d in DONGS)
    return f"""<footer class="site-footer"><div class="wrap">
<div class="footer-grid">
  <div class="footer-brand">
    <b class="grad">{BRAND}</b>
    <p>서울 금천구 전지역 방문 마사지·홈타이 예약 안내입니다. 지역·역·테마별 상세 안내는 각 페이지에서 확인하세요.</p>
  </div>
  <div><h4>지역·역 안내</h4>
    <a href="/geumcheon-gu/area/">금천구 전체</a>{dong_links}
    <a href="/geumcheon-gu/stations/">지하철역별 안내</a></div>
  <div><h4>테마·코스</h4>
    <a href="/themes/">테마별 안내</a><a href="/course/">코스안내</a>
    <a href="/course/price/">가격 안내</a><a href="/course/guide/">코스 선택 가이드</a></div>
  <div><h4>이용 안내</h4>
    <a href="/reservation/">예약안내</a><a href="/guide/">이용가이드</a>
    <a href="/magazine/">매거진</a><a href="/reviews/">후기</a><a href="/customer/">고객센터</a></div>
</div>
<div class="footer-ops">
  <div><b>운영 시간</b>{HOURS}</div>
  <div><b>전화 예약·상담</b><a href="tel:{PHONE_TEL}">{PHONE_DISP}</a></div>
</div>
<div class="company-info">
  <div><b>상호</b> {COMPANY['name']}</div>
  <div><b>대표</b> {COMPANY['ceo']}</div>
  <div><b>사업자등록번호</b> {COMPANY['biz_no']}</div>
  <div><b>주소</b> {COMPANY['addr']}</div>
  <div><b>통신판매업신고</b> {COMPANY['sales_no']}</div>
  <div><b>개인정보보호책임자</b> {COMPANY['privacy_officer']}</div>
</div>
<div class="footer-policies">
  <a href="/customer/#notice">공지사항</a><a href="/geumcheon-gu/faq/">자주 묻는 질문</a>
  <a href="/customer/#inquiry">1:1 문의</a><a href="/privacy/">개인정보처리방침</a>
  <a href="/terms/">이용약관</a><a href="/youth/">청소년보호정책</a>
</div>
<div class="footer-bottom">
  © 2026 {COMPANY['name']}. All rights reserved.
  <div class="legal-note">본 서비스는 의료 행위가 아닌 건강관리(이완·휴식) 목적의 방문 관리 서비스이며, 만 19세 이상 성인을 대상으로 합니다. 불법·퇴폐 행위는 일절 제공하지 않습니다.</div>
</div>
</div></footer>"""

# ---------------------------------------------------------------------------
# Shared JS  (idle-loaded)
# ---------------------------------------------------------------------------
JS = """
(function(){
  var t=document.querySelector('.toggle'),m=document.getElementById('primary-menu');
  if(t&&m){t.addEventListener('click',function(){
    var o=m.classList.toggle('open');t.setAttribute('aria-expanded',o);});}
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&m){m.classList.remove('open');}});
  function idle(fn){if('requestIdleCallback'in window){requestIdleCallback(fn,{timeout:1500});}else{setTimeout(fn,1);}}
  idle(function(){
    if(!('IntersectionObserver'in window)){document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('in');});return;}
    var io=new IntersectionObserver(function(es){es.forEach(function(e){
      if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12,rootMargin:'80px'});
    document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
    var secs=[].slice.call(document.querySelectorAll('.lux-sec')),
        links=[].slice.call(document.querySelectorAll('.toc a'));
    if(secs.length&&links.length){
      var spy=new IntersectionObserver(function(es){es.forEach(function(e){
        if(e.isIntersecting){var id=e.target.id;
          links.forEach(function(a){a.classList.toggle('active',a.getAttribute('href')==='#'+id);});}});
      },{rootMargin:'-35% 0px -55% 0px'});
      secs.forEach(function(s){spy.observe(s);});
    }
  });
})();
"""

# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------
def page(path, title, desc, active, body, jsonld=None, og_type="website"):
    canonical = BASE_URL + path
    ld = ""
    if jsonld:
        blocks = jsonld if isinstance(jsonld, list) else [jsonld]
        ld = "".join(
            '<script type="application/ld+json">'
            + json.dumps(b, ensure_ascii=False, separators=(",", ":"))
            + "</script>"
            for b in blocks
        )
    og_img = BASE_URL + "/assets/og-cover.jpg"
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b0b0e">
<meta name="format-detection" content="telephone=no">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="googlebot" content="index,follow">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="author" content="{COMPANY['name']} 운영팀">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="ko-KR" href="{canonical}">
<link rel="alternate" hreflang="x-default" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="ko_KR">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_img}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<style>{CSS}</style>
{ld}
</head>
<body>
{menu_html(active)}
{body}
{footer_html()}
{call_fab()}
<script>{JS}</script>
</body>
</html>"""

def call_fab():
    """오렌지색 플로팅 전화예약 버튼 — 전 페이지 고정 노출."""
    phone_svg = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8c1.4 2.8 3.8 5.2 '
                 '6.6 6.6l2.2-2.2c.28-.28.68-.36 1.02-.24 1.12.37 2.33.57 3.58.57.55 0 1 .45 1 '
                 '1V20c0 .55-.45 1-1 1C10.4 21 3 13.6 3 4.4c0-.55.45-1 1-1h3.6c.55 0 1 .45 1 1 0 '
                 '1.25.2 2.46.57 3.58.12.34.04.74-.24 1.02l-2.2 2.2z"/></svg>')
    return (f'<a class="call-fab" href="tel:{PHONE_TEL}" aria-label="전화 예약 {PHONE_DISP}">'
            f'<span class="call-fab-ic">{phone_svg}</span>'
            f'<span class="call-fab-tx">전화 예약<small>{PHONE_DISP}</small></span></a>')

# ---------------------------------------------------------------------------
# Reusable body builders
# ---------------------------------------------------------------------------
def breadcrumb(items):
    parts = []
    for href, label in items:
        parts.append(f'<a href="{href}">{label}</a>' if href else f"<b>{label}</b>")
    return f'<div class="wrap"><nav class="crumb" aria-label="탐색경로">{" › ".join(parts)}</nav></div>'

def bc_ld(trail):
    el = []
    for i, (p, n) in enumerate(trail):
        item = {"@type": "ListItem", "position": i + 1, "name": n}
        if p:
            item["item"] = BASE_URL + p
        el.append(item)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": el}

def faq_block(qas, heading="자주 묻는 질문"):
    rows = "".join(
        f"<details><summary>{q}<span>+</span></summary><div>{a}</div></details>"
        for q, a in qas
    )
    return f"""<section class="block" id="faq"><div class="wrap">
<span class="eyebrow"><span class="pulse"></span>FAQ</span>
<h2 class="sec">{heading}</h2>
<div style="margin-top:26px;max-width:820px">{rows}</div>
</div></section>"""

def faq_ld(qas):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in qas
        ],
    }

def notes_block(eyebrow, heading, lead, notes, _id="about"):
    cards = "".join(
        f'<div class="note-card reveal"><div class="note-num">{n:02d}</div>'
        f'<div class="note-content"><h3 class="note-title">{t}</h3>'
        f'<div class="note-text">{"".join(f"<p>{p}</p>" for p in ps)}</div></div></div>'
        for n, (t, ps) in enumerate(notes, 1)
    )
    return f"""<section class="block" id="{_id}"><div class="wrap">
<span class="eyebrow"><span class="pulse"></span>{eyebrow}</span>
<h2 class="sec">{heading}</h2>
<p class="sec-lead">{lead}</p>
<div class="note-stack" style="margin-top:30px">{cards}</div>
</div></section>"""

def price_menu_block(anchor="pricing-menu"):
    """코스별 기본 요금 (60·90·120분) — 공통 블록(지역·역 본문에는 반복 금지)."""
    cards = ""
    for p in TIME_PRICING:
        best = " best" if p.get("best") else ""
        badge = '<span class="pmenu-badge">추천</span>' if p.get("best") else ""
        cards += (
            f'<div class="pmenu-card{best}">{badge}'
            f'<div class="pmenu-name">{p["name"]}</div>'
            f'<div class="pmenu-price">{p["price"]}<span>원</span></div>'
            f'<div class="pmenu-dur">{p["dur"]}</div>'
            f'<div class="pmenu-desc">{p["desc"]}</div>'
            f'<a class="pmenu-btn" href="tel:{PHONE_TEL}">예약 문의</a></div>'
        )
    return (
        f'<section class="block" id="{anchor}"><div class="wrap">'
        f'<span class="eyebrow"><span class="pulse"></span>요금 안내</span>'
        f'<h2 class="sec">코스별 기본 요금</h2>'
        f'<p class="sec-lead">60·90·120분 코스별 기본 요금입니다. 숨겨진 추가 비용 없이 투명하게 안내합니다.</p>'
        f'<div class="pmenu">{cards}</div>'
        f'<p class="pmenu-note">지역·예약 시간대·이동 거리에 따라 상담 시 최종 확인됩니다. '
        f'<a href="/course/price/">상세 요금 안내 보기 →</a></p>'
        f'</div></section>'
    )

def offer_ld():
    return {
        "@context": "https://schema.org", "@type": "OfferCatalog",
        "name": "코스별 기본 요금",
        "itemListElement": [
            {"@type": "Offer", "name": p["name"],
             "price": p["price"].replace(",", ""), "priceCurrency": "KRW",
             "description": p["desc"], "url": BASE_URL + "/course/price/"}
            for p in TIME_PRICING
        ],
    }

def cta_band(title="오늘 밤, 가까운 곳에서 휴식을 예약하세요", sub=None):
    sub = sub or f"{HOURS} · 전화 한 통으로 방문 일정과 코스를 안내드립니다."
    return f"""<section class="cta-band"><div>
<span class="eyebrow"><span class="pulse"></span>RESERVE</span>
<h2>{title}</h2><p>{sub}</p>
<div class="actions" style="justify-content:center">
<a class="btn btn-primary" href="tel:{PHONE_TEL}">{PHONE_DISP} 전화하기 →</a>
<a class="btn btn-ghost" href="/reservation/">예약 안내 보기</a>
</div></div></section>"""

def byline():
    """저자·감수·업데이트 표기 (E-E-A-T 신뢰 신호)."""
    return (f'<div class="byline">'
            f'<span class="au">작성 · {BRAND_SHORT} 운영팀</span>'
            f'<span>감수 · {COMPANY["ceo"]} ({COMPANY["name"]})</span>'
            f'<span>최종 업데이트 · {UPDATED.replace("-", ".")}</span></div>')

def article_ld(title, desc, path):
    return {
        "@context": "https://schema.org", "@type": "Article",
        "headline": title, "description": desc, "inLanguage": "ko-KR",
        "author": {"@type": "Organization", "name": BRAND, "url": BASE_URL + "/"},
        "publisher": {"@type": "Organization", "name": COMPANY["name"], "url": BASE_URL + "/"},
        "mainEntityOfPage": BASE_URL + path,
        "image": BASE_URL + "/assets/og-cover.jpg",
        "datePublished": UPDATED, "dateModified": UPDATED,
    }

def render_lux(sections):
    """다크 럭스 섹션 패널 + 좌측 고정 목차(TOC) 생성."""
    toc, panels = [], []
    for i, (title, blocks) in enumerate(sections, 1):
        sid = f"sec-{i}"
        toc.append(f'<li><a href="#{sid}">{title}</a></li>')
        inner = ""
        for b in blocks:
            if isinstance(b, tuple) and b[0] == "ul":
                inner += "<ul>" + "".join(f"<li>{x}</li>" for x in b[1]) + "</ul>"
            elif isinstance(b, tuple) and b[0] == "h3":
                inner += f"<h3>{b[1]}</h3>"
            elif isinstance(b, tuple) and b[0] == "html":
                inner += b[1]
            else:
                inner += f"<p>{b}</p>"
        panels.append(f'<section class="lux-sec reveal" id="{sid}"><h2>{title}</h2>{inner}</section>')
    toc_html = ('<aside class="toc"><div class="toc-inner"><span class="toc-label">목차</span>'
                f'<ul>{"".join(toc)}</ul></div></aside>')
    return toc_html, "".join(panels)

def content_page(path, active, trail, *, title, desc, eyebrow, h1, lead,
                 sections, faq, data_note=None, service=None, show_price=False,
                 top_links=None, extra_schema=None, cta_title=None):
    """E-E-A-T 기준 개별 콘텐츠 페이지 생성기 (다크 럭스 레이아웃 + TOC)."""
    toc_html, panels = render_lux(sections)
    if data_note:
        panels += f'<div class="data-box"><b>현장 운영 메모</b><p>{data_note}</p></div>'
    links_html = ""
    if top_links:
        btns = ""
        for href, label, *rest in top_links:
            primary = rest and rest[0]
            cls = "btn btn-primary" if primary else "btn btn-ghost"
            btns += f'<a class="{cls}" href="{href}">{label}</a>'
        links_html = f'<div class="actions" style="margin-top:22px">{btns}</div>'
    body = (breadcrumb(trail) +
        f'<section class="lux-hero"><div class="wrap">'
        f'<span class="eyebrow"><span class="pulse"></span>{eyebrow}</span>'
        f'<h1 class="lux-h1">{h1}</h1>'
        f'<p class="lux-lead">{lead}</p>{byline()}{links_html}</div></section>'
        f'<section class="block lux-body" style="padding-top:34px"><div class="wrap">'
        f'<div class="lux-grid">{toc_html}<div class="lux-main">{panels}</div></div>'
        f'</div></section>'
        + (price_menu_block() if show_price else "")
        + faq_block(faq) + (cta_band(cta_title) if cta_title else cta_band()))
    jsonld = [bc_ld(trail), article_ld(title, desc, path), faq_ld(faq)]
    if service:
        jsonld.append(service_ld(service[0], service[1], path))
        jsonld.append(offer_ld())
    if extra_schema:
        jsonld += extra_schema
    write(path, page(path, title, desc, active, body, jsonld, og_type="article"))

# ---------------------------------------------------------------------------
# JSON-LD: org / localbusiness / website / service
# ---------------------------------------------------------------------------
def org_ld():
    return {
        "@context": "https://schema.org", "@type": "Organization",
        "name": BRAND, "legalName": COMPANY["name"], "url": BASE_URL + "/",
        "telephone": PHONE_DISP,
        "address": {"@type": "PostalAddress", "addressLocality": "금천구",
                    "addressRegion": "서울특별시", "addressCountry": "KR"},
    }

def website_ld():
    return {
        "@context": "https://schema.org", "@type": "WebSite",
        "name": BRAND, "url": BASE_URL + "/",
    }

def localbiz_ld(name=None, area="서울특별시 금천구", path="/"):
    return {
        "@context": "https://schema.org",
        "@type": "HealthAndBeautyBusiness",
        "name": name or BRAND, "url": BASE_URL + path,
        "telephone": PHONE_DISP, "priceRange": "₩₩",
        "areaServed": {"@type": "AdministrativeArea", "name": area},
        "address": {"@type": "PostalAddress", "addressLocality": "금천구",
                    "addressRegion": "서울특별시", "addressCountry": "KR"},
        "openingHoursSpecification": {"@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            "opens": "00:00", "closes": "23:59"},
    }

def service_ld(name, desc, path):
    return {
        "@context": "https://schema.org", "@type": "Service",
        "name": name, "description": desc, "serviceType": "방문 건강관리(마사지) 서비스",
        "provider": {"@type": "Organization", "name": BRAND, "url": BASE_URL + "/"},
        "areaServed": {"@type": "AdministrativeArea", "name": "서울특별시 금천구"},
        "url": BASE_URL + path,
    }

# ---------------------------------------------------------------------------
def write(path, html):
    if path == "/":
        out = os.path.join(ROOT, "index.html")
    else:
        d = os.path.join(ROOT, path.strip("/"))
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
