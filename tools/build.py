# -*- coding: utf-8 -*-
"""금천 VIP 마사지 — static site generator (페이지 빌더).

순수 정적 HTML(인라인 CSS/JS, 의존성 0)을 생성한다.
구조 원칙(도어웨이 회피):
  - 지역은 대표 동 3개(가산동·독산동·시흥동)만. 숫자 행정동은 대표 동에 통합.
  - 역은 3개 역세권만. 환승역(가산디지털단지역)도 URL은 1개.
  - 테마는 독립 페이지. 지역·역·테마 조합 페이지 생성 금지.
  - 공통 정보(시간·준비물·위생·가격)는 전용 페이지로 링크아웃, 본문 반복 금지.

Run:  python3 tools/build.py
Output: HTML + sitemap.xml + robots.txt + site.webmanifest (repo root)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import (  # noqa: E402
    ROOT, BASE_URL, BRAND, BRAND_SHORT, PHONE_DISP, PHONE_TEL, HOURS,
    INDEXNOW_KEY, COMPANY, DONGS, DONG_ZONES, STATIONS, STATION_ZONES,
    COURSES, TIME_PRICING, THEMES, COURSE_DETAIL, POSTS, UPDATED,
    page, write, breadcrumb, bc_ld, faq_block, faq_ld, notes_block,
    price_menu_block, offer_ld, cta_band, byline, article_ld, render_lux,
    content_page, org_ld, website_ld, localbiz_ld, service_ld,
)
import json  # noqa: E402

DONG_BY_SLUG = {d["slug"]: d for d in DONGS}
STATION_BY_SLUG = {s["slug"]: s for s in STATIONS}
POST_BY_SLUG = {p["slug"]: p for p in POSTS}

# 지역·역 → 매거진 글 추천 (내부링크 교차 연결)
DONG_POSTS = {
    "gasan-dong": ["night-worker-recovery", "home-thai-vs-swedish"],
    "doksan-dong": ["first-time-guide", "couple-massage-guide"],
    "siheung-dong": ["workout-recovery-timing", "sleep-massage"],
}
STATION_POSTS = {
    "gasan-digital-complex-station": ["night-worker-recovery", "hotel-room-massage"],
    "doksan-station": ["first-time-guide", "pressure-guide"],
    "geumcheon-gu-office-station": ["workout-recovery-timing", "sleep-massage"],
}

# 역별 개별화된 SEO description (템플릿 복제 회피)
STATION_SEO_DESC = {
    "gasan-digital-complex-station":
        "가산디지털단지역(1·7호선 환승) 출장마사지·홈타이 안내 - G밸리 지식산업센터, 아울렛, 오피스텔·숙소 생활권별 방문 안내와 평균 도착 24분 기준, 퇴근 동선 이용 팁을 제공합니다.",
    "doksan-station":
        "독산역(1호선) 출장마사지·홈타이 안내 - 역세권 대단지 아파트와 전통 생활권 기준의 방문 안내, 평균 도착 26분 기준, 저녁 시간대 이용 팁을 제공합니다.",
    "geumcheon-gu-office-station":
        "금천구청역(1호선) 출장마사지·홈타이 안내 - 구청 일대와 시흥사거리, 호암산 자락 생활권 기준의 방문 안내, 평균 도착 29분 기준, 주말 등산 후 이용 팁을 제공합니다.",
}

# 역별 고유 이용 팁 (도어웨이 회피: 역마다 다른 1차 정보)
STATION_TIPS = {
    "gasan-digital-complex-station": ("퇴근 동선에 맞춘 이용 팁", [
        "G밸리 퇴근 인파가 몰리는 18~20시에는 역 주변 이동이 느려집니다. 이 시간대 예약이라면 퇴근 직전 미리 전화해 도착 시간을 맞추는 것이 요령입니다.",
        "야근 후라면 지하철에서 내리기 전 전화 한 통으로 충분합니다. 오피스텔 도착 후 씻고 나올 때쯤 관리사가 도착하는 흐름이 이 역세권의 표준 패턴입니다.",
        "주말 아울렛 쇼핑 후 숙소·자택에서 받는 문의도 꾸준합니다. 쇼핑을 마치는 시간을 기준으로 예약해 두면 대기가 없습니다."]),
    "doksan-station": ("독산역 생활권 이용 팁", [
        "역세권 대단지 아파트는 동·호수 체계가 커서, 단지명과 동 번호까지 알려주시면 도착이 눈에 띄게 빨라집니다.",
        "가족 단위 이용이 많은 권역이라 저녁 8~10시대 예약이 집중됩니다. 아이를 재운 뒤 받는 10시 이후 시간대는 상대적으로 여유가 있습니다.",
        "1호선 지연 등으로 귀가가 늦어질 때는 도착 예정 시각 기준으로 예약을 잡아두면 헛걸음이 없습니다."]),
    "geumcheon-gu-office-station": ("금천 남부에서의 이용 팁", [
        "시흥사거리 방면은 버스 환승 거점이라 저녁 퇴근 시간대 도로가 붐빕니다. 이 시간대에는 도착 여유를 10분쯤 더 두고 안내드립니다.",
        "주말에는 호암산 등산 후 하체 집중 문의가 많은 역세권입니다. 하산 전 미리 전화해 두면 집 도착과 거의 동시에 시작할 수 있습니다.",
        "구청·관공서 일대 평일 저녁 예약은 청사 주변보다 주거지 기준 주소로 알려주시는 편이 배정이 빠릅니다."]),
}


def sec(_id, eyebrow, heading, paras, extra=""):
    """홈 허브용 단순 섹션 (H2 + 문단 + 부가 HTML)."""
    ps = "".join(f'<p class="sec-lead" style="max-width:820px;margin-top:10px">{p}</p>' for p in paras)
    return (f'<section class="block" id="{_id}" style="padding:64px 0"><div class="wrap">'
            f'<span class="eyebrow"><span class="pulse"></span>{eyebrow}</span>'
            f'<h2 class="sec">{heading}</h2>{ps}{extra}</div></section>')


# ---- Home (허브: 키워드는 Title·H1·첫문단에만, 상세는 링크아웃) -------------
HOME_FAQ = [
    ("금천구 전지역 방문이 가능한가요?",
     "예약 시간, 정확한 위치, 배정 상황에 따라 가능 여부가 달라집니다. 지역별 안내 페이지에서 가산동, 독산동, 시흥동 기준으로 확인할 수 있습니다."),
    ("가산디지털단지역이나 독산역 근처도 가능한가요?",
     "주요 역세권은 역 상세 페이지에서 주변 생활권과 함께 안내합니다. 정확한 가능 여부는 예약 시 위치를 기준으로 확인합니다."),
    ("독산1동과 독산2동은 왜 따로 없나요?",
     "독산1동부터 독산4동은 독산동 대표 페이지에서 통합 안내하여 중복 페이지 위험을 줄입니다. 시흥1동부터 시흥5동도 시흥동 페이지에서 같은 방식으로 안내합니다."),
    ("당일 예약도 가능한가요?",
     "가능할 수 있지만 저녁 시간대와 주말은 문의가 많을 수 있어 사전 예약을 권장합니다."),
    ("테마별 관리는 어디에서 확인하나요?",
     "스웨디시, 타이마사지, 홈케어 등 테마별 안내 페이지에서 특징과 추천 대상을 확인할 수 있습니다."),
]


def build_home():
    dong_cards = "".join(
        f'<a class="card reveal" href="/geumcheon-gu/{d["slug"]}/"><div class="k">AREA</div>'
        f'<h3>{d["name"]}</h3><p>{d["character"]}</p><span class="more">안내 보기 →</span></a>'
        for d in DONGS)
    station_cards = "".join(
        f'<a class="card reveal" href="/geumcheon-gu/stations/{s["slug"]}/"><div class="k">{s["lines"]}</div>'
        f'<h3>{s["name"]}</h3><p>{s["character"]}입니다.</p><span class="more">안내 보기 →</span></a>'
        for s in STATIONS)
    theme_chips = "".join(
        f'<a class="chip" href="/themes/{t["slug"]}/"><b>{t["name"]}</b></a>' for t in THEMES)
    marquee_items = ["연중무휴 24시간 상담", "금천구 전지역 방문", "당일 예약 가능",
                     "정찰 요금 안내", "위생·안전 관리", "홈타이 · 호텔 방문"]
    marquee = "".join(f"<span>{x}</span>" for x in marquee_items * 2)

    body = f"""
<section class="hero"><div class="hero-inner">
  <div class="hero-copy">
    <span class="eyebrow"><span class="pulse"></span>SEOUL · GEUMCHEON-GU 24H</span>
    <h1>금천 출장마사지·홈타이<br><span class="serif grad">예약 안내</span></h1>
    <p class="lead">가산동·독산동·시흥동과 금천구 주요 역세권까지 — 방문 마사지·홈타이 예약을 연중무휴로 안내드립니다.</p>
    <div class="actions">
      <a class="btn btn-primary" href="tel:{PHONE_TEL}">지금 예약하기 →</a>
      <a class="btn btn-ghost" href="/geumcheon-gu/area/">지역별 안내</a>
    </div>
    <div class="trust">
      <span><b>{HOURS}</b></span><span>·</span>
      <span>평균 도착 <b>30분 내외</b></span><span>·</span><span>금천구 <b>전지역</b></span>
    </div>
  </div>
  <div class="hero-visual">
    <div class="floating fl-1"><span class="dot"></span>LIVE · 24시간 상담 가능</div>
    <div class="glass">
      <h3>VIP SIGNATURE<b>아로마 딥 릴렉스</b></h3>
      <div class="book-row"><span>지역</span><span>금천구 전지역</span></div>
      <div class="book-row"><span>코스</span><span>아로마 90분</span></div>
      <div class="book-row"><span>도착</span><span>평균 30분 내외</span></div>
      <a class="bk" href="tel:{PHONE_TEL}">전화 예약 →</a>
    </div>
    <div class="floating fl-2">GEUMCHEON VIP CARE</div>
  </div>
</div></section>

<div class="marquee" aria-hidden="true"><div class="marquee-track">{marquee}</div></div>

{sec("intro", "SERVICE", "금천 출장마사지·홈타이 서비스 안내", [
    "금천구에서 방문 마사지와 홈타이 예약을 찾는 이용자를 위해 가능 지역, 예약 절차, 코스 선택 기준, 이용 전 확인사항을 안내합니다. "
    "이 페이지는 금천구 전체 구조를 설명하는 허브 역할을 하며, 상세 정보는 지역별·지하철역별·테마별 안내 페이지에서 확인할 수 있도록 구성했습니다.",
    "서비스에 대한 자세한 소개는 <a href='/geumcheon-gu/' style='color:var(--gold);font-weight:700'>금천 출장마사지 안내</a>와 "
    "<a href='/geumcheon-gu/home-thai/' style='color:var(--gold);font-weight:700'>금천 홈타이 안내</a>에서 이어집니다."])}

{sec("coverage", "COVERAGE", "금천구 전지역 방문 가능 안내", [
    "금천구는 가산동, 독산동, 시흥동을 중심으로 지역 안내를 구성합니다. 독산1동부터 독산4동, 시흥1동부터 시흥5동처럼 숫자로 나뉜 행정동은 "
    "별도 페이지를 만들지 않고 대표 동 페이지에서 통합 안내하여 중복 페이지 위험을 줄입니다.",
    "자세한 기준은 <a href='/geumcheon-gu/coverage/' style='color:var(--gold);font-weight:700'>전지역 방문 가능 안내</a>에서 확인하실 수 있습니다."])}

{sec("region", "AREA GUIDE", "지역별 안내", [
    "지역별 안내는 금천구 대표 동 기준으로 구성됩니다. 각 페이지에서는 해당 생활권의 특징, 주변 역세권, 방문 전 확인사항, "
    "예약 가능 시간, 관련 테마를 고유하게 설명합니다."],
    f'<div class="grid g3" style="margin-top:28px">{dong_cards}</div>')}

{sec("station", "STATION GUIDE", "지하철역 인근 안내", [
    "지하철역별 안내는 금천구 주요 역세권을 기준으로 구성합니다. 각 역 페이지에서는 인근 생활권, 주변 대표 동, 예약 가능 시간, "
    "방문 전 준비사항을 설명하며, 출구별 페이지나 역과 테마를 조합한 페이지는 만들지 않습니다."],
    f'<div class="grid g3" style="margin-top:28px">{station_cards}</div>')}

{sec("theme", "THEME GUIDE", "테마별 관리 안내", [
    "테마별 안내에서는 관리 유형별 특징, 추천 대상, 예약 전 확인사항을 설명합니다. 테마는 독립 페이지로 운영하고, "
    "지역 페이지와 역 페이지에서는 관련 테마로만 연결합니다. 지역·역·테마를 조합한 페이지는 만들지 않습니다."],
    f'<div class="chips" style="margin-top:24px">{theme_chips}</div>'
    f'<p style="margin-top:18px"><a class="btn btn-ghost" href="/themes/">전체 테마 보기 →</a></p>')}

{sec("course", "COURSE", "코스 선택 안내", [
    "코스는 이용 목적과 컨디션에 따라 선택하는 것이 좋습니다. 피로 회복, 편안한 휴식, 근육 이완, 숙소 방문, 커플 이용 등 "
    "상황에 맞는 기준을 제시하며, 자세한 설명과 요금은 <a href='/course/' style='color:var(--gold);font-weight:700'>코스안내</a>와 "
    "<a href='/course/guide/' style='color:var(--gold);font-weight:700'>코스 선택 가이드</a>에서 다룹니다."])}

{sec("process", "HOW IT WORKS", "예약 진행 방식", [
    "예약은 희망 지역 또는 역 인근 위치 확인, 희망 시간 확인, 코스와 인원 확인, 방문 가능 여부 안내, 예약 확정 순서로 진행합니다. "
    "저녁 시간대나 주말은 문의가 몰릴 수 있으므로 여유 있는 예약을 권장합니다."])}

{sec("check", "CHECKLIST", "이용 전 확인사항", [
    "원활한 방문 관리를 위해 정확한 주소, 공동현관 출입 방법, 주차 가능 여부, 조용한 공간 확보 여부를 미리 확인하는 것이 좋습니다. "
    "숙소나 오피스텔 이용 시에는 출입 안내와 연락 가능 여부를 함께 확인해야 합니다. "
    "자세한 내용은 <a href='/geumcheon-gu/checklist/' style='color:var(--gold);font-weight:700'>이용 전 확인사항</a>에서 안내합니다."])}

{sec("safety", "HYGIENE & SAFETY", "위생 및 안전 안내", [
    "건전하고 안전한 방문 관리를 위해 위생 기준, 예약 정보 확인, 개인정보 보호, 금지행위 안내를 명확히 제공합니다. "
    "이용 전 서비스 범위와 유의사항을 확인하고, 불법적이거나 무리한 요청은 진행하지 않는다는 기준을 분명히 안내합니다. "
    "상세 기준은 <a href='/geumcheon-gu/safety/' style='color:var(--gold);font-weight:700'>위생 및 안전 안내</a>를 참고해 주세요."])}

{faq_block(HOME_FAQ)}

{cta_band("예약문의",
    "금천 출장마사지·홈타이 예약은 희망 지역, 지하철역 인근 위치, 시간, 코스 정보를 기준으로 가능 여부를 안내합니다. "
    "지역별·지하철역별·테마별 안내를 확인한 뒤 문의하시면 더 빠르게 상담할 수 있습니다.")}
"""
    jsonld = [org_ld(), website_ld(), localbiz_ld(), offer_ld(), faq_ld(HOME_FAQ)]
    html = page("/", "금천 출장마사지·홈타이 | 금천구 전지역 방문 마사지 예약 안내",
                "금천 출장마사지·홈타이 안내 페이지입니다. 가산동, 독산동, 시흥동과 금천구 주요 지하철역 인근, 테마별 관리, 예약 전 확인사항을 확인해보세요.",
                "home", body, jsonld)
    write("/", html)


# ---- 금천 출장마사지 대표 페이지 -------------------------------------------
def build_geumcheon():
    trail = [("/", "홈"), (None, "금천 출장마사지")]
    geumcheon_faq = [
        ("금천 출장마사지는 어디까지 방문하나요?",
         "가산동·독산동·시흥동 등 금천구 전지역을 안내드립니다. 정확한 가능 여부는 예약 시간과 위치에 따라 상담 시 확인해 드립니다."),
        ("홈타이와는 무엇이 다른가요?",
         "출장마사지는 방문 관리 전반을, 홈타이는 그중 건식 타이마사지 방문 코스를 가리킵니다. 금천 홈타이 안내 페이지에서 자세히 설명합니다."),
        ("관리사는 어떤 분이 방문하나요?",
         "위생·안전 가이드라인을 준수하는 관리사가 약속된 시간에 방문하며, 요청 사항은 상담 시 확인해 드립니다."),
        ("예약 후 얼마나 기다리나요?",
         "금천구 기준 평균 24~32분 내외로 도착합니다. 시간대와 정확한 위치, 배정 상황에 따라 달라질 수 있어 예약 시 예상 시간을 함께 안내드립니다."),
        ("숙소나 오피스텔로도 방문하나요?",
         "네. 자택 외에 오피스텔·호텔·레지던스 숙소로도 방문합니다. 건물 출입 방법과 호수를 알려주시면 진행이 빠릅니다."),
    ]
    sections = [
        ("금천 출장마사지 서비스 소개", [
            "금천 출장마사지는 고객이 계신 자택·오피스텔·숙소로 관리사가 방문해 진행하는 방문형 건강관리 서비스입니다.",
            "가산디지털단지의 야근 후 휴식, 독산·시흥 주거 단지의 가족 단위 이용까지 — 금천구 생활 패턴에 맞춰 코스와 시간을 안내드립니다.",
            "본 서비스는 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며, 만 19세 이상 성인을 대상으로 합니다."]),
        ("방문 가능 지역", [
            "금천구는 가산동·독산동·시흥동 3개 대표 동 기준으로 안내합니다. 숫자 행정동(독산1~4동, 시흥1~5동)은 대표 동 페이지에서 통합 안내합니다.",
            ("ul", ['<a href="/geumcheon-gu/area/">금천구 전체 지역 안내</a>',
                    '<a href="/geumcheon-gu/gasan-dong/">가산동</a>',
                    '<a href="/geumcheon-gu/doksan-dong/">독산동</a>',
                    '<a href="/geumcheon-gu/siheung-dong/">시흥동</a>',
                    '<a href="/geumcheon-gu/stations/">지하철역별 안내</a>'])]),
        ("금천 생활권의 특징", [
            "가산동은 지식산업센터와 오피스텔이 밀집한 업무 권역으로 늦은 밤 예약 비중이 높습니다.",
            "독산동은 대단지 아파트와 전통 생활권이 공존해 저녁 시간대 자택 방문 문의가 많고, 시흥동은 금천 남부의 주거 밀집지로 주말 문의가 꾸준합니다.",
            "이런 생활권 차이에 맞춰 각 지역 페이지에서 방문 포인트와 평균 도착 시간을 고유하게 안내합니다."]),
        ("예약 진행 방식", [
            "예약은 다섯 단계로 진행됩니다. 희망 지역(또는 역 인근 위치) 확인, 희망 시간 확인, 코스와 인원 확인, 방문 가능 여부 안내, 예약 확정 순입니다.",
            "전화 한 통이면 전 과정이 끝나며, 상담 중에 예상 도착 시간과 최종 요금까지 함께 안내드립니다.",
            "저녁 시간대(21~24시)와 주말은 문의가 몰릴 수 있으므로, 원하는 시간이 정해져 있다면 미리 예약하실수록 일정 조율이 수월합니다."]),
        ("시간대별 이용 패턴", [
            "낮~초저녁은 도착이 비교적 빠르고 일정 조율이 쉬운 시간대입니다. 밤 21~24시는 하루 중 예약이 가장 집중되는 시간대로, 도착 시간을 넉넉히 안내드립니다.",
            "심야·새벽에도 상담은 가능하며, 위치에 따라 도착 시간이 다소 길어질 수 있습니다. 자세한 기준은 예약 가능 시간 페이지에서 확인하세요."]),
        ("많이 찾는 코스", [
            "피로 회복·아로마·스포츠·홈타이 코스가 가장 많이 선택됩니다. 처음이라면 90분 피로 회복 관리가 가장 무난하고, 건식을 선호하면 홈타이 코스를 권해 드립니다.",
            "코스별 상세 설명과 요금은 전용 페이지에서 확인하세요.",
            ("ul", ['<a href="/course/">전체 코스 보기</a>',
                    '<a href="/course/fatigue/">피로 회복 관리</a>',
                    '<a href="/course/home-thai/">홈타이 코스</a>',
                    '<a href="/course/price/">가격 안내</a>'])]),
        ("이용 전에 알아두면 좋은 점", [
            "방문 전에는 편하게 누울 수 있는 공간과 연락 가능한 번호, 정확한 주소만 준비하시면 됩니다. "
            "공동현관 출입 방법을 미리 알려주시면 도착이 더 빨라집니다.",
            "관리에 사용하는 수건·오일 등 용품은 위생 기준에 맞춰 관리하며, 관리 종료 후에는 사용한 공간을 정돈하고 마무리합니다. "
            "예약 정보로 받은 연락처와 주소는 예약 진행 목적으로만 사용합니다.",
            "처음 이용이라 진행 흐름이 궁금하다면 이용가이드를, 다른 이용자의 경험이 궁금하다면 후기 페이지를 먼저 확인해 보세요."]),
        ("예약·준비·위생은 전용 안내에서", [
            "예약 가능 시간, 방문 전 준비물, 위생·안전 기준은 페이지마다 반복하지 않고 전용 안내에서 자세히 다룹니다.",
            ("ul", ['<a href="/geumcheon-gu/hours/">예약 가능 시간</a>',
                    '<a href="/geumcheon-gu/checklist/">이용 전 확인사항</a>',
                    '<a href="/geumcheon-gu/safety/">위생 및 안전 안내</a>',
                    '<a href="/geumcheon-gu/faq/">자주 묻는 질문</a>'])]),
    ]
    content_page("/geumcheon-gu/", "geumcheon", trail,
        title="금천 출장마사지 안내 | 금천구 방문 마사지 서비스 소개",
        desc="금천 출장마사지 서비스 소개 - 금천구 가산동, 독산동, 시흥동 방문 가능 지역과 생활권 특징, 많이 찾는 코스, 예약 전 확인 링크를 안내합니다.",
        eyebrow="금천구 대표", h1="금천 출장마사지 안내",
        lead="서울 금천구 전지역을 대상으로 하는 방문 마사지 예약 안내입니다. "
             "지역·역·테마별 상세 안내로 연결되는 대표 페이지입니다.",
        sections=sections, faq=geumcheon_faq,
        top_links=[("tel:" + PHONE_TEL, "예약문의", True),
                   ("/geumcheon-gu/area/", "지역별 안내"), ("/course/", "코스안내")],
        service=("금천 출장마사지", "서울 금천구 전지역 방문 건강관리 서비스"),
        extra_schema=[localbiz_ld(name=BRAND, path="/geumcheon-gu/")],
        cta_title="금천 방문 예약을 도와드릴까요?")


# ---- 금천 홈타이 안내 -------------------------------------------------------
def build_homethai():
    trail = [("/", "홈"), ("/geumcheon-gu/", "금천 출장마사지"), (None, "금천 홈타이 안내")]
    ht_faq = [
        ("홈타이는 오일을 사용하나요?",
         "아닙니다. 건식 관리라 오일 없이 편한 옷차림 그대로 받을 수 있고, 받은 뒤 샤워가 필수가 아닙니다."),
        ("어떤 공간이 필요한가요?",
         "바닥에 누울 수 있는 공간이면 충분합니다. 이불이나 요를 한 겹 깔면 더 편안합니다."),
        ("타이마사지 테마 페이지와 무엇이 다른가요?",
         "테마 페이지는 관리 방식의 특징을, 이 페이지는 금천구에서 홈타이를 예약하는 방법과 흐름을 안내합니다."),
        ("스웨디시와 고민 중인데 어떻게 고르나요?",
         "굳은 몸을 펴고 싶으면 홈타이, 부드럽게 이완되어 자고 싶으면 스웨디시입니다. 자세한 비교는 매거진의 홈타이 vs 스웨디시 글에서 다룹니다."),
        ("관리사가 여성인가요?",
         "배정 기준과 요청 사항은 예약 상담에서 확인해 드립니다. 원하시는 사항을 편하게 말씀해 주세요."),
        ("홈타이도 심야에 받을 수 있나요?",
         "네. 오히려 밤 10시 이후가 홈타이의 피크 시간대입니다. 심야 도착 변수는 예약 시 함께 안내드립니다."),
        ("이불이 없으면 못 받나요?",
         "수건과 휴대 매트로 대체 가능합니다. 예약 시 환경만 알려주세요."),
    ]
    sections = [
        ("금천 홈타이란", [
            "홈타이는 타이마사지를 고객이 계신 자택·숙소로 방문해 진행하는 방식입니다.",
            "지압과 스트레칭이 결합된 건식 관리로, 굳은 몸의 가동 범위를 넓히고 개운함을 끌어내는 데 초점을 둡니다.",
            "금천구에서는 가산동 오피스텔의 야근 후 이용, 독산·시흥 주거지의 저녁 이용 문의가 고르게 들어옵니다."]),
        ("이용 흐름", [
            "전화로 위치·희망 시간·코스(60·90·120분)를 알려주시면 방문 가능 시간을 확정해 드립니다.",
            "관리사가 매트 등 필요한 용품을 준비해 방문하며, 트레이닝복 등 편한 복장이면 바로 시작할 수 있습니다.",
            "발끝에서 시작해 다리·허리·등·어깨 순으로 지압과 스트레칭을 번갈아 진행합니다."]),
        ("이런 분께 잘 맞습니다", [
            ("ul", ["몸이 굳어 있는데 스트레칭을 따로 챙기지 못하는 분",
                    "오일 사용 없이 깔끔하게 받고 싶은 분",
                    "샤워 부담 없이 받은 뒤 바로 쉬고 싶은 분"])]),
        ("금천 동별 홈타이 이용 모습", [
            ("h3", "가산동 — 야근 후 오피스텔"),
            "밤 10시 이후 시작 예약이 집중되는 권역입니다. 샤워 없이 받고 그대로 자는 건식의 장점이 야근 패턴과 정확히 맞물립니다.",
            ("h3", "독산동 — 저녁 자택"),
            "퇴근 후 저녁 식사를 마치고 받는 8~10시대 예약이 많습니다. 가족 공간에서도 옷을 입고 받는 방식이라 부담이 적습니다.",
            ("h3", "시흥동 — 주말 낮"),
            "주말 등산·활동 후 굳은 몸을 펴는 낮 시간 예약이 꾸준합니다. 동별 도착 시간은 <a href='/geumcheon-gu/area/'>지역별 안내</a>에서 확인하세요."]),
        ("자주 선택되는 시간 구성", [
            "60분은 하체·허리 중심의 압축 구성으로, 늦은 밤 빠르게 풀고 자려는 분께 맞습니다.",
            "90분은 발끝부터 어깨까지 전신을 펴는 표준 구성으로 첫 이용이라면 이쪽을 권합니다. 120분은 전신에 등·어깨 반복 정리를 더한 구성입니다.",
            "받는 중 압이 강하면 즉시 조절되며, 스트레칭 동작은 가동 범위를 확인하며 단계적으로 진행하니 몸이 굳은 분도 걱정할 것 없습니다."]),
        ("코스·요금과 상세 안내", [
            "홈타이의 시간 구성과 요금 기준은 코스 전용 페이지에서 확인하실 수 있습니다.",
            ("ul", ['<a href="/course/home-thai/">홈타이 코스 상세</a>',
                    '<a href="/themes/thai-massage/">타이마사지 테마 안내</a>',
                    '<a href="/course/price/">가격 안내</a>',
                    '<a href="/geumcheon-gu/checklist/">이용 전 확인사항</a>'])]),
    ]
    content_page("/geumcheon-gu/home-thai/", "geumcheon", trail,
        title="금천 홈타이 안내 | 금천구 방문 타이마사지 예약",
        desc="금천 홈타이 안내 - 자택·숙소에서 받는 건식 타이마사지 방문 서비스입니다. 동별 이용 패턴, 이용 흐름, 추천 대상, 코스·요금 링크를 안내합니다.",
        eyebrow="금천구 · 홈타이", h1="금천 홈타이 안내",
        lead="타이마사지를 금천구 자택·숙소에서 그대로 받는 홈타이 예약 안내입니다. "
             "가산·독산·시흥 동별 이용 패턴과 시간 구성, 준비 사항까지 한 페이지에 정리했습니다.",
        sections=sections, faq=ht_faq,
        data_note="금천 홈타이 예약의 절반 이상이 밤 10시 이후 시작입니다. 샤워 없이 받고 그대로 잠드는 건식의 장점이 야근 생활권과 맞물린 결과로, 90분 전신 구성이 표준입니다.",
        top_links=[("tel:" + PHONE_TEL, "예약문의", True),
                   ("/course/home-thai/", "홈타이 코스"), ("/themes/thai-massage/", "타이마사지 테마")],
        service=("금천 홈타이", "금천구 방문 타이마사지(홈타이) 안내"),
        cta_title="금천 홈타이 예약, 지금 도와드릴까요?")


# ---- 금천구 전지역 방문 가능 안내 -------------------------------------------
def build_coverage():
    trail = [("/", "홈"), ("/geumcheon-gu/", "금천 출장마사지"), (None, "전지역 방문 가능 안내")]
    cv_faq = [
        ("독산3동인데 어느 페이지를 보면 되나요?",
         "독산1동부터 독산4동까지 모두 독산동 페이지에서 통합 안내합니다. 예약 시에는 정확한 주소 기준으로 확인해 드립니다."),
        ("금천구 경계 바로 밖도 방문되나요?",
         "구로·관악 등 인접 지역은 위치에 따라 가능할 수 있습니다. 예약 시 주소를 기준으로 확인해 드립니다."),
        ("어느 동이 도착이 가장 빠른가요?",
         "배정 상황에 따라 다르지만 평균적으로 가산동 25분, 독산동 27분, 시흥동 30분 내외입니다."),
        ("법정동과 행정동이 헷갈려요.",
         "헷갈리셔도 됩니다. 어떤 행정동이든 가산동·독산동·시흥동 세 페이지 중 하나에 속하고, 실제 예약은 주소만으로 진행되기 때문입니다."),
        ("주소를 모르는 위치(상가·사무실)는요?",
         "건물명이나 가까운 역·큰 교차로를 알려주시면 일차 확인이 가능합니다. 정확한 주소는 방문 확정 전까지만 알려주시면 됩니다."),
        ("이사 와서 동을 잘 몰라요.",
         "가까운 지하철역만 알아도 충분합니다. 가산디지털단지역·독산역·금천구청역 기준의 역세권 페이지에서 시작해 보세요."),
        ("페이지가 3개뿐인 이유가 있나요?",
         "같은 내용을 동 이름만 바꿔 늘리는 대신, 대표 동 3곳에 생활권 정보를 충실히 담는 방식이 이용자에게도 검색에도 정확하기 때문입니다."),
    ]
    dong_lines = [
        f'<a href="/geumcheon-gu/{d["slug"]}/">{d["name"]}</a> — {d["character"]}. '
        f"평균 {d['arrival']}분 내외 도착." for d in DONGS]
    sections = [
        ("금천구 행정동과 대표 동", [
            "금천구의 법정동은 가산동·독산동·시흥동 3개이고, 행정동은 가산동, 독산1~4동, 시흥1~5동으로 구분됩니다.",
            "저희는 검색·안내 구조를 법정동(대표 동) 기준으로 통합해, 독산1동~독산4동은 독산동 페이지 1개로, "
            "시흥1동~시흥5동은 시흥동 페이지 1개로 안내합니다.",
            "숫자 행정동마다 페이지를 만들면 내용이 중복된 저품질 페이지가 양산되기 때문에, 대표 동 페이지에 생활권 정보를 모아 정확도를 높였습니다."]),
        ("대표 동 3곳 안내", dong_lines),
        ("역세권 기준 안내", [
            "지하철로 위치를 설명하시는 분들을 위해 가산디지털단지역·독산역·금천구청역 3개 역세권 페이지도 운영합니다.",
            "환승역인 가산디지털단지역은 1호선·7호선 어느 노선으로 오셔도 같은 페이지에서 안내합니다.",
            ("ul", ['<a href="/geumcheon-gu/stations/">지하철역별 안내 전체 보기</a>'])]),
        ("이용 흐름 예시", [
            ("h3", "예시 1 — \"독산3동인데 가능해요?\""),
            "독산1~4동은 모두 독산동 페이지 기준으로 안내되며, 예약은 행정동 구분 없이 정확한 주소로 확인합니다. 평균 27분 내외 도착권입니다.",
            ("h3", "예시 2 — \"시흥사거리 근처 빌라예요\""),
            "시흥동 생활권 중심부로, 기준점(사거리·건물명)만으로도 일차 확인이 됩니다. 정확한 주소를 주시면 도착 시간이 확정됩니다.",
            ("h3", "예시 3 — \"가산디지털단지역에서 7호선 타고 왔어요\""),
            "노선과 무관하게 가산디지털단지역 페이지 하나에서 안내하며, 역 기준 방향(지식산업센터/아울렛/오피스텔)을 말씀해 주시면 더 정확합니다."]),
        ("방문 가능 여부 확인 방법", [
            "같은 동 안에서도 정확한 위치·예약 시간·배정 상황에 따라 가능 여부와 도착 시간이 달라집니다.",
            "예약 시 정확한 주소(또는 가까운 역·건물)를 알려주시면 방문 가능 여부와 예상 도착 시간을 바로 확인해 드립니다.",
            "구로·관악 등 금천 경계와 맞닿은 인접 지역은 위치에 따라 가능할 수 있으며, 변동 요소가 있다면 상담에서 먼저 고지합니다."]),
    ]
    content_page("/geumcheon-gu/coverage/", "geumcheon", trail,
        title="금천구 전지역 방문 가능 안내 | 대표 동 통합 기준",
        desc="금천구 전지역 방문 가능 안내 - 가산동·독산동·시흥동 대표 동 통합 기준과 역세권 안내, 방문 가능 여부 확인 방법을 설명합니다.",
        eyebrow="금천구 · 전지역", h1="금천구 전지역 방문 가능 안내",
        lead="금천구 어디서든 — 대표 동 3개와 역세권 3곳 기준으로 방문 가능 지역을 안내합니다.",
        sections=sections, faq=cv_faq,
        top_links=[("tel:" + PHONE_TEL, "예약문의", True), ("/geumcheon-gu/area/", "지역별 안내"),
                   ("/geumcheon-gu/stations/", "지하철역별 안내")])


# ---- 지역 허브 ---------------------------------------------------------------
def build_area_hub():
    trail = [("/", "홈"), ("/geumcheon-gu/", "금천 출장마사지"), (None, "지역별 안내")]
    cards = "".join(
        f'<a class="card reveal" href="/geumcheon-gu/{d["slug"]}/"><div class="k">GEUMCHEON</div>'
        f'<h3>{d["name"]}</h3><p>{d["character"]}. {d["landmarks"]}.</p>'
        f'<span class="more">동 안내 보기 →</span></a>' for d in DONGS)
    hub_faq = [
        ("지역 페이지에는 어떤 내용이 있나요?",
         "각 동의 생활권 특징, 방문 포인트별 평균 도착 시간, 인근 역세권, 관련 테마·코스 링크를 고유하게 안내합니다."),
        ("우리 동네가 목록에 없어요.",
         "금천구의 모든 행정동은 가산동·독산동·시흥동 3개 대표 동 페이지에 포함되어 있습니다. 독산1~4동은 독산동, 시흥1~5동은 시흥동에서 확인하세요."),
        ("역 기준으로도 찾을 수 있나요?",
         "네. 가산디지털단지역·독산역·금천구청역 기준의 지하철역별 안내 페이지를 함께 운영합니다."),
        ("동 경계가 애매한 위치는 어떻게 하나요?",
         "동 경계 근처라면 어느 페이지를 보셔도 무방합니다. 실제 방문 가능 여부는 페이지 구분이 아니라 정확한 주소를 기준으로 확인해 드립니다."),
        ("세 동의 도착 시간이 왜 다른가요?",
         "배정 동선과 생활권 구조가 다르기 때문입니다. 평균적으로 가산동 25분, 독산동 27분, 시흥동 30분 내외이며 시간대에 따라 달라질 수 있습니다."),
    ]
    dong_intro = (
        '<h3 style="font-size:20px;font-weight:800;margin:42px 0 10px"><span class="grad">세 생활권은 이렇게 다릅니다</span></h3>'
        '<p class="sec-lead" style="max-width:820px">가산동은 1·7호선 환승역인 가산디지털단지역과 지식산업센터가 모인 업무 권역이라 '
        '야근 후 오피스텔 방문과 숙소 방문 문의가 많습니다. 독산동은 1호선 독산역을 끼고 대단지 아파트와 전통 생활권이 함께 있어 '
        '저녁 시간대 자택 방문 비중이 높습니다. 시흥동은 금천구청역과 시흥사거리를 중심으로 금천 남부를 아우르는 주거 생활권이라 '
        '주말 가족 단위 문의가 꾸준합니다.</p>'
        '<p class="sec-lead" style="max-width:820px;margin-top:12px">이런 생활권 차이 때문에 같은 코스라도 동마다 문의가 몰리는 시간대와 '
        '방문 포인트가 다릅니다. 각 동 페이지에서는 방문 포인트별 평균 도착 시간을 예약 데이터 기준으로 안내하므로, '
        '내 위치와 가까운 포인트를 확인한 뒤 문의하시면 상담이 빨라집니다.</p>'
        '<h3 style="font-size:20px;font-weight:800;margin:42px 0 10px"><span class="grad">지역 페이지 활용 방법</span></h3>'
        '<p class="sec-lead" style="max-width:820px">먼저 내가 있는 동(또는 가까운 동) 페이지에서 방문 가능 생활권과 평균 도착 시간을 확인하세요. '
        '그다음 원하는 관리 유형이 있다면 테마별 안내에서 특징을, 시간과 요금은 코스안내에서 확인하면 예약 전 필요한 정보가 모두 갖춰집니다.</p>'
        '<p class="sec-lead" style="max-width:820px;margin-top:12px">전화 예약 시에는 동 이름과 함께 가까운 역이나 큰 건물을 알려주시면 좋습니다. '
        '예를 들어 “독산동 ○○아파트”나 “시흥사거리 근처”처럼 기준점을 말씀해 주시면 방문 가능 여부와 도착 시간을 바로 확인해 드립니다. '
        '심야나 주말처럼 문의가 몰리는 시간대라면 한두 시간 여유를 두고 미리 연락 주시는 편이 일정 조율에 유리합니다.</p>')
    body = (breadcrumb(trail) +
        '<section class="block" style="padding-bottom:40px"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>AREA GUIDE</span>'
        '<h2 class="sec">금천구 전체 — 지역별 안내</h2>'
        '<p class="sec-lead" style="max-width:820px">금천구 방문 안내는 대표 동 3개 기준으로 운영합니다. '
        '각 동 페이지에서 생활권 특징과 방문 포인트, 평균 도착 시간을 고유하게 확인하실 수 있습니다.</p>'
        f'<div class="grid g3" style="margin-top:28px">{cards}</div>'
        + dong_intro +
        '<div class="data-box" style="max-width:820px;margin-top:30px"><b>통합 기준</b>'
        '<p>가산동은 가산동 페이지 1개로, 독산1동~독산4동은 독산동 페이지 1개로, 시흥1동~시흥5동은 시흥동 페이지 1개로 통합 안내합니다. '
        '숫자 행정동 개별 페이지는 만들지 않습니다. 이는 같은 내용을 동 이름만 바꿔 반복하는 중복 페이지를 막고, '
        '한 페이지에 생활권 정보를 충실히 담기 위한 기준입니다. 금천구 공식 구분 기준으로 법정동은 가산동·독산동·시흥동 3개이며, '
        '행정동은 가산동과 독산1~4동, 시흥1~5동으로 나뉩니다.</p></div>'
        '<p class="sec-lead" style="max-width:820px;margin-top:26px">역 기준으로 찾으신다면 '
        '<a href="/geumcheon-gu/stations/" style="color:var(--gold);font-weight:700">지하철역별 안내</a>에서 '
        '가산디지털단지역·독산역·금천구청역 페이지를 확인하세요. 예약 가능 시간과 준비 사항은 '
        '<a href="/geumcheon-gu/hours/" style="color:var(--gold);font-weight:700">예약 가능 시간</a>, '
        '<a href="/geumcheon-gu/checklist/" style="color:var(--gold);font-weight:700">이용 전 확인사항</a>에서 공통으로 안내합니다.</p>'
        '</div></section>' + faq_block(hub_faq) + cta_band())
    coll = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "금천구 지역별 안내", "url": BASE_URL + "/geumcheon-gu/area/",
        "hasPart": [{"@type": "WebPage", "name": d["name"],
                     "url": BASE_URL + f"/geumcheon-gu/{d['slug']}/"} for d in DONGS],
    }
    html = page("/geumcheon-gu/area/", "금천구 지역별 안내 | 가산동·독산동·시흥동 방문 안내",
        "금천구 지역별 안내 - 대표 동 3개(가산동, 독산동, 시흥동) 기준의 방문 안내 허브입니다. 숫자 행정동은 대표 동 페이지에서 통합 안내합니다.",
        "area", body, [bc_ld(trail), coll, faq_ld(hub_faq)])
    write("/geumcheon-gu/area/", html)


# ---- 동 페이지 (3) -----------------------------------------------------------
# 동별 개별화된 SEO title/description (템플릿 복제 회피)
DONG_SEO = {
    "gasan-dong": (
        "가산동 출장마사지 | 가산디지털단지 오피스텔 방문 관리 안내",
        "가산동 출장마사지 안내 - 가산디지털단지역(1·7호선)과 G밸리 지식산업센터, 오피스텔 생활권 기준의 방문 안내입니다. 야근 후 이용 패턴과 평균 도착 25분 기준을 확인하세요."),
    "doksan-dong": (
        "독산동 출장마사지 | 독산역 아파트 생활권 방문 관리 안내",
        "독산동 출장마사지 안내 - 독산1동~독산4동을 통합 안내하는 대표 페이지입니다. 독산역 대단지 아파트와 전통 생활권의 방문 포인트, 평균 도착 27분 기준을 확인하세요."),
    "siheung-dong": (
        "시흥동 출장마사지 | 금천 남부 주거 생활권 방문 관리 안내",
        "시흥동 출장마사지 안내 - 시흥1동~시흥5동을 통합 안내하는 대표 페이지입니다. 금천구청역·시흥사거리·호암산 자락 생활권의 방문 포인트와 평균 도착 30분 기준을 확인하세요."),
}


def build_dong_pages():
    for d in DONGS:
        name, slug = d["name"], d["slug"]
        path = f"/geumcheon-gu/{slug}/"
        trail = [("/", "홈"), ("/geumcheon-gu/", "금천 출장마사지"),
                 ("/geumcheon-gu/area/", "지역별 안내"), (None, name)]
        siblings = [x for x in DONGS if x["slug"] != slug]
        zones = DONG_ZONES[slug]
        my_stations = [STATION_BY_SLUG[s] for s in d["station_slugs"]]
        st_names = "·".join(s["name"] for s in my_stations)

        zone_blocks = [
            f"{name}은 {d['landmarks']}를 중심으로 생활권이 이어집니다. {d['character']}이라 "
            f"방문 문의 패턴도 이 특성을 따라가며, 세부 가능 여부는 정확한 위치·예약 시간·배정 상황에 따라 달라질 수 있습니다."]
        zone_arr = ", ".join(
            f"{zt.replace(' 인근', '').replace(' 일대', '')} 약 {d['arrival'] + i * 2}분"
            for i, (zt, _) in enumerate(zones))
        zone_blocks.append(
            f"방문 포인트별 평균 도착 시간(예약 데이터 기준)은 {zone_arr} 내외입니다. "
            f"같은 {name} 안에서도 위치에 따라 도착 시간이 달라집니다.")
        for zt, zd in zones:
            zone_blocks += [("h3", zt), zd]

        related = [f'<a href="/geumcheon-gu/stations/{s["slug"]}/">{s["name"]} 안내</a>' for s in my_stations]
        related += [f'<a href="/geumcheon-gu/{s["slug"]}/">{s["name"]} 안내</a>' for s in siblings]
        related += ['<a href="/geumcheon-gu/area/">금천구 전체 지역 안내</a>']

        sections = [
            (f"{name} 이용 안내", [
                f"{name}은 {d['character']}입니다. 주요 위치는 {d['landmarks']} 일대로, 이 생활권을 중심으로 방문 문의가 들어옵니다.",
                f"예약 시 위치·희망 시간·코스·인원을 확인한 뒤 방문 가능 여부를 안내드리며, 평균 {d['arrival']}분 내외로 도착합니다.",
                '예약 방법과 결제 절차는 <a href="/reservation/">예약안내</a>, 처음 이용 시 흐름은 <a href="/guide/">이용가이드</a>에서 확인하실 수 있습니다.']),
            (f"{name} 방문 가능 생활권", zone_blocks),
            ("함께 보기", [
                f"{name}과 연결되는 역세권·인근 동 안내입니다.",
                ("ul", related)]
                + ([d["sub_note"]] if d.get("sub_note") else [])),
            (f"{name}에서 많이 찾는 관리", [
                f"{name}({d['character']})에서는 생활 패턴에 맞는 테마·코스 문의가 많습니다. 상세 설명은 전용 페이지에서 확인하세요.",
                ("ul", ['<a href="/themes/">테마별 안내</a>', '<a href="/course/">전체 코스</a>',
                        '<a href="/course/fatigue/">피로 회복 관리</a>', '<a href="/course/home-thai/">홈타이 코스</a>',
                        '<a href="/course/price/">가격 안내</a>']),
                f"{name} 생활 패턴과 이어지는 읽을거리도 매거진에 정리되어 있습니다.",
                ("ul", [f'<a href="/magazine/{ps}/">매거진 · {POST_BY_SLUG[ps]["h1"].split(" — ")[0]}</a>'
                        for ps in DONG_POSTS.get(slug, [])])]),
            ("예약·준비·위생 안내", [
                "예약 가능 시간, 방문 전 준비물, 위생·안전 기준은 페이지마다 반복하지 않고 전용 안내에서 확인하실 수 있습니다.",
                ("ul", ['<a href="/geumcheon-gu/hours/">예약 가능 시간</a>',
                        '<a href="/geumcheon-gu/checklist/">이용 전 확인사항</a>',
                        '<a href="/geumcheon-gu/safety/">위생 및 안전 안내</a>'])]),
        ]
        dong_faq = [
            (f"{name} 전 지역 방문이 가능한가요?",
             f"예약 시간, 정확한 위치, 배정 상황에 따라 가능 여부가 달라질 수 있습니다. {st_names} 인근 등 세부 위치 기준으로 안내드립니다."),
            (f"{st_names} 근처도 예약할 수 있나요?",
             f"{st_names} 인근은 {name}의 핵심 생활권으로, 역 상세 페이지에서 주변 생활권과 함께 안내합니다."),
            (f"{name}은 어떤 지역인가요?",
             f"{name}은 {d['character']}입니다. {d['landmarks']} 인근을 중심으로 방문 문의가 많습니다."),
            (f"{name} 도착까지 얼마나 걸리나요?",
             f"평균 {d['arrival']}분 내외이며, 시간대와 정확한 위치에 따라 달라질 수 있습니다."),
        ]
        if d.get("sub_note"):
            num_q = "독산1동~독산4동도 같은 페이지인가요?" if slug == "doksan-dong" else "시흥1동~시흥5동도 같은 페이지인가요?"
            dong_faq.append((num_q, d["sub_note"] + " 예약 시에는 정확한 주소 기준으로 확인해 드립니다."))
        else:
            dong_faq.append((f"{name}은 야근 후 늦은 시간에도 가능한가요?",
                             "상담은 24시간 가능합니다. 심야 시간대는 도착 시간이 다소 길어질 수 있어 미리 예약을 권장드립니다."))
        lead = (f"금천구 {name}({d['character']})에서 방문 마사지 예약을 찾는 분들을 위한 안내입니다. "
                f"{name}은 {st_names} 인근 생활권과 가까워 평균 {d['arrival']}분 내외로 도착합니다.")
        seo_title, seo_desc = DONG_SEO[slug]
        content_page(path, "area", trail,
            title=seo_title, desc=seo_desc,
            eyebrow=f"금천구 {name}", h1=f"{name} 출장마사지 예약 안내", lead=lead,
            sections=sections, faq=dong_faq,
            data_note=f"{name} 일대는 평균 {d['arrival']}분 내외로 도착합니다(예약 데이터 기준). "
                      "저녁·주말은 문의가 몰려 도착이 다소 길어질 수 있어 사전 예약을 권장드립니다.",
            service=(f"{name} 출장마사지", f"금천구 {name} 일대 방문 건강관리 서비스"),
            top_links=[("tel:" + PHONE_TEL, "예약문의", True), ("/course/", "코스안내"),
                       ("/geumcheon-gu/", "금천 출장마사지")],
            cta_title=f"{name} 방문 예약, 지금 도와드릴까요?",
            extra_schema=[localbiz_ld(name=f"{BRAND_SHORT} {name} 방문 관리",
                                      area=f"서울특별시 금천구 {name}", path=path)])


# ---- 지하철역 허브 -------------------------------------------------------------
def build_stations_hub():
    trail = [("/", "홈"), ("/geumcheon-gu/", "금천 출장마사지"), (None, "지하철역별 안내")]
    line1_cards = "".join(
        f'<a class="card reveal" href="/geumcheon-gu/stations/{s["slug"]}/"><div class="k">{s["lines"]}</div>'
        f'<h3>{s["name"]}</h3><p>{s["character"]}입니다.</p><span class="more">역 안내 보기 →</span></a>'
        for s in STATIONS)
    g = STATION_BY_SLUG["gasan-digital-complex-station"]
    line7_card = (
        f'<a class="card reveal" href="/geumcheon-gu/stations/{g["slug"]}/"><div class="k">{g["lines"]}</div>'
        f'<h3>{g["name"]}</h3><p>7호선에서도 같은 역 페이지에서 안내합니다. 환승역도 URL은 하나만 사용합니다.</p>'
        f'<span class="more">역 안내 보기 →</span></a>')
    st_faq = [
        ("환승역은 노선마다 페이지가 다른가요?",
         "아닙니다. 가산디지털단지역은 1호선·7호선 어느 쪽이든 같은 페이지 하나에서 안내합니다."),
        ("출구 번호별 안내도 있나요?",
         "출구별 페이지는 만들지 않습니다. 역 페이지 본문에서 생활권 단위로 안내하고, 정확한 위치는 예약 시 확인해 드립니다."),
        ("역 근처 숙소에서도 받을 수 있나요?",
         "네. 각 역 페이지에서 인근 오피스텔·숙소 생활권을 함께 안내합니다."),
        ("역과 동 페이지 중 무엇을 보면 되나요?",
         "지하철로 위치를 설명하기 편하면 역 페이지를, 동네 기준이 편하면 동 페이지를 보시면 됩니다. 두 페이지는 서로 연결되어 있어 어느 쪽에서 시작해도 같은 안내로 이어집니다."),
        ("막차 이후 시간에도 가능한가요?",
         "상담은 24시간 가능합니다. 심야에는 위치에 따라 도착 시간이 길어질 수 있어 여유 있는 예약을 권장드립니다."),
    ]
    st_guide = (
        '<h3 style="font-size:20px;font-weight:800;margin:42px 0 10px"><span class="grad">역세권별 이용 패턴</span></h3>'
        '<p class="sec-lead" style="max-width:820px">가산디지털단지역은 지식산업센터 퇴근 인구와 아울렛·숙소 방문객이 겹치는 곳이라 '
        '평일 밤과 주말 모두 문의가 많은 역세권입니다. 독산역은 대단지 아파트 중심의 주거 역세권으로 저녁 시간 자택 방문 예약이 많고, '
        '금천구청역은 관공서와 시흥동 생활권이 만나는 곳이라 평일 저녁과 주말 문의가 고르게 들어옵니다.</p>'
        '<p class="sec-lead" style="max-width:820px;margin-top:12px">예약 시에는 역 이름과 함께 방향(생활권)을 알려주시면 좋습니다. '
        '예를 들어 같은 가산디지털단지역이라도 지식산업센터 쪽과 아울렛 쪽은 동선이 달라, 방향을 알면 도착 시간을 더 정확히 안내할 수 있습니다. '
        '정확한 주소를 알려주시면 가장 빠르고, 역·건물 기준만으로도 일차 확인이 가능합니다.</p>'
        '<h3 style="font-size:20px;font-weight:800;margin:42px 0 10px"><span class="grad">예약 전 체크 포인트</span></h3>'
        '<p class="sec-lead" style="max-width:820px">역세권 예약에서 가장 자주 나오는 질문은 “출구 몇 번 쪽인데 가능한가요?”입니다. '
        '안내는 출구 번호가 아니라 생활권 단위로 하므로, 출구보다는 건물 이름이나 주소를 알려주시는 편이 정확합니다. '
        '숙소(호텔·레지던스)라면 건물명과 객실 번호, 프런트 출입 안내가 필요한지도 함께 알려주세요.</p>'
        '<p class="sec-lead" style="max-width:820px;margin-top:12px">평균 도착 시간은 역 기준 24~31분 내외이며, 밤 21~24시처럼 예약이 '
        '몰리는 시간대에는 다소 길어질 수 있습니다. 시간대별 특징과 도착 시간을 줄이는 방법은 예약 가능 시간 페이지에서, '
        '방문 전 준비 사항은 이용 전 확인사항 페이지에서 자세히 안내합니다.</p>')
    body = (breadcrumb(trail) +
        '<section class="block" style="padding-bottom:30px"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>STATION GUIDE</span>'
        '<h2 class="sec">금천 지하철역 전체</h2>'
        '<p class="sec-lead" style="max-width:820px">금천구 주요 역세권을 기준으로 방문 안내를 제공합니다. '
        '각 역 페이지에서는 인근 생활권, 주변 대표 동, 평균 도착 시간을 고유하게 설명합니다. '
        '출구별 페이지나 역과 테마를 조합한 페이지는 만들지 않습니다.</p>'
        '<h3 id="line1" style="font-size:21px;font-weight:800;margin:42px 0 6px"><span class="grad">1호선 금천권</span></h3>'
        '<p class="sec-lead">금천구를 남북으로 잇는 1호선의 3개 역입니다.</p>'
        f'<div class="grid g3" style="margin-top:18px">{line1_cards}</div>'
        '<h3 id="line7" style="font-size:21px;font-weight:800;margin:42px 0 6px"><span class="grad">7호선 금천권</span></h3>'
        '<p class="sec-lead">7호선이 지나는 금천구 역은 가산디지털단지역 하나입니다. 광명·철산 방면이나 강남권에서 7호선으로 이동하실 때도 '
        '같은 페이지를 보시면 됩니다.</p>'
        f'<div class="grid g3" style="margin-top:18px">{line7_card}</div>'
        + st_guide +
        '<div class="data-box" style="max-width:820px;margin-top:34px"><b>운영 기준</b>'
        '<p>환승역은 여러 노선에 노출되더라도 URL은 하나만 사용합니다. 역세권 안내는 가산디지털단지역·독산역·금천구청역 3곳으로 한정하며, '
        '역 인근의 동 단위 상세는 가산동·독산동·시흥동 지역 페이지에서 이어집니다. '
        '출구별 페이지나 역 이름에 테마를 붙인 페이지는 만들지 않고, 실제 방문 가능 여부는 항상 정확한 위치를 기준으로 확인해 드립니다.</p></div>'
        '</div></section>' + faq_block(st_faq) + cta_band())
    coll = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "금천 지하철역별 안내", "url": BASE_URL + "/geumcheon-gu/stations/",
        "hasPart": [{"@type": "WebPage", "name": s["name"],
                     "url": BASE_URL + f"/geumcheon-gu/stations/{s['slug']}/"} for s in STATIONS],
    }
    html = page("/geumcheon-gu/stations/", "금천 지하철역별 안내 | 가산디지털단지역·독산역·금천구청역",
        "금천 지하철역별 안내 - 1호선 가산디지털단지역, 독산역, 금천구청역과 7호선 가산디지털단지역 역세권 기준의 방문 안내 허브입니다.",
        "stations", body, [bc_ld(trail), coll, faq_ld(st_faq)])
    write("/geumcheon-gu/stations/", html)


# ---- 역 페이지 (3) ------------------------------------------------------------
def build_station_pages():
    for s in STATIONS:
        name, slug = s["name"], s["slug"]
        path = f"/geumcheon-gu/stations/{slug}/"
        dong = DONG_BY_SLUG[s["dong_slug"]]
        trail = [("/", "홈"), ("/geumcheon-gu/", "금천 출장마사지"),
                 ("/geumcheon-gu/stations/", "지하철역별 안내"), (None, name)]
        zones = STATION_ZONES[slug]
        others = [x for x in STATIONS if x["slug"] != slug]

        zone_blocks = [
            f"{name}은 {s['character']}입니다. 역을 중심으로 한 생활권별 방문 안내는 아래와 같으며, "
            "출구 번호 단위가 아닌 생활권 단위로 안내합니다."]
        zone_arr = ", ".join(
            f"{zt.replace(' 인근', '').replace(' 일대', '').replace(' 방면', '')} 약 {s['arrival'] + i * 2}분"
            for i, (zt, _) in enumerate(zones))
        zone_blocks.append(f"생활권별 평균 도착 시간(예약 데이터 기준)은 {zone_arr} 내외입니다.")
        for zt, zd in zones:
            zone_blocks += [("h3", zt), zd]

        sections = [
            (f"{name} 인근 이용 안내", [
                f"{name}({s['lines']})은 금천구 {dong['name']}에 있습니다. {s['character']}으로, "
                f"역 인근 자택·오피스텔·숙소 방문 문의가 꾸준히 들어옵니다.",
                f"예약 시 역 기준 방향(생활권)과 정확한 위치를 알려주시면 방문 가능 여부와 도착 시간을 빠르게 확인해 드립니다. "
                f"평균 도착 시간은 {s['arrival']}분 내외입니다."]),
            (f"{name} 방문 가능 생활권", zone_blocks),
            STATION_TIPS[slug],
            ("주변 대표 동 함께 보기", [
                f"{name} 일대의 동 단위 상세 안내는 {dong['name']} 페이지에서 이어집니다.",
                ("ul", [f'<a href="/geumcheon-gu/{dong["slug"]}/">{dong["name"]} 안내</a>',
                        '<a href="/geumcheon-gu/stations/">금천 지하철역 전체</a>']
                       + [f'<a href="/geumcheon-gu/stations/{o["slug"]}/">{o["name"]} 안내</a>' for o in others])]),
            ("관련 테마·코스", [
                "역세권에서 많이 찾는 관리 유형은 테마·코스 전용 페이지에서 확인하세요. 역과 테마를 조합한 별도 페이지는 운영하지 않습니다.",
                ("ul", ['<a href="/themes/">테마별 안내</a>', '<a href="/course/">전체 코스</a>',
                        '<a href="/course/price/">가격 안내</a>']),
                f"{name} 생활권과 이어지는 매거진 글도 함께 읽어보세요.",
                ("ul", [f'<a href="/magazine/{ps}/">매거진 · {POST_BY_SLUG[ps]["h1"].split(" — ")[0]}</a>'
                        for ps in STATION_POSTS.get(slug, [])])]),
            ("예약·준비·위생 안내", [
                "예약 가능 시간, 방문 전 준비물, 위생·안전 기준은 전용 안내에서 확인하실 수 있습니다.",
                ("ul", ['<a href="/geumcheon-gu/hours/">예약 가능 시간</a>',
                        '<a href="/geumcheon-gu/checklist/">이용 전 확인사항</a>',
                        '<a href="/geumcheon-gu/safety/">위생 및 안전 안내</a>'])]),
        ]
        st_faq = [
            (f"{name} 몇 번 출구 쪽도 가능한가요?",
             "출구 번호와 무관하게 역 인근 생활권 전체를 안내합니다. 정확한 주소를 알려주시면 가능 여부를 바로 확인해 드립니다."),
            (f"{name}에서 도착까지 얼마나 걸리나요?",
             f"평균 {s['arrival']}분 내외이며, 시간대·정확한 위치·배정 상황에 따라 달라질 수 있습니다."),
            (f"{name} 근처 숙소·오피스텔에서도 받을 수 있나요?",
             "네. 건물명과 출입 방법을 알려주시면 방문 가능 여부를 확인해 드립니다."),
            (f"{name}은 어느 동에 있나요?",
             f"금천구 {dong['name']}에 있으며, 동 단위 상세 안내는 {dong['name']} 페이지에서 확인하실 수 있습니다."),
        ]
        if slug == "gasan-digital-complex-station":
            st_faq.append(("1호선과 7호선 안내가 다른가요?",
                           "아닙니다. 가산디지털단지역은 환승역이지만 안내 페이지는 이 페이지 하나입니다."))
        lead = (f"{name}({s['lines']}) 인근에서 방문 마사지·홈타이 예약을 찾는 분들을 위한 안내입니다. "
                f"{s['character']}으로, 평균 {s['arrival']}분 내외로 도착합니다.")
        content_page(path, "stations", trail,
            title=f"{name} 출장마사지·홈타이 | 금천구 {dong['name']} 방문 마사지 안내",
            desc=STATION_SEO_DESC[slug],
            eyebrow=f"금천구 · {s['lines']}", h1=f"{name} 출장마사지·홈타이 예약 안내", lead=lead,
            sections=sections, faq=st_faq,
            data_note=f"{name} 인근은 평균 {s['arrival']}분 내외로 도착합니다(예약 데이터 기준). "
                      "심야·주말은 여유 있는 예약을 권장드립니다.",
            service=(f"{name} 인근 방문 관리", f"금천구 {dong['name']} {name} 역세권 방문 건강관리 서비스"),
            top_links=[("tel:" + PHONE_TEL, "예약문의", True),
                       (f"/geumcheon-gu/{dong['slug']}/", f"{dong['name']} 안내"),
                       ("/geumcheon-gu/stations/", "지하철역 전체")],
            cta_title=f"{name} 인근 방문 예약, 지금 도와드릴까요?")


# ---- 테마 허브 + 테마 페이지 ---------------------------------------------------
def build_themes_hub():
    trail = [("/", "홈"), (None, "테마별 안내")]
    cards = "".join(
        f'<a class="card reveal" href="/themes/{t["slug"]}/"><div class="k">{t["kicker"]}</div>'
        f'<h3>{t["name"]}</h3><p>{t["short"]}</p><span class="more">테마 보기 →</span></a>'
        for t in THEMES)
    th_faq = [
        ("테마와 코스는 무엇이 다른가요?",
         "테마는 관리 방식(스웨디시·로미로미·타이 등)이고, 코스는 시간·목적 구성(60·90·120분, 피로 회복 등)입니다. 코스를 고른 뒤 원하는 테마를 함께 말씀해 주시면 됩니다."),
        ("지역이나 역과 묶인 테마 페이지는 없나요?",
         "없습니다. 테마는 독립 페이지로만 운영하고, 지역·역 페이지에서는 관련 테마 링크로만 연결합니다."),
        ("어떤 테마부터 보면 좋을까요?",
         "처음이라면 스웨디시, 건식을 원하면 타이마사지, 향까지 원하면 아로마테라피부터 확인해 보세요."),
        ("테마를 정하지 않고 예약해도 되나요?",
         "네. 코스만 정하시면 기본 테마(스웨디시 계열)로 진행되며, 상담 중에 컨디션을 듣고 알맞은 테마를 추천드릴 수도 있습니다."),
        ("두 가지 테마를 섞을 수 있나요?",
         "전신은 스웨디시, 마무리는 발마사지처럼 부위·단계별로 조합할 수 있습니다. 예약 시 원하는 구성을 말씀해 주세요."),
    ]
    th_guide = (
        '<h3 style="font-size:20px;font-weight:800;margin:42px 0 10px"><span class="grad">테마 고르는 기준</span></h3>'
        '<p class="sec-lead" style="max-width:820px">첫 번째 기준은 오일 사용 여부입니다. 부드럽고 깊은 이완을 원하면 오일 기반의 '
        '스웨디시·로미로미·아로마테라피가 맞고, 옷을 입은 채 깔끔하게 받고 싶다면 건식인 타이마사지·중국마사지가 맞습니다.</p>'
        '<p class="sec-lead" style="max-width:820px;margin-top:12px">두 번째 기준은 압의 세기입니다. 은은한 압을 선호하면 스웨디시·아로마테라피, '
        '깊지만 아프지 않은 압은 로미로미, 또렷하고 시원한 강압은 중국마사지·스포츠·경락이 적합합니다.</p>'
        '<p class="sec-lead" style="max-width:820px;margin-top:12px">세 번째 기준은 받는 환경과 목적입니다. 자택이면 홈케어, 숙소면 호텔식마사지, '
        '늦은 시간이면 24시간 안내, 받다가 잠들고 싶다면 수면 가능 구성을 참고하세요. 부위·목적별로는 발마사지, 스킨케어, 왁싱, '
        '둘이 함께라면 커플 관리가 있습니다.</p>'
        '<p class="sec-lead" style="max-width:820px;margin-top:12px">테마를 정했다면 다음은 시간입니다. 시간(60·90·120분)과 요금은 '
        '테마가 아니라 코스 기준으로 정해지므로, 코스안내에서 원하는 시간 구성을 고르고 예약 시 테마를 함께 말씀해 주시면 됩니다. '
        '어떤 조합이 맞을지 모르겠다면 전화 상담에서 오늘의 컨디션과 선호(압 세기·오일 사용 여부·받는 환경)를 알려주세요. '
        '거기에 맞는 테마와 시간을 바로 추천드립니다.</p>')
    body = (breadcrumb(trail) +
        '<section class="block" style="padding-bottom:40px"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>THEME GUIDE</span>'
        '<h2 class="sec">전체 테마</h2>'
        '<p class="sec-lead" style="max-width:820px">관리 유형별 특징, 추천 대상, 예약 전 확인사항을 테마별 독립 페이지에서 안내합니다. '
        '오일 기반의 부드러운 이완(스웨디시·로미로미·아로마테라피), 건식의 개운함(타이·중국마사지·스포츠·경락), '
        '방문 환경별 안내(홈케어·호텔식·24시간·수면 가능), 부위·목적별 관리(발·스킨케어·왁싱·커플)로 나뉩니다.</p>'
        f'<div class="grid g3" style="margin-top:28px">{cards}</div>'
        + th_guide +
        '<div class="data-box" style="max-width:820px;margin-top:30px"><b>운영 기준</b>'
        '<p>테마는 독립 페이지로 운영하며, 특정 지역·역과 조합한 페이지(예: 역 이름 + 테마)는 만들지 않습니다. '
        '테마 선택이 어려우면 코스 선택 가이드를 먼저 확인하거나 상담 시 컨디션을 말씀해 주세요.</p></div>'
        '</div></section>' + faq_block(th_faq) + cta_band())
    coll = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "테마별 안내", "url": BASE_URL + "/themes/",
        "hasPart": [{"@type": "WebPage", "name": t["name"],
                     "url": BASE_URL + f"/themes/{t['slug']}/"} for t in THEMES],
    }
    html = page("/themes/", "테마별 안내 | 금천 방문 관리 전체 테마",
        "금천 방문 관리 테마별 안내 - 스웨디시, 로미로미, 타이마사지, 아로마테라피, 홈케어, 발마사지, 왁싱 등 관리 유형별 특징과 추천 대상을 안내합니다.",
        "themes", body, [bc_ld(trail), coll, faq_ld(th_faq)])
    write("/themes/", html)


# 테마별 개별화된 title 수식어 (짧은 테마명 간 메타 유사도 완화)
THEME_TITLE_TAIL = {
    "swedish": "부드러운 오일 전신 이완", "lomilomi": "하와이식 딥티슈 리듬 케어",
    "thai-massage": "스트레칭 중심 건식 케어", "chinese-massage": "경혈 지압 강압 케어",
    "aromatherapy": "향과 함께하는 심신 이완", "home-care": "자택에서 받는 기본 구성",
    "hotel-style": "호텔·숙소 방문 프리미엄 케어", "foot-care": "발·종아리 집중 케어",
    "sports-meridian": "운동 후 근육·경락 집중 케어", "skin-care": "얼굴·두피 컨디션 정돈",
    "waxing": "출장 왁싱과 사후 케어", "couple-care": "2인 동반 구성 안내",
    "24-hours": "심야·새벽 이용 가이드", "sleep-friendly": "잠들어도 되는 수면 구성",
}


def build_theme_pages():
    tt = [("/", "홈"), ("/themes/", "테마별 안내")]
    for t in THEMES:
        content_page(f"/themes/{t['slug']}/", "themes", tt + [(None, t["name"])],
            title=f"{t['name']} | {THEME_TITLE_TAIL[t['slug']]} · 금천 방문 관리",
            desc=f"금천 방문 관리 {t['name']} 테마 안내 - {t['short']} 특징과 추천 대상, 진행 방식, 예약 전 확인사항을 확인하세요.",
            eyebrow=t["kicker"], h1=f"{t['name']} 테마 안내",
            lead=t["lead"], sections=t["sections"], faq=t["faq"],
            data_note=t.get("data_note"), show_price=True,
            service=(f"{t['name']} 방문 관리", t["short"]),
            top_links=[("tel:" + PHONE_TEL, "예약문의", True),
                       ("/themes/", "전체 테마"), ("/course/guide/", "코스 선택 가이드")],
            cta_title=f"{t['name']} 관리, 지금 예약해 보세요")


# ---- 코스 허브 + 코스 페이지 ---------------------------------------------------
def build_course_hub():
    trail = [("/", "홈"), (None, "코스안내")]
    course_cards = "".join(
        f'<a class="card reveal" href="/course/{c["slug"]}/"><div class="k">{c["kicker"]}</div>'
        f'<h3>{c["name"]}</h3><p>{c["desc"]}</p><span class="more">코스 보기 →</span></a>'
        for c in COURSES)
    more_cards = (
        '<a class="card reveal" href="/course/price/"><div class="k">PRICE</div>'
        '<h3>가격 안내</h3><p>코스별 60·90·120분 정찰 요금과 변동 요소를 안내합니다.</p>'
        '<span class="more">가격 보기 →</span></a>'
        '<a class="card reveal" href="/course/guide/"><div class="k">GUIDE</div>'
        '<h3>코스 선택 가이드</h3><p>목적·상황별 추천과 시간 선택 기준을 안내합니다.</p>'
        '<span class="more">가이드 보기 →</span></a>')
    course_faq = [
        ("코스는 어떻게 선택하나요?",
         "컨디션과 목적을 말씀해 주시면 피로 회복·아로마·스포츠·홈타이 중 적합한 코스를 안내드립니다."),
        ("코스와 테마를 함께 골라야 하나요?",
         "코스만 골라도 됩니다. 원하는 관리 방식(테마)이 있으면 예약 시 함께 말씀해 주세요."),
        ("커플·단체 관리도 되나요?",
         "커플·가족 동반 관리와 기업·단체 사전 협의형 관리를 운영합니다. 각 코스 페이지에서 조건을 확인하세요."),
        ("표시된 요금 외 추가 비용이 있나요?",
         "정찰 요금을 원칙으로 하며, 변동 사항은 예약 시 사전에 안내드립니다."),
        ("시간은 어떻게 고르나요?",
         "60분은 핵심 부위 정리, 90분은 전신을 고르게 푸는 표준 구성, 120분은 마무리 케어까지 여유 있는 구성입니다. 고민되면 90분으로 시작해 보세요."),
    ]
    course_guide = (
        '<h3 style="font-size:20px;font-weight:800;margin:42px 0 10px"><span class="grad">코스는 이렇게 구성됩니다</span></h3>'
        '<p class="sec-lead" style="max-width:820px">모든 코스는 시간(60·90·120분)과 목적의 조합입니다. 피로 회복 관리는 부드러운 전신 이완, '
        '아로마 관리는 향을 더한 심신 이완, 스포츠 관리는 또렷한 압의 근육 정리, 홈타이 코스는 옷을 입은 채 받는 건식 스트레칭 관리입니다. '
        '여기에 인원 구성에 따라 커플·가족 동반 관리와 기업·단체 협의형 관리가 더해집니다.</p>'
        '<p class="sec-lead" style="max-width:820px;margin-top:12px">예약 흐름은 간단합니다. 코스와 시간을 고르고, 위치와 희망 시각을 알려주시면 '
        '방문 가능 여부와 최종 요금을 확인해 드립니다. 관리 방식(테마)을 바꾸고 싶다면 예약 시 함께 말씀해 주세요. '
        '테마별 특징은 테마별 안내에서 따로 설명합니다.</p>'
        '<h3 style="font-size:20px;font-weight:800;margin:42px 0 10px"><span class="grad">요금은 이렇게 안내됩니다</span></h3>'
        '<p class="sec-lead" style="max-width:820px">모든 코스는 정찰 요금이 원칙입니다. 아래 기본 요금표에서 시간별 금액을 확인할 수 있고, '
        '코스 종류·방문 지역·시간대(심야 등)·인원에 따라 달라지는 부분은 예약 상담에서 최종 확인해 드립니다. '
        '현장에서 사전 안내와 다른 금액을 요구하지 않으며, 변동이 필요한 경우 반드시 관리 전에 설명드리고 동의를 받은 뒤 진행합니다.</p>'
        '<p class="sec-lead" style="max-width:820px;margin-top:12px">어느 코스가 맞을지 고민된다면 처음에는 90분 피로 회복 관리로 시작해 보세요. '
        '받아본 뒤 압이 약했다면 스포츠 관리로, 향이 좋았다면 아로마 관리로, 건식이 편했다면 홈타이로 옮겨가며 '
        '내게 맞는 구성을 찾는 분들이 많습니다. 자세한 선택 기준은 코스 선택 가이드에서 안내합니다.</p>')
    body = (breadcrumb(trail) +
        '<section class="block" id="all" style="padding-bottom:30px"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>COURSE</span>'
        '<h2 class="sec">전체 코스</h2>'
        '<p class="sec-lead" style="max-width:820px">목적과 컨디션에 맞춰 고를 수 있는 방문 관리 코스입니다. '
        '피로 회복·아로마·스포츠는 컨디션 목적별 구성이고, 홈타이는 건식 타이마사지 방문 코스, '
        '커플·가족과 기업·단체는 인원 구성에 따른 코스입니다. 코스를 눌러 상세 안내를 확인하세요.</p>'
        f'<div class="grid g3" style="margin-top:26px">{course_cards}</div>'
        + course_guide + '</div></section>' +
        price_menu_block() +
        '<section class="block" style="padding-top:30px"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>MORE</span>'
        '<h2 class="sec">가격과 코스 선택</h2>'
        f'<div class="grid g2" style="margin-top:24px">{more_cards}</div></div></section>' +
        faq_block(course_faq) + cta_band())
    jsonld = [bc_ld(trail),
              service_ld("방문 마사지 코스", "피로 회복·아로마·스포츠·홈타이·커플·가족·기업·단체 방문 관리 코스", "/course/"),
              offer_ld(), faq_ld(course_faq)]
    html = page("/course/", "코스안내 | 금천 출장마사지 코스·요금 안내",
        "금천 출장마사지 코스안내 - 피로 회복, 아로마, 스포츠, 홈타이, 커플·가족, 기업·단체 코스 설명과 60·90·120분 정찰 요금을 안내합니다.",
        "course", body, jsonld)
    write("/course/", html)


def build_course_pages():
    ct = [("/", "홈"), ("/course/", "코스안내")]
    for c in COURSE_DETAIL:
        content_page(f"/course/{c['slug']}/", "course", ct + [(None, c["name"])],
            title=c["title"], desc=c["desc"], eyebrow=c["eyebrow"], h1=c["h1"],
            lead=c["lead"], sections=c["sections"], faq=c["faq"],
            data_note=c.get("data_note"), show_price=c.get("show_price", True),
            service=c.get("service"),
            top_links=[("tel:" + PHONE_TEL, "예약문의", True),
                       ("/course/", "전체 코스"), ("/course/price/", "가격 안내")])


# ---- 운영팀 소개 (E-E-A-T: Who·How·Why, 책임 저자) -------------------------------
def build_about():
    trail = [("/", "홈"), (None, "운영팀 소개")]
    about_faq = [
        ("이 사이트의 정보는 누가 작성하나요?",
         f"금천 VIP 운영팀이 작성하고 운영 책임자({COMPANY['ceo']})가 감수합니다. 모든 페이지 하단 바이라인에 작성·감수·업데이트 일자를 표기합니다."),
        ("콘텐츠의 근거는 무엇인가요?",
         "실제 예약 상담에서 반복되는 질문과 예약 데이터에서 확인되는 이용 패턴(시간대·지역·코스 선택 비율)이 1차 근거입니다. 외부 자료를 옮겨 적는 방식의 글은 만들지 않습니다."),
        ("문의는 어디로 하나요?",
         f"전화 {PHONE_DISP}(연중무휴 24시간)로 받습니다. 콘텐츠 오류 제보도 같은 번호로 주시면 확인 후 수정합니다."),
    ]
    sections = [
        ("WHO — 누가 만드나요", [
            f"이 사이트는 서울 금천구 방문 건강관리 예약을 운영하는 <strong>{COMPANY['name']}</strong> 운영팀이 직접 만들고 관리합니다.",
            "예약 접수, 관리사 배정, 고객 응대를 매일 수행하는 실무팀이 콘텐츠 작성을 겸하고 있어, 글에 담기는 정보는 외부 작가의 짐작이 아니라 현장의 운영 경험에서 나옵니다.",
            f"모든 콘텐츠의 최종 책임자는 운영 대표({COMPANY['ceo']})이며, 각 페이지 하단 바이라인에 작성 주체와 감수자, 최종 업데이트 일자를 표기합니다."]),
        ("HOW — 어떻게 만드나요", [
            "콘텐츠는 세 가지 재료로 만듭니다. ① 예약 상담에서 실제로 반복되는 질문, ② 예약 데이터에서 확인되는 이용 패턴(지역·시간대·코스 선택 비율, 평균 도착 시간), ③ 현장 운영에서 정리된 응대·위생 기준.",
            "각 지역 페이지의 '현장 운영 메모'와 평균 도착 시간은 이 데이터를 바탕으로 작성한 1차 정보입니다. 초안 작성에 도구의 도움을 받는 경우에도 사실 확인과 최종 검수는 항상 운영팀이 직접 수행합니다.",
            "잘못된 정보를 발견하면 즉시 수정하고 페이지의 업데이트 일자를 갱신합니다. 오류 제보는 언제든 환영합니다."]),
        ("WHY — 왜 만드나요", [
            "방문 마사지 정보는 과장과 키워드 나열이 많은 분야입니다. 저희는 반대로 갑니다 — 이용자가 예약 전에 궁금한 것(가능 지역, 도착 시간, 요금, 준비물)을 사실대로 답하는 것이 이 사이트의 목적입니다.",
            "그래서 지역 페이지는 대표 동 3개로만 운영하고(숫자 행정동 통합), 같은 내용을 지역명만 바꿔 반복하는 페이지를 만들지 않습니다. 테마·코스도 각각 한 페이지에서 깊이 있게 다룹니다.",
            "본 서비스는 의료 행위가 아닌 이완·휴식 목적의 건강관리이며, 의료적 효과를 주장하는 표현을 쓰지 않는 것을 편집 원칙으로 합니다."]),
        ("운영 기준 요약", [
            ("ul", ["정찰 요금 — 상담에서 확정한 금액이 최종 금액입니다. 현장 추가 요구 없음.",
                    "사전 안내 — 변동 요소(심야·인접 지역·인원)는 반드시 예약 단계에서 고지합니다.",
                    "위생·안전 — 용품 위생 기준과 응대 가이드라인을 공개 운영합니다.",
                    "연령 기준 — 만 19세 이상 성인 대상이며 불법·퇴폐 행위를 일절 제공하지 않습니다.",
                    "후기 원칙 — 대가성 후기를 받지 않고, 동의된 후기만 게시합니다."]),
            "세부 기준은 <a href='/geumcheon-gu/safety/'>위생 및 안전 안내</a>, <a href='/course/price/'>가격 안내</a>, <a href='/reviews/'>후기 운영 안내</a>에서 확인할 수 있습니다."]),
        ("연락처와 책임 정보", [
            f"상호 {COMPANY['name']} · 대표 {COMPANY['ceo']} · 개인정보보호책임자 {COMPANY['privacy_officer']}",
            f"전화 <strong>{PHONE_DISP}</strong> ({HOURS}) — 예약·문의·오류 제보 모두 이 번호로 받습니다.",
            "사업자 정보는 모든 페이지 하단에, 개인정보 처리 기준은 <a href='/privacy/'>개인정보처리방침</a>에 공개되어 있습니다."]),
    ]
    content_page("/about/", "customer", trail,
        title="운영팀 소개 | 금천 VIP 마사지는 누가, 어떻게, 왜 만드나",
        desc="금천 VIP 마사지 운영팀 소개 - 콘텐츠를 만드는 사람(Who), 만드는 방식과 데이터 근거(How), 운영 철학(Why), 책임자 연락처를 공개합니다.",
        eyebrow="ABOUT · WHO·HOW·WHY", h1="운영팀 소개",
        lead="이 사이트의 모든 정보는 금천구 예약 현장을 매일 운영하는 팀이 직접 작성하고 책임집니다. "
             "누가, 어떻게, 왜 만드는지 투명하게 공개합니다.",
        sections=sections, faq=about_faq,
        data_note="페이지마다 표기된 평균 도착 시간과 이용 패턴은 자체 예약 데이터 기준이며, 분기마다 갱신합니다. 수치가 실제와 다르게 느껴진다면 제보해 주세요 — 확인 후 바로 수정합니다.",
        top_links=[("tel:" + PHONE_TEL, "전화 문의", True),
                   ("/geumcheon-gu/safety/", "위생·안전 기준"), ("/customer/", "고객센터")],
        extra_schema=[org_ld()])


# ---- 매거진(블로그) -------------------------------------------------------------
def post_card(p):
    return (f'<a class="card reveal" href="/magazine/{p["slug"]}/">'
            f'<div class="k">{p["category"]} · {p["date"].replace("-", ".")}</div>'
            f'<h3>{p["h1"].split(" — ")[0].split(" —")[0]}</h3><p>{p["lead"][:80]}…</p>'
            f'<span class="more">글 읽기 →</span></a>')


def blogposting_ld(p):
    path = f"/magazine/{p['slug']}/"
    return {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p["h1"], "description": p["desc"], "inLanguage": "ko-KR",
        "articleSection": p["category"],
        "author": {"@type": "Organization", "name": f"{BRAND_SHORT} 운영팀", "url": BASE_URL + "/about/"},
        "publisher": {"@type": "Organization", "name": COMPANY["name"], "url": BASE_URL + "/",
                      "logo": {"@type": "ImageObject", "url": BASE_URL + "/icon-512.png"}},
        "mainEntityOfPage": BASE_URL + path,
        "image": BASE_URL + "/assets/og-cover.jpg",
        "datePublished": p["date"], "dateModified": UPDATED,
    }


def build_magazine_hub():
    trail = [("/", "홈"), (None, "매거진")]
    posts_sorted = sorted(POSTS, key=lambda p: p["date"], reverse=True)
    cards = "".join(post_card(p) for p in posts_sorted)
    mg_faq = [
        ("매거진에는 어떤 글이 올라오나요?",
         "이용 가이드, 테마 비교, 금천 지역 생활 정보, 건강 루틴 등 방문 관리를 더 잘 활용하기 위한 정보성 글을 게재합니다."),
        ("글의 내용대로 예약하면 되나요?",
         "글은 선택 기준을 돕는 참고 자료입니다. 실제 가능 여부와 구성은 예약 상담에서 위치·시간 기준으로 확정해 드립니다."),
        ("의학 정보로 봐도 되나요?",
         "아닙니다. 모든 글은 이완·휴식 목적의 건강관리 정보이며, 통증·질환은 의료기관 진료를 권합니다."),
        ("새 글은 얼마나 자주 올라오나요?",
         "비정기적으로 추가됩니다. 지역·테마 페이지와 연결되는 주제 중심으로 차례로 발행합니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block" style="padding-bottom:40px"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>MAGAZINE</span>'
        '<h2 class="sec">매거진 — 전체 글</h2>'
        '<p class="sec-lead" style="max-width:820px">출장마사지·홈타이를 더 잘 활용하기 위한 정보를 모았습니다. '
        '처음 이용하는 분을 위한 단계별 가이드부터 홈타이와 스웨디시처럼 헷갈리는 테마 비교, '
        '가산디지털단지 야근 후 회복 루틴 같은 금천 지역 생활 정보, 수면·운동과 마사지의 관계까지 — '
        '예약 상담에서 실제로 가장 많이 받는 질문들을, 예약 데이터에서 보이는 실제 이용 패턴과 함께 글로 정리했습니다.</p>'
        '<p class="sec-lead" style="max-width:820px;margin-top:12px">각 글에는 관련된 '
        '<a href="/geumcheon-gu/area/" style="color:var(--gold);font-weight:700">지역별 안내</a>, '
        '<a href="/geumcheon-gu/stations/" style="color:var(--gold);font-weight:700">지하철역별 안내</a>, '
        '<a href="/themes/" style="color:var(--gold);font-weight:700">테마별 안내</a> 페이지가 연결되어 있어 '
        '글을 읽다가 바로 상세 안내로 이동할 수 있습니다. 읽는 순서가 고민된다면 처음 이용 가이드 → 압 세기 고르는 법 → '
        '관심 있는 테마 비교 순서를 권합니다. 모든 글에는 발행일과 작성 주체를 표기하고, 내용이 바뀌면 업데이트 일자를 갱신합니다.</p>'
        f'<div class="grid g3" style="margin-top:28px">{cards}</div>'
        '<div class="data-box" style="max-width:820px;margin-top:30px"><b>편집 기준</b>'
        '<p>매거진의 모든 글은 검색을 위한 키워드 나열이 아니라, 실제 예약 상담에서 반복되는 질문과 예약 데이터에서 보이는 '
        '이용 패턴을 바탕으로 작성합니다. 지역·역·테마를 조합한 중복성 글은 만들지 않으며, 글당 한 가지 주제를 깊이 있게 다룹니다. '
        '작성 주체와 검수 기준은 <a href="/about/">운영팀 소개</a>에 공개되어 있습니다.</p></div>'
        '</div></section>' + faq_block(mg_faq) + cta_band())
    coll = {
        "@context": "https://schema.org", "@type": "Blog",
        "name": f"{BRAND} 매거진", "url": BASE_URL + "/magazine/",
        "blogPost": [{"@type": "BlogPosting", "headline": p["h1"],
                      "url": BASE_URL + f"/magazine/{p['slug']}/",
                      "datePublished": p["date"]} for p in posts_sorted],
    }
    html = page("/magazine/", "매거진 | 금천 출장마사지·홈타이 이용 가이드와 지역 정보",
        "금천 VIP 마사지 매거진 - 출장마사지 처음 이용 가이드, 홈타이·스웨디시 비교, 가산디지털단지 야근 회복 루틴, 수면·운동과 마사지 정보를 제공합니다.",
        "magazine", body, [bc_ld(trail), coll, faq_ld(mg_faq)])
    write("/magazine/", html)


def build_magazine_posts():
    mt = [("/", "홈"), ("/magazine/", "매거진")]
    for p in POSTS:
        path = f"/magazine/{p['slug']}/"
        related_cards = "".join(post_card(POST_BY_SLUG[s]) for s in p["related"] if s in POST_BY_SLUG)
        toc_html, panels = render_lux(p["sections"])
        panels += (
            '<section class="lux-sec reveal" id="related"><h2>함께 읽기</h2>'
            '<p>이 글과 이어지는 매거진 글입니다.</p>'
            f'<div class="grid g3">{related_cards}</div></section>')
        post_byline = (f'<div class="byline">'
                       f'<span class="au">{p["category"]}</span>'
                       f'<span>발행 · {p["date"].replace("-", ".")}</span>'
                       f'<span>작성 · {BRAND_SHORT} 운영팀</span>'
                       f'<span>최종 업데이트 · {UPDATED.replace("-", ".")}</span></div>')
        body = (breadcrumb(mt + [(None, p["menu"])]) +
            f'<section class="lux-hero"><div class="wrap">'
            f'<span class="eyebrow"><span class="pulse"></span>{p["kicker"]}</span>'
            f'<h1 class="lux-h1">{p["h1"]}</h1>'
            f'<p class="lux-lead">{p["lead"]}</p>{post_byline}'
            f'<div class="actions" style="margin-top:22px">'
            f'<a class="btn btn-primary" href="tel:{PHONE_TEL}">예약문의</a>'
            f'<a class="btn btn-ghost" href="/magazine/">매거진 전체 글</a></div></div></section>'
            f'<section class="block lux-body" style="padding-top:34px"><div class="wrap">'
            f'<div class="lux-grid">{toc_html}<div class="lux-main">{panels}</div></div>'
            f'</div></section>'
            + faq_block(p["faq"]) + cta_band())
        trail = mt + [(None, p["menu"])]
        jsonld = [bc_ld(trail), blogposting_ld(p), faq_ld(p["faq"])]
        html = page(path, p["title"], p["desc"], "magazine", body, jsonld, og_type="article")
        write(path, html)


# ---- 예약안내 / 이용가이드 -----------------------------------------------------
def build_reservation():
    trail = [("/", "홈"), (None, "예약안내")]
    res_faq = [
        ("당일 예약이 가능한가요?", "가능합니다. 다만 저녁·주말은 문의가 몰릴 수 있어 사전 예약을 권장드립니다."),
        ("예약을 변경하고 싶어요.", "확정된 일정 변경은 가능한 한 빠르게 연락 주시면 조정을 도와드립니다. 빠를수록 다른 시간으로 옮기기 쉽습니다."),
        ("결제는 어떻게 하나요?", "정찰 요금을 사전에 안내드리며 결제 방법은 예약 시 함께 안내합니다. 현장에서 금액이 바뀌지 않습니다."),
        ("전화 말고 다른 예약 방법이 있나요?", "현재는 전화 상담이 가장 빠르고 정확합니다. 통화가 어려우면 문자를 남겨주셔도 순서대로 회신드립니다."),
        ("예약자와 받는 사람이 달라도 되나요?", "네. 선물 예약도 많습니다. 받는 분의 주소·연락처만 정확히 알려주세요."),
        ("며칠 뒤 예약도 미리 잡을 수 있나요?", "네. 기념일·행사처럼 날짜가 정해진 일정은 미리 잡아두는 편이 원하는 시간 확보에 유리합니다."),
    ]
    sections = [
        ("예약은 다섯 단계로 끝납니다", [
            "① 위치 확인 — 동 이름, 가까운 역, 또는 정확한 주소를 알려주세요. ② 시간 확인 — 희망 시각을 말씀하시면 그 시간대 배정 상황을 확인합니다.",
            "③ 코스·인원 확인 — 코스가 고민이면 컨디션만 말씀하셔도 추천드립니다. ④ 가능 여부 안내 — 예상 도착 시간과 최종 요금을 함께 확정합니다. ⑤ 예약 확정 — 끝입니다. 평균 통화 시간은 1~2분입니다.",
            "코스 선택이 막막하면 <a href='/course/guide/'>코스 선택 가이드</a>를, 첫 이용 전체 흐름은 <a href='/magazine/first-time-guide/'>처음 이용 가이드</a>를 먼저 읽어보세요."]),
        ("예약 가능 시간", [
            "전화 상담은 연중무휴 24시간 운영합니다. 실제 방문 가능 시간은 시간대·위치·배정 상황에 따라 달라지며 상담에서 확정됩니다.",
            "밤 21~24시는 하루 중 예약이 가장 몰리는 시간대입니다. 원하는 시간이 있다면 한두 시간 전 미리 연락하시는 편이 확실합니다.",
            "시간대별 특징과 도착 시간을 줄이는 요령은 <a href='/geumcheon-gu/hours/'>예약 가능 시간 안내</a>에서 자세히 다룹니다."]),
        ("방문 가능 장소", [
            "자택, 오피스텔, 호텔·레지던스 숙소 모두 방문합니다. 장소 유형별 준비 사항은 <a href='/geumcheon-gu/checklist/'>이용 전 확인사항</a>에 정리되어 있습니다.",
            "지역은 금천구 전역(가산동·독산동·시흥동)이 기본 권역이며, 인접 지역은 위치 기준으로 상담 시 확인해 드립니다.",
            ("ul", ['<a href="/geumcheon-gu/area/">지역별 안내에서 우리 동 확인하기</a>',
                    '<a href="/geumcheon-gu/stations/">지하철역 기준으로 확인하기</a>'])]),
        ("결제 안내", [
            "코스별 정찰 요금을 예약 단계에서 확정해 안내드립니다. 변동 요소(심야 시간대, 인접 지역, 인원 구성)가 있으면 반드시 상담에서 먼저 고지합니다.",
            "결제 수단은 예약 시 함께 안내드리며, 요금 구조 전체는 <a href='/course/price/'>가격 안내</a>에서 확인할 수 있습니다."]),
        ("변경·취소 안내", [
            "일정 변경과 취소는 부담 없이 가능합니다. 다만 관리사가 이동을 시작한 뒤에는 조정이 어려울 수 있어, 변동이 생기면 가능한 한 빨리 연락 주세요.",
            "예약 시간에 연락이 닿지 않으면 확인 후 일정이 조정될 수 있습니다. 도착 전 연락 가능한 번호를 꼭 남겨주세요."]),
        ("예약 전 체크리스트", [
            ("ul", ["방문 장소 주소(공동현관 출입 방법 포함)",
                    "연락 가능한 전화번호",
                    "희망 코스와 시간(60·90·120분)",
                    "희망 시각과 대안 시각 하나",
                    "특이사항(알러지·임신·관절 질환·반려동물 등)"]),
            "다섯 가지를 미리 정리해 두면 상담이 1분 안에 끝납니다."]),
    ]
    content_page("/reservation/", "reservation", trail,
        title="예약안내 | 금천 출장마사지 예약 방법·결제 안내",
        desc="금천 출장마사지 예약안내 - 5단계 예약 방법, 예약 가능 시간, 방문 가능 장소, 결제와 변경·취소 기준을 안내합니다. 연중무휴 24시간 상담.",
        eyebrow="RESERVATION", h1="예약안내",
        lead="예약 방법부터 결제·변경까지 — 전화 한 통으로 끝나는 전체 과정을 단계별로 안내합니다.",
        sections=sections, faq=res_faq,
        data_note="예약 통화의 평균 소요 시간은 1~2분입니다. 위치·시간·코스 세 가지가 준비된 상담은 1분 안에 확정되는 비율이 가장 높습니다. "
                  "변경·취소 연락이 빠른 예약일수록 원하는 대체 시간이 잡히는 비율도 높았습니다.",
        top_links=[("tel:" + PHONE_TEL, "지금 예약하기", True),
                   ("/course/guide/", "코스 선택 가이드"), ("/geumcheon-gu/hours/", "예약 가능 시간")])


def build_guide():
    trail = [("/", "홈"), (None, "이용가이드")]
    guide_faq = [
        ("처음인데 무엇을 준비하나요?", "편히 쉴 수 있는 공간과 연락 가능한 번호만 있으면 됩니다. 용품은 관리사가 모두 준비합니다."),
        ("관리 후 주의할 점이 있나요?", "충분한 수분 섭취와 휴식을 권장드립니다. 깊은 압을 받은 날은 사우나·음주를 피하세요."),
        ("이 서비스는 의료 행위인가요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상을 대상으로 합니다."),
        ("관리사에게 직접 요청해도 되나요?", "압·부위·온도 등 관리 관련 요청은 언제든 직접 말씀하시면 됩니다. 일정 변경은 예약 전화로 해주세요."),
        ("후기를 남기고 싶어요.", "이용 후 문자나 전화로 남겨주시면 동의를 받아 후기 페이지에 게시합니다."),
        ("같은 관리사를 다시 요청할 수 있나요?", "네. 좋았던 관리사가 있다면 예약 시 말씀해 주세요. 일정이 맞으면 우선 배정해 드립니다."),
        ("받는 중에 자세를 바꿔달라고 해도 되나요?", "물론입니다. 목 각도, 베개 높이, 실내 온도까지 사소한 것도 편하게 요청하세요."),
        ("끝나고 바로 외출해도 되나요?", "가능하지만 이완 효과를 길게 가져가려면 30분 이상 휴식 후 움직이는 것을 권합니다."),
    ]
    sections = [
        ("처음 이용하신다면", [
            "예약 시 지역·시간·코스만 말씀해 주시면 나머지는 안내에 따라 진행됩니다. 코스를 몰라도 컨디션을 말하면 추천을 받을 수 있습니다.",
            "관리사가 도착하면 압 세기와 집중 부위를 확인하고 시작합니다. 진행 중에도 조절 요청은 언제든 가능합니다 — 참는 것이 미덕이 아닙니다.",
            "예약부터 마무리까지의 전 과정을 한 편으로 읽고 싶다면 <a href='/magazine/first-time-guide/'>출장마사지 처음 이용 가이드</a>를 추천합니다."]),
        ("방문 전 준비사항", [
            "편하게 누울 수 있는 공간(침대 또는 바닥)과 연락 가능한 번호, 정확한 주소·출입 방법이면 충분합니다.",
            "관리 전 가벼운 샤워로 몸을 데워두면 이완이 잘 되고, 식사 후 한 시간쯤 지난 때가 가장 편안합니다.",
            "장소 유형별(자택·오피스텔·숙소) 세부 준비는 <a href='/geumcheon-gu/checklist/'>이용 전 확인사항</a>에 정리되어 있습니다."]),
        ("관리 중 이렇게 하시면 됩니다", [
            "가장 중요한 것은 솔직한 피드백입니다. \"한 단계만 세게\", \"그 부위는 빼고\" 같은 구체적인 말이 만족도를 좌우합니다.",
            "졸리면 그냥 주무셔도 됩니다. 받다가 잠드는 것은 가장 좋은 신호 중 하나이며, 아예 수면을 전제로 한 <a href='/themes/sleep-friendly/'>수면 가능 구성</a>도 있습니다.",
            "대화는 의무가 아닙니다. 조용히 받고 싶다면 시작 전에 한마디만 해두세요."]),
        ("관리 후 주의사항", [
            "따뜻한 물을 충분히 마시고, 가능하면 바로 무리한 활동 없이 쉬는 것이 좋습니다.",
            "깊은 압을 받은 다음 날 가벼운 뻐근함은 정상 반응이지만, 이틀 이상 이어지는 통증은 다음 예약에서 압을 낮추라는 신호입니다.",
            "좋았던 압·향·부위를 기억해 두세요. 다음 예약 때 그대로 말하면 두 번째부터는 내 몸에 맞춘 관리가 됩니다."]),
        ("위생·안전과 금지행위", [
            "수건·오일 등 용품은 위생 기준에 맞춰 관리하며, 관리 종료 후 사용한 공간을 정돈합니다. 상세 기준은 <a href='/geumcheon-gu/safety/'>위생 및 안전 안내</a>에 공개되어 있습니다.",
            "본 서비스는 만 19세 이상 대상의 건전한 건강관리 서비스입니다. 불법·퇴폐 행위 요구는 일절 제공되지 않으며, 요청 시 관리가 즉시 중단됩니다.",
            "과도한 음주 상태에서는 안전을 위해 관리가 어려울 수 있습니다."]),
    ]
    content_page("/guide/", "guide", trail,
        title="이용가이드 | 금천 출장마사지 방문 전 준비·주의사항",
        desc="금천 출장마사지 이용가이드 - 처음 이용하는 분을 위한 준비사항, 관리 중 요청 요령, 관리 후 주의사항, 위생·안전 기준과 금지행위 안내입니다.",
        eyebrow="GUIDE", h1="이용가이드",
        lead="처음 이용하시는 분도 안심할 수 있도록 — 방문 전 준비부터 관리 중 요청 요령, 관리 후 케어까지 순서대로 안내합니다.",
        sections=sections, faq=guide_faq,
        data_note="첫 이용 고객이 가장 자주 묻는 것은 '무엇을 준비해야 하나요'입니다. 답은 간단합니다 — 누울 자리와 연락처, 그리고 솔직한 피드백이면 충분합니다. 나머지는 전부 안내에 따라 진행됩니다.",
        top_links=[("tel:" + PHONE_TEL, "예약문의", True),
                   ("/magazine/first-time-guide/", "처음 이용 가이드 글"), ("/reservation/", "예약안내")])


# ---- 후기 ---------------------------------------------------------------------
def build_reviews():
    trail = [("/", "홈"), (None, "후기")]
    region_reviews = [
        ("가산동 · 30대", "홈타이", "야근 끝나고 오피스텔로 와주셨는데 도착 안내가 정확했습니다. 건식이라 받고 바로 잘 수 있어 좋았어요."),
        ("독산동 · 40대", "피로회복", "예약부터 마무리까지 깔끔했고 위생 안내가 꼼꼼했습니다. 90분이 금방 갔네요."),
        ("시흥동 · 30대", "아로마", "주말 저녁에 받았는데 응대가 정중하고 편안했어요. 라벤더 향 추천대로 받길 잘했습니다."),
        ("가산동 · 40대", "스포츠·경락", "어깨가 돌처럼 굳어 있었는데 압 조절을 잘 해주셔서 시원하게 풀렸습니다."),
        ("독산동 · 30대", "커플", "기념일에 둘이 같이 받았는데 각자 다른 코스로 해주셔서 만족했어요."),
        ("시흥동 · 50대", "발마사지", "호암산 다녀온 날 받았는데 다리가 확 가벼워졌습니다. 다음 주에 또 예약했어요."),
    ]
    station_reviews = [
        ("가산디지털단지역 인근 · 30대", "스웨디시", "환승하고 숙소 도착할 때쯤 맞춰 와주셔서 좋았습니다. 출장 때마다 부를 것 같아요."),
        ("독산역 인근 · 40대", "스포츠", "운동 후 받았는데 컨디션이 한결 가벼워졌어요. 하체 위주로 잘 풀어주셨습니다."),
        ("금천구청역 인근 · 50대", "발마사지", "도착 시간을 미리 알려주셔서 기다림이 없었습니다. 설명도 친절했어요."),
        ("가산디지털단지역 인근 · 20대", "수면 가능", "받다가 진짜 잠들었는데 약속한 대로 조용히 마무리해 주셨습니다. 신기한 경험이었어요."),
    ]
    course_reviews = [
        ("재방문 · 30대", "아로마 90분", "지난번 향을 기억해 주셔서 놀랐어요. 두 번째가 훨씬 좋았습니다."),
        ("첫 이용 · 40대", "피로 회복 90분", "처음이라 긴장했는데 압 확인부터 마무리까지 설명이 명확해서 편했습니다."),
        ("정기 이용 · 30대", "홈타이 60분", "매주 수요일 밤 고정으로 받고 있어요. 한 주 피로가 쌓이질 않네요."),
    ]
    def cards(rows):
        return "".join(
            f'<div class="review reveal"><div class="stars">★★★★★</div>'
            f'<p>“{q}”</p><div class="who">{w} · {c} 이용</div></div>' for w, c, q in rows)
    rv_faq = [
        ("후기는 어떻게 남기나요?",
         "이용 후 문자 또는 전화로 남겨주시면 됩니다. 게시 동의를 받은 후기만 이곳에 게재합니다."),
        ("후기를 남기면 혜택이 있나요?",
         "후기 대가로 금전·할인을 제공하지 않습니다. 대가성 후기는 신뢰를 해치기 때문에 받지 않는 것이 원칙입니다."),
        ("내 후기를 지우고 싶어요.",
         "고객센터로 요청하시면 확인 후 바로 삭제해 드립니다."),
        ("후기가 실제 이용 후기인지 어떻게 믿나요?",
         "예약 기록이 확인된 이용 건의 후기만 게시하며, 대가성 후기를 받지 않는 원칙을 운영팀 소개에 공개하고 있습니다."),
        ("아쉬웠던 점도 적어도 되나요?",
         "네. 비판적인 의견도 같은 기준으로 검토하며, 서비스 개선의 가장 중요한 자료로 사용합니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block" id="all" style="padding-bottom:30px"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>REVIEWS</span>'
        '<h2 class="sec">전체 후기</h2>'
        '<p class="sec-lead" style="max-width:820px">이용하신 고객들의 후기입니다. 후기는 실제 이용 고객의 동의 하에 게시되며, '
        '개인을 특정할 수 있는 정보(이름·연락처·상세 주소)는 표시하지 않습니다. 지역과 연령대, 이용 코스만 함께 적어 '
        '비슷한 상황의 분들이 참고할 수 있도록 했습니다.</p>'
        f'<h3 id="region" style="font-size:20px;font-weight:800;margin:38px 0 14px"><span class="grad">지역별 후기</span></h3>'
        '<p class="sec-lead">가산동·독산동·시흥동 — 동별 생활권에서 들어온 후기입니다. 각 동의 방문 안내는 '
        '<a href="/geumcheon-gu/area/" style="color:var(--gold);font-weight:700">지역별 안내</a>에서 확인하세요.</p>'
        f'<div class="grid g3" style="margin-top:14px">{cards(region_reviews)}</div>'
        f'<h3 id="station" style="font-size:20px;font-weight:800;margin:38px 0 14px"><span class="grad">역세권 후기</span></h3>'
        '<p class="sec-lead">지하철역 인근 숙소·오피스텔 이용 후기입니다. 역 기준 안내는 '
        '<a href="/geumcheon-gu/stations/" style="color:var(--gold);font-weight:700">지하철역별 안내</a>에서 확인하세요.</p>'
        f'<div class="grid g3" style="margin-top:14px">{cards(station_reviews)}</div>'
        f'<h3 style="font-size:20px;font-weight:800;margin:38px 0 14px"><span class="grad">코스·테마별 후기</span></h3>'
        '<p class="sec-lead">어떤 관리를 받을지 고민된다면 같은 코스를 받은 분들의 후기가 참고가 됩니다. '
        '코스 설명은 <a href="/course/" style="color:var(--gold);font-weight:700">코스안내</a>, 관리 방식은 '
        '<a href="/themes/" style="color:var(--gold);font-weight:700">테마별 안내</a>에서 확인하세요.</p>'
        + f'<div class="grid g3" style="margin-top:14px">{cards(course_reviews)}</div>' +
        '<div class="data-box" id="write" style="max-width:820px;margin-top:38px"><b>후기 작성 안내</b>'
        '<p>이용 후 문자 또는 전화로 후기를 남겨주시면 동의를 받아 게시합니다. 개인정보(이름·연락처·상세 주소)는 게시하지 않으며, '
        '게시된 후기의 수정·삭제는 고객센터로 요청해 주세요. 후기에 대한 금전적 대가는 제공하지 않으며, '
        '비판적인 의견도 서비스 개선을 위해 같은 기준으로 검토합니다. 후기 운영 원칙은 운영팀 소개 페이지에도 함께 공개되어 있습니다.</p></div>'
        '</div></section>' + faq_block(rv_faq, "후기 관련 질문") + cta_band())
    html = page("/reviews/", "후기 | 금천 출장마사지 이용 후기",
        "금천 출장마사지 이용 후기 - 가산동·독산동·시흥동 지역별 후기와 역세권 후기, 후기 작성·운영 원칙을 확인하세요.",
        "reviews", body, [bc_ld(trail), faq_ld(rv_faq)])
    write("/reviews/", html)


# ---- 고객센터 / 정책 ------------------------------------------------------------
def build_customer():
    """고객센터 — 문의 채널·유형별 안내·정책 링크."""
    trail = [("/", "홈"), (None, "고객센터")]
    cust_faq = [
        ("문의는 어디로 하나요?", f"전화 {PHONE_DISP}로 문의하실 수 있습니다. 연중무휴 24시간 상담을 운영합니다."),
        ("운영 시간이 어떻게 되나요?", "연중무휴 24시간 상담을 운영합니다. 방문 가능 시간은 위치·배정 상황에 따라 안내드립니다."),
        ("개인정보는 어떻게 관리되나요?", "개인정보처리방침에 따라 예약 진행 목적으로만 이용하고, 목적 달성 후 파기합니다."),
        ("불만·개선 의견은 어떻게 전달하나요?", "전화 또는 문자로 남겨주시면 운영 책임자가 직접 확인하고 회신드립니다."),
        ("세금계산서·영수증 발급이 되나요?", "기업·단체 이용 시 사전 협의로 발급 가능합니다. 개인 이용 영수 관련 사항도 상담 시 안내드립니다."),
        ("답변까지 얼마나 걸리나요?", "전화는 즉시, 문자는 접수 순서대로 회신합니다. 밤 시간대에 남긴 문자도 빠짐없이 확인합니다."),
        ("사이트 정보가 실제와 달라요.", "오류 제보로 알려주시면 확인 후 바로 수정하고 페이지 업데이트 일자를 갱신합니다."),
        ("전화번호가 하나뿐인가요?", f"네. 예약·문의·제보 모두 {PHONE_DISP} 한 번호로 통합 운영해 안내가 엇갈리지 않도록 하고 있습니다."),
    ]
    sections = [
        ("공지사항", [
            "서비스 운영과 관련된 변경 사항(운영 시간, 요금 기준, 지역 안내)을 이곳에서 안내합니다.",
            "현재 공지: 금천구 전지역(가산동·독산동·시흥동) 정상 운영 중이며, 연중무휴 24시간 상담을 유지하고 있습니다. "
            "요금 기준은 <a href='/course/price/'>가격 안내</a> 페이지가 항상 최신 기준입니다."]),
        ("1:1 문의", [
            f"가장 빠른 채널은 전화입니다. <strong>{PHONE_DISP}</strong> — 연중무휴 24시간 상담을 운영합니다.",
            "통화가 어려운 상황이면 같은 번호로 문자를 남겨주세요. 순서대로 확인해 회신드립니다.",
            "예약 관련 문의라면 위치·시간·코스 세 가지를 함께 남겨주시면 한 번의 회신으로 확정까지 진행됩니다."]),
        ("문의 유형별 안내", [
            ("h3", "예약·변경·취소"),
            "전화 한 통이 가장 빠릅니다. 절차는 <a href='/reservation/'>예약안내</a>에 정리되어 있습니다.",
            ("h3", "서비스·코스 질문"),
            "<a href='/geumcheon-gu/faq/'>자주 묻는 질문</a>에 대부분의 답이 있습니다. 없는 질문은 전화로 바로 답드립니다.",
            ("h3", "불만·개선 의견"),
            "서비스 품질 관련 의견은 운영 책임자가 직접 확인합니다. 같은 문제가 반복되지 않도록 관리 기준에 반영합니다."]),
        ("제휴·기업 문의", [
            "기업·단체 방문 관리(워크숍·사내 복지·행사)와 제휴 문의도 같은 번호로 접수합니다.",
            "인원·날짜·장소를 알려주시면 당일 안에 견적을 안내드리며, 정기 운영도 협의 가능합니다. 구성 예시는 <a href='/course/group/'>기업·단체 방문 관리</a>에서 확인하세요."]),
        ("전화 연결이 어려울 때", [
            "심야·새벽이나 상담이 몰리는 밤 시간대에는 통화 연결이 잠시 늦어질 수 있습니다. 이때는 끊지 말고 문자를 남겨주세요 — 접수 순서대로 빠짐없이 회신드립니다.",
            "문자에는 ① 위치(동 또는 역), ② 희망 시간, ③ 코스(모르면 '추천 요청')를 적어주시면 회신 한 번으로 예약이 확정됩니다.",
            "긴급하지 않은 문의(제휴·후기 삭제·정보 수정)는 낮 시간대에 주시면 가장 빠르게 처리됩니다."]),
        ("정책·약관", [
            "서비스 이용 조건과 개인정보 처리 기준은 아래 문서에 공개되어 있습니다.",
            ("ul", ['<a href="/privacy/">개인정보처리방침</a>',
                    '<a href="/terms/">이용약관</a>',
                    '<a href="/youth/">청소년보호정책</a>']),
            "운영 주체와 콘텐츠 제작 기준이 궁금하다면 <a href='/about/'>운영팀 소개</a>를 확인해 주세요."]),
    ]
    content_page("/customer/", "customer", trail,
        title="고객센터 | 금천 VIP 마사지 문의·공지",
        desc="금천 VIP 마사지 고객센터 - 공지사항, 1:1 문의, 문의 유형별 안내, 제휴·기업 문의, 정책·약관 안내입니다. 연중무휴 24시간 상담.",
        eyebrow="CUSTOMER", h1="고객센터",
        lead=f"전화 {PHONE_DISP} · {HOURS} — 예약부터 불만 접수, 제휴 문의까지 모든 연락을 한 번호로 받습니다.",
        sections=sections, faq=cust_faq,
        data_note="문의의 대부분은 예약 관련이며, 위치·시간·코스가 함께 접수된 문의는 평균 1~2분 안에 확정됩니다. 불만·개선 의견은 운영 책임자가 직접 확인하는 것을 원칙으로 하며, 처리 결과를 반드시 회신합니다.",
        top_links=[("tel:" + PHONE_TEL, "전화 문의", True),
                   ("/geumcheon-gu/faq/", "자주 묻는 질문"), ("/reservation/", "예약안내")])


def policy_page(path, title, heading, sections, desc):
    trail = [("/", "홈"), (None, heading)]
    secs = "".join(
        f'<div class="note-card"><div class="note-content"><h3 class="note-title">{t}</h3>'
        f'<div class="note-text">{"".join(f"<p>{p}</p>" for p in ps)}</div></div></div>'
        for t, ps in sections)
    body = (breadcrumb(trail) +
        f'<section class="block"><div class="wrap">'
        f'<span class="eyebrow"><span class="pulse"></span>POLICY</span>'
        f'<h2 class="sec">{heading}</h2>'
        f'<div class="note-stack" style="margin-top:26px;max-width:820px">{secs}</div>'
        f'</div></section>')
    html = page(path, title, desc, "customer", body, [bc_ld(trail)])
    write(path, html)


def build_policies():
    policy_page("/privacy/", "개인정보처리방침 | 금천 VIP 마사지", "개인정보처리방침",
        [("제1조 수집하는 개인정보의 항목 및 방법",
          ["예약 접수와 방문 진행을 위해 다음의 최소한의 개인정보를 수집합니다: 연락처(전화번호), 방문 장소 주소, 희망 일시·코스, 출입에 필요한 안내 정보.",
           "수집 방법은 전화·문자 상담 과정에서 이용자가 직접 제공하는 방식이며, 그 외 경로로 개인정보를 수집하지 않습니다.",
           "결제 과정에서 필요한 정보는 결제 수단별 최소 범위로만 확인하며 별도로 저장하지 않습니다."]),
         ("제2조 개인정보의 이용 목적",
          ["수집한 정보는 ① 예약 확정 및 방문 일정 안내, ② 관리사 배정과 도착 안내, ③ 예약 변경·취소 처리, ④ 이용 관련 문의 응대 목적으로만 이용합니다.",
           "마케팅·광고 목적의 연락은 이용자가 별도로 동의한 경우를 제외하고 하지 않으며, 수집한 정보를 제3자에게 제공하지 않습니다."]),
         ("제3조 보유 및 파기",
          ["개인정보는 예약 이행 완료 후 지체 없이 파기하는 것을 원칙으로 합니다. 다만 관련 법령(통신비밀보호법, 전자상거래법 등)에 따라 보존 의무가 있는 정보는 해당 기간 동안 보관 후 파기합니다.",
           "전자적 파일 형태는 복구 불가능한 방법으로 삭제하고, 서면 기록은 분쇄 또는 소각하여 파기합니다."]),
         ("제4조 이용자의 권리",
          ["이용자는 언제든지 본인 개인정보의 열람·정정·삭제·처리정지를 요청할 수 있습니다.",
           f"요청은 전화({PHONE_DISP})로 접수하며, 본인 확인 후 지체 없이 처리합니다. 게시된 후기의 삭제 요청도 같은 절차로 처리됩니다."]),
         ("제5조 개인정보의 안전성 확보 조치",
          ["개인정보 접근 권한을 운영 담당자로 최소화하고, 예약 진행에 필요한 기간에만 접근하도록 관리합니다.",
           "예약 정보가 포함된 기기·문서는 잠금 상태로 관리하며, 목적 달성 즉시 파기 절차를 진행합니다."]),
         ("제6조 개인정보보호책임자",
          [f"개인정보보호책임자: {COMPANY['privacy_officer']} · 전화 {PHONE_DISP}",
           "개인정보 처리와 관련한 불만이나 피해 구제는 개인정보분쟁조정위원회, 한국인터넷진흥원 개인정보침해신고센터에도 문의하실 수 있습니다.",
           "본 방침은 2026년 6월 10일부터 적용되며, 변경 시 본 페이지를 통해 공지합니다."])],
        "금천 VIP 마사지 개인정보처리방침 - 수집 항목과 방법, 이용 목적, 보유·파기 기준, 이용자 권리, 안전성 확보 조치, 개인정보보호책임자를 안내합니다.")
    policy_page("/terms/", "이용약관 | 금천 VIP 마사지", "이용약관",
        [("제1조 목적",
          ["본 약관은 금천 VIP 마사지(이하 '운영자')가 제공하는 방문 건강관리 예약 서비스의 이용 조건과 절차, 운영자와 이용자의 권리·의무를 규정함을 목적으로 합니다."]),
         ("제2조 서비스의 내용",
          ["본 서비스는 이용자가 지정한 장소로 관리사가 방문하여 이완·휴식 목적의 건강관리(마사지)를 제공하는 예약 중개·운영 서비스입니다.",
           "본 서비스는 의료 행위가 아니며, 질환의 진단·치료·처방을 목적으로 하지 않습니다. 통증·질환이 있는 경우 의료기관 진료를 우선해야 합니다."]),
         ("제3조 이용 자격",
          ["본 서비스는 만 19세 이상 성인만 이용할 수 있으며, 운영자는 필요 시 성인 여부 확인을 요청할 수 있습니다.",
           "확인에 협조하지 않거나 미성년자로 확인되는 경우 서비스 제공이 거절됩니다."]),
         ("제4조 예약·변경·취소",
          ["예약은 전화 상담으로 접수하며, 위치·시간·코스 확인 후 확정됩니다. 확정 시 안내된 정찰 요금이 최종 요금이며 현장에서 임의 변경되지 않습니다.",
           "일정 변경·취소는 방문 전까지 가능하며, 관리사 이동 시작 후에는 제한될 수 있습니다."]),
         ("제5조 금지행위",
          ["다음 행위는 금지되며, 위반 시 사전 고지 없이 서비스가 중단되고 향후 이용이 제한될 수 있습니다: ① 불법·퇴폐 행위의 요구, ② 관리사에 대한 폭언·성희롱·신체적 위협, ③ 허위 예약 및 반복적인 무단 취소, ④ 과도한 음주 상태에서의 이용 강행.",
           "서비스 중단 시 이미 진행된 부분에 대한 요금은 반환되지 않습니다."]),
         ("제6조 운영자의 의무와 책임 제한",
          ["운영자는 위생·안전 가이드라인을 준수하며, 사전에 안내한 일정과 요금 기준을 지킵니다.",
           "천재지변, 교통 상황 등 불가항력으로 도착이 지연되는 경우 즉시 안내하며, 이용자는 대기 또는 취소를 선택할 수 있습니다.",
           "본 약관은 2026년 6월 10일부터 적용됩니다."])],
        "금천 VIP 마사지 이용약관 - 서비스 내용, 이용 자격, 예약·변경·취소 기준, 금지행위, 운영자의 의무와 책임 제한을 안내합니다.")
    policy_page("/youth/", "청소년보호정책 | 금천 VIP 마사지", "청소년보호정책",
        [("청소년 이용 제한",
          ["본 서비스는 만 19세 이상 성인을 대상으로 하는 방문 건강관리 서비스이며, 청소년은 어떠한 경우에도 이용할 수 없습니다.",
           "예약 상담 단계에서 성인 여부를 확인하며, 방문 시 미성년자로 의심되는 경우 신분 확인을 요청하고 확인이 어려우면 서비스 제공을 중단합니다."]),
         ("청소년 보호를 위한 운영 조치",
          ["청소년이 서비스에 접근하지 않도록 사이트 전반에 이용 연령 기준을 고지하고 있습니다.",
           "예약자가 성인이라도 방문 장소에 미성년자만 있는 경우 서비스가 진행되지 않습니다.",
           "광고·홍보물에서 청소년에게 유해한 표현을 사용하지 않는 것을 원칙으로 합니다."]),
         ("건전한 운영 원칙",
          ["불법·퇴폐 행위를 일절 제공하지 않으며, 이러한 요구는 즉시 서비스 중단 사유가 됩니다.",
           "본 서비스는 이완·휴식 목적의 건전한 건강관리 서비스를 지향하며, 위생·안전 기준과 응대 가이드라인을 공개 운영합니다."]),
         ("청소년보호책임자",
          [f"청소년보호책임자: {COMPANY['privacy_officer']} · 전화 {PHONE_DISP}",
           "청소년 보호와 관련한 신고·문의는 위 연락처로 접수하며, 확인 즉시 필요한 조치를 진행합니다.",
           "본 정책은 2026년 6월 10일부터 적용됩니다."])],
        "금천 VIP 마사지 청소년보호정책 - 만 19세 이상 이용 제한, 성인 확인 절차, 청소년 보호 운영 조치와 책임자 연락처를 안내합니다.")


# ---- 금천 공통 정보 페이지 (링크아웃 대상) ---------------------------------------
def build_info_pages():
    gt = [("/", "홈"), ("/geumcheon-gu/", "금천 출장마사지")]

    content_page("/geumcheon-gu/hours/", "geumcheon", gt + [(None, "예약 가능 시간")],
        title="예약 가능 시간 | 금천 출장마사지 24시간 상담·도착 안내",
        desc="금천 출장마사지 예약 가능 시간 안내 - 연중무휴 24시간 상담, 시간대별 특징, 지역별 평균 도착 시간, 예약 팁을 제공합니다.",
        eyebrow="금천 · 시간", h1="예약 가능 시간",
        lead="연중무휴 24시간 예약 상담을 운영합니다. 실제 방문 가능 시간은 시간대와 위치에 따라 안내드리며, 시간대·요일별 패턴까지 함께 정리했습니다.",
        sections=[
            ("운영 시간", [
                "전화 상담은 <strong>연중무휴 24시간</strong> 가능합니다.",
                "실제 방문 가능 시간은 시간대·위치·배정 상황에 따라 달라질 수 있어 상담 시 확정해 드립니다."]),
            ("시간대별 특징", [
                ("ul", ["낮~초저녁: 비교적 도착이 빠르고 일정 조율이 수월합니다.",
                        "밤 21~24시: 예약이 가장 많이 몰리는 시간대로, 도착 시간을 넉넉히 안내드립니다.",
                        "심야(자정 이후): 방문 가능하나 위치에 따라 도착 시간이 길어질 수 있습니다."])]),
            ("지역별 평균 도착 시간", [
                "금천구 내 위치에 따라 평균 24~32분 내외로 도착합니다.",
                "가산동 일대가 비교적 빠르고, 시흥동 남부 등 외곽은 다소 길어질 수 있습니다.",
                "예약 시 정확한 위치를 알려주시면 예상 도착 시간을 안내드립니다."]),
            ("요일별 예약 패턴", [
                "평일은 화~목요일 밤이 가장 붐비고, 월요일은 상대적으로 여유가 있습니다. 한 주의 피로가 쌓이는 수요일 밤 고정 예약 고객이 꾸준히 늘고 있습니다.",
                "금요일 저녁은 아로마·커플 구성, 토요일 오후는 운동 후 스포츠 구성, 일요일 밤은 한 주를 준비하는 피로 회복 구성이 많습니다.",
                "기념일·연휴 전날은 평소보다 일찍 마감되는 시간대가 나오므로 하루 전 예약을 권합니다."]),
            ("시간대별 상세 안내", [
                ("h3", "아침(6~10시)"),
                "출근 전·출장 출발 전 60분 구성 위주입니다. 전날 밤 예약해 두면 아침 대기가 없습니다.",
                ("h3", "낮(10~18시)"),
                "하루 중 가장 여유 있는 시간대로, 재택근무 중 휴식이나 어르신 방문 예약이 많습니다.",
                ("h3", "저녁~밤(18~24시)"),
                "퇴근 후 수요가 몰리는 피크 시간대입니다. 특히 21~24시는 한두 시간 전 예약이 안전합니다.",
                ("h3", "심야~새벽(0~6시)"),
                "방문 가능하지만 배정 변수가 커집니다. 자세한 요령은 <a href='/themes/24-hours/'>24시간 이용 안내</a>를 참고하세요."]),
            ("도착 시간을 줄이는 방법", [
                "예약 시 정확한 주소와 공동현관·동·호수 등 출입 정보를 함께 알려주세요.",
                "가까운 지하철역이나 큰 건물 등 기준점을 알려주시면 위치 파악이 빨라집니다."]),
            ("예약 변경·취소", [
                "일정이 바뀌면 가능한 한 빠르게 연락 주세요. 빠를수록 다른 시간으로 조율하기 쉽습니다."]),
        ],
        data_note="지역 평균 도착 시간(예약 데이터 기준): 가산동 25분, 독산동 27분, 시흥동 30분 내외. 역세권 기준은 각 역 페이지에서 안내합니다. "
                  "출입 정보(공동현관·호수)가 함께 접수된 예약은 그렇지 않은 예약보다 평균 도착이 5분 이상 빨랐습니다.",
        faq=[
            ("새벽에도 예약되나요?", "상담은 24시간 가능합니다. 심야는 위치에 따라 도착 시간이 길어질 수 있어 상담 시 안내드립니다."),
            ("도착까지 얼마나 걸리나요?", "지역에 따라 평균 24~32분 내외이며, 시간대와 위치에 따라 달라집니다."),
            ("당일 예약이 가능한가요?", "가능합니다. 저녁·주말은 문의가 몰릴 수 있어 사전 예약을 권장드립니다."),
            ("예약이 가장 잘 잡히는 시간은 언제인가요?", "평일 낮~초저녁과 월요일이 상대적으로 여유 있습니다. 피크인 21~24시를 피하면 원하는 시각에 잡힐 확률이 높습니다."),
            ("정기 예약(매주 같은 시간)도 되나요?", "네. 고정 요일·시간으로 반복 예약하는 고객이 늘고 있습니다. 상담 시 정기 운영을 요청해 주세요."),
            ("도착이 늦어지면 어떻게 안내되나요?", "교통 등으로 지연이 예상되면 즉시 연락드리며, 대기 또는 일정 변경을 선택하실 수 있습니다."),
            ("공휴일·명절에도 운영하나요?", "네. 연중무휴 원칙은 명절에도 동일합니다. 연휴 저녁은 문의가 몰려 사전 예약을 권합니다.")])

    content_page("/geumcheon-gu/checklist/", "geumcheon", gt + [(None, "이용 전 확인사항")],
        title="이용 전 확인사항 | 금천 출장마사지 방문 준비 안내",
        desc="금천 출장마사지 이용 전 확인사항 - 방문 장소 준비, 예약 정보, 결제 준비, 이용 시 주의사항을 안내합니다. 만 19세 이상 건강관리 서비스입니다.",
        eyebrow="금천 · 확인", h1="이용 전 확인사항",
        lead="원활한 방문을 위해 예약 전 아래 사항을 미리 확인해 주세요. 장소 유형별·상황별 체크리스트로 정리했습니다.",
        sections=[
            ("방문 장소 준비", [
                "편하게 누워 쉴 수 있는 공간을 확보해 주세요.",
                "정확한 주소와 출입 방법(공동현관 등), 주차 가능 여부를 알려주시면 도착이 빨라집니다."]),
            ("예약 정보 확인", [
                ("ul", ["연락 가능한 전화번호", "방문 장소 주소",
                        "희망 코스와 시간(60·90·120분)", "방문 희망 시각"])]),
            ("방문 장소별 안내", [
                ("h3", "자택·오피스텔"),
                "공동현관 출입 방법과 동·호수를 알려주시면 도착이 빨라집니다. 반려동물이 있다면 미리 안내해 주세요.",
                ("h3", "호텔·숙소"),
                "건물명과 객실 번호, 프런트 출입 안내가 필요한지 함께 알려주시면 원활합니다."]),
            ("결제 준비", [
                "코스별 정찰 요금을 사전에 안내드리며, 결제 방법은 예약 시 함께 확인합니다.",
                "변동 요소(지역·시간대 등)는 미리 고지해 드립니다."]),
            ("상황별 체크리스트", [
                ("h3", "첫 이용이라면"),
                "누울 공간, 연락처, 주소 — 이 세 가지면 충분합니다. 압 선호를 모르면 '중간으로 시작'이라고만 말해두세요. 전체 흐름은 <a href='/magazine/first-time-guide/'>처음 이용 가이드</a>에 있습니다.",
                ("h3", "커플·가족 동반이라면"),
                "두 사람이 나란히 누울 수 있는지 확인하고, 어려우면 순차 진행을 요청하세요. 관리사 2인 배정을 위해 1~2일 전 예약이 안전합니다.",
                ("h3", "기업·단체라면"),
                "인원·1인당 시간·장소(회의실 등)·콘센트 여부를 미리 정리해 주시면 견적이 빨라집니다."]),
            ("출입·주차 안내", [
                "공동현관 비밀번호는 예약 시 또는 도착 직전에 알려주셔도 됩니다. 보안이 엄격한 건물은 도착 시 전화 호출 방식이 가장 확실합니다.",
                "주차가 어려운 건물이라면 근처 공영주차장이나 정차 가능한 위치를 한 줄만 남겨주세요. 도착 지연을 막는 가장 효과적인 정보입니다."]),
            ("예약 당일 흐름 요약", [
                "예약 확정 → 출발 안내 연락 → 도착 → 압·부위 확인 → 관리 진행 → 공간 정돈·마무리. 이 여섯 단계가 전부입니다.",
                "고객이 할 일은 연락을 받을 수 있는 상태로 누울 자리만 비워두는 것뿐입니다. 나머지는 모두 관리사가 진행합니다."]),
            ("이용 시 주의사항", [
                "본 서비스는 의료 행위가 아닌 건강관리 서비스이며 <strong>만 19세 이상</strong> 성인을 대상으로 합니다.",
                "불법·퇴폐 행위 요구는 일절 제공되지 않으며, 요청 시 서비스가 중단될 수 있습니다.",
                "음주가 심한 경우 안전을 위해 관리가 어려울 수 있습니다."]),
        ],
        data_note="예약 시 주소와 출입 방법을 함께 남겨주시면 도착 시간이 평균적으로 단축됩니다. 공동현관 비밀번호 등은 도착 직전 안내해 주셔도 되며, 출입 정보가 정확한 예약일수록 시작 시각이 일정했습니다.",
        faq=[
            ("무엇을 준비하면 되나요?", "편히 쉴 공간과 연락 가능한 번호, 정확한 주소면 충분합니다."),
            ("출입은 어떻게 하나요?", "출입 방법을 미리 알려주시면 도착이 수월합니다. 필요한 안내는 상담 시 도와드립니다."),
            ("예약을 변경할 수 있나요?", "가능한 한 빠르게 연락 주시면 일정 변경을 도와드립니다."),
            ("반려동물이 있으면 미리 말해야 하나요?", "네. 알러지가 있는 관리사를 피해 배정할 수 있도록 예약 시 알려주시면 좋습니다. 관리 중에는 다른 공간 분리를 권합니다."),
            ("몸 상태(임신·질환)는 어디까지 알려야 하나요?", "임신, 관절·피부 질환, 복용 약 등 관리에 영향을 줄 수 있는 사항은 안전을 위해 꼭 알려주세요. 구성 조정에만 사용됩니다."),
            ("준비가 하나도 안 된 상태인데 가능할까요?", "네. 누울 자리만 있으면 됩니다. 수건·오일·매트 등 관리 용품은 전부 관리사가 가져갑니다."),
            ("엘리베이터 없는 건물인데 괜찮나요?", "네. 층수만 미리 알려주시면 도착 시간 안내에 반영합니다.")])

    content_page("/geumcheon-gu/safety/", "geumcheon", gt + [(None, "위생 및 안전 안내")],
        title="위생 및 안전 안내 | 금천 출장마사지 위생·안전 기준",
        desc="금천 출장마사지 위생 및 안전 안내 - 용품 위생 관리, 관리사·고객 안전 가이드라인, 비의료 서비스 고지, 개인정보 보호 원칙을 안내합니다.",
        eyebrow="금천 · 안전", h1="위생 및 안전 안내",
        lead="안심하고 받으실 수 있도록 위생과 안전을 운영의 기본 기준으로 둡니다. 용품 관리부터 응대 기준, 문제 발생 시 처리 절차까지 공개합니다.",
        sections=[
            ("위생 관리 기준", [
                "관리에 사용하는 수건·오일 등 용품은 위생 기준에 맞춰 관리합니다.",
                "수건은 1회 사용 후 교체를 원칙으로 하고, 오일 등 소모품은 적정 보관 상태를 확인해 사용합니다.",
                "방문 시 단정한 복장과 청결을 기본으로 하며, 관리 종료 후 사용한 공간을 정돈하고 마무리합니다."]),
            ("관리사·고객 안전", [
                "관리사와 고객 모두의 안전을 위한 운영 가이드라인을 준수합니다.",
                "상호 존중을 원칙으로 하며, 부적절한 요구가 있을 경우 관리가 중단될 수 있습니다."]),
            ("비의료 서비스 고지", [
                "본 서비스는 의료 행위가 아닌 <strong>이완·휴식 목적의 건강관리(마사지) 서비스</strong>입니다.",
                "질환의 진단·치료를 목적으로 하지 않으며, 통증·부상은 의료기관 진료를 권유드립니다."]),
            ("개인정보 보호", [
                "예약을 위해 수집한 연락처·주소 등은 예약 진행 목적으로만 이용하고, 목적 달성 후 관련 법령에 따라 파기합니다.",
                "자세한 내용은 <a href='/privacy/'>개인정보처리방침</a>에서 확인하실 수 있습니다."]),
            ("관리사 교육과 응대 기준", [
                "어느 관리사가 방문하더라도 같은 경험이 되도록 응대 가이드라인(도착 인사, 시작 전 확인, 진행 중 점검, 마무리 정돈)을 운영합니다.",
                "시작 전에는 압 세기와 집중 부위를 반드시 확인하고, 진행 중에도 압·온도·자세의 불편 여부를 살핍니다.",
                "고객 피드백은 운영 책임자가 직접 확인해 교육에 반영합니다. 같은 지적이 반복되지 않도록 하는 것이 기준입니다."]),
            ("문제가 생겼을 때의 처리 절차", [
                "서비스 중 불편이 있었다면 고객센터로 알려주세요. 운영 책임자가 사실 확인 후 직접 회신드립니다.",
                "확인 결과에 따라 재방문 조치 등 합리적인 보상 기준을 적용하며, 동일 문제 재발 방지 조치를 함께 안내드립니다.",
                "운영 주체와 책임자 정보는 <a href='/about/'>운영팀 소개</a>와 모든 페이지 하단에 공개되어 있습니다."]),
            ("고객님께 부탁드리는 점", [
                ("ul", ["만 19세 이상 본인 확인에 협조해 주세요.",
                        "관리사에 대한 존중과 기본 예의를 지켜주세요.",
                        "불법·퇴폐 행위 요구는 삼가주세요. 요청 시 서비스가 중단됩니다.",
                        "과도한 음주 상태에서는 안전을 위해 관리가 어려울 수 있습니다."])]),
        ],
        data_note="위생·안전은 운영의 기본 기준입니다. 관리사 교육과 응대 가이드라인으로 일관된 방문 경험을 유지하며, 고객 피드백은 운영 책임자가 직접 확인해 교육에 반영합니다.",
        faq=[
            ("위생은 어떻게 관리되나요?", "수건·오일 등 용품을 위생 기준에 맞춰 관리하고, 관리 후 공간을 정돈합니다."),
            ("안전은 어떻게 보장되나요?", "관리사·고객 모두의 안전을 위한 가이드라인을 운영하며 상호 존중을 원칙으로 합니다."),
            ("의료적 효과가 있나요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 치료를 보장하지 않습니다."),
            ("불편 사항은 어디에 말하나요?", "고객센터 번호로 알려주시면 운영 책임자가 직접 확인하고 회신드립니다."),
            ("관리사 정보는 미리 알 수 있나요?", "배정 확정 후 도착 안내와 함께 기본 정보를 알려드립니다. 특정 요청 사항은 예약 시 말씀해 주세요."),
            ("선물(대리 예약)도 가능한가요?", "네. 받는 분의 주소와 연락처만 알려주시면 됩니다. 부모님·배우자 선물 예약이 꾸준히 늘고 있습니다."),
            ("관리 중 불편하면 중단할 수 있나요?", "네. 언제든 중단·조정을 요청하실 수 있습니다. 고객과 관리사 모두 무리하지 않는 것이 안전 기준의 핵심입니다."),
            ("수건은 매번 새것을 쓰나요?", "네. 직접 닿는 용품은 1회 사용 후 교체를 원칙으로 합니다.")])

    content_page("/geumcheon-gu/faq/", "geumcheon", gt + [(None, "자주 묻는 질문")],
        title="금천 출장마사지 FAQ | 예약·지역·요금 자주 묻는 질문",
        desc="금천 출장마사지 자주 묻는 질문 - 방문 가능 지역, 예약 방법, 도착 시간, 테마·코스, 요금, 안전까지 자주 들어오는 질문을 한곳에 정리했습니다.",
        eyebrow="금천 · FAQ", h1="자주 묻는 질문",
        lead="예약·지역·시간·테마·코스·요금 등 자주 들어오는 질문을 한곳에 정리했습니다. 가장 많은 질문 TOP 3 해설부터 확인해 보세요.",
        sections=[
            ("질문을 모았습니다", [
                "이용 전 자주 들어오는 질문을 주제별로 정리했습니다.",
                "더 궁금한 점은 <a href='/customer/'>고객센터</a> 또는 전화로 언제든 문의해 주세요."]),
            ("예약·지역 한눈에", [
                ("h3", "어디까지 방문하나요"),
                "가산동·독산동·시흥동 등 금천구 전지역을 안내드립니다. 독산1~4동, 시흥1~5동은 대표 동 페이지에서 통합 안내합니다.",
                ("h3", "당일·심야 예약"),
                "상담은 24시간 가능하며, 시간대와 위치에 따라 방문 가능 시간을 안내드립니다."]),
            ("테마·코스·요금 한눈에", [
                ("h3", "어떤 관리가 있나요"),
                "스웨디시·로미로미·타이·아로마 등 테마와, 피로 회복·홈타이 등 코스를 운영합니다. 시간은 60·90·120분 기준입니다.",
                ("h3", "요금은 어떻게 안내되나요"),
                "코스별 정찰 요금을 사전에 안내하며, 지역·시간대 등 변동 요소는 예약 시 미리 알려드립니다."]),
            ("가장 많이 묻는 질문 TOP 3 해설", [
                ("h3", "1위 — \"지금 부르면 언제 도착하나요?\""),
                "지역 평균 24~32분이지만, 정답은 '위치를 알려주시면 바로 확인'입니다. 주소·역·건물 중 하나만 있으면 1분 내 답이 나옵니다.",
                ("h3", "2위 — \"얼마예요?\""),
                "60분 9만 원, 90분 14만 원, 120분 18만 원이 기본 기준입니다. 코스·시간대·인원에 따른 변동은 상담에서 먼저 고지합니다.",
                ("h3", "3위 — \"뭘 받아야 할지 모르겠어요\""),
                "오늘 컨디션 한 문장이면 됩니다. '몸이 무거워요' → 피로 회복, '굳었어요' → 홈타이, '신경이 곤두서요' → 아로마."]),
            ("안전·신뢰", [
                "본 서비스는 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며, 만 19세 이상 성인을 대상으로 합니다.",
                "위생·안전 가이드라인을 준수하며, 자세한 내용은 위생 및 안전 안내 페이지에서 확인하실 수 있습니다."]),
        ],
        data_note="가장 많이 들어오는 문의는 '도착까지 걸리는 시간'과 '코스·요금'입니다. 예약 시 위치와 희망 코스를 함께 알려주시면 빠르게 안내해 드립니다.",
        faq=[
            ("금천구 어디까지 방문 가능한가요?", "가산동·독산동·시흥동 등 금천구 전지역을 안내드립니다."),
            ("독산2동, 시흥4동처럼 숫자 동도 되나요?", "네. 숫자 행정동은 독산동·시흥동 대표 페이지 기준으로 통합 안내하며, 예약 시 정확한 주소로 확인해 드립니다."),
            ("예약은 어떻게 하나요?", "전화 또는 문의로 지역·시간·코스를 알려주시면 방문 가능 시간을 확정해 드립니다."),
            ("도착까지 얼마나 걸리나요?", "지역에 따라 평균 24~32분 내외이며, 시간대와 위치에 따라 달라질 수 있습니다."),
            ("당일·심야 예약이 가능한가요?", "상담은 24시간 가능합니다. 심야는 위치에 따라 도착 시간이 길어질 수 있습니다."),
            ("어떤 테마가 있나요?", "스웨디시·로미로미·타이마사지·중국마사지·아로마테라피 등 테마별 안내 페이지에서 확인하실 수 있습니다."),
            ("요금은 어떻게 되나요?", "코스별 정찰 요금을 사전에 안내드립니다. 자세한 금액은 가격 안내에서 확인하세요."),
            ("표시 요금 외 추가 비용이 있나요?", "정찰 요금을 원칙으로 하며 지역·시간대 등 변동 요소는 예약 시 미리 안내드립니다."),
            ("이 서비스는 의료 행위인가요?", "아닙니다. 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상을 대상으로 합니다."),
            ("정기적으로 받고 싶은데 방법이 있나요?", "고정 요일·시간의 정기 예약과 같은 관리사 우선 배정을 함께 요청하실 수 있습니다."),
            ("문의했는데 답이 늦으면 어떻게 하나요?", "상담이 몰리는 밤 시간대에는 문자 접수 후 순서대로 회신드립니다. 급한 예약은 전화 재시도가 가장 빠릅니다.")])


# ---- robots / sitemap / manifest / favicon --------------------------------------
def build_meta_files():
    urls = ["/", "/about/", "/geumcheon-gu/", "/geumcheon-gu/home-thai/", "/geumcheon-gu/coverage/",
            "/geumcheon-gu/area/", "/geumcheon-gu/stations/", "/themes/", "/course/",
            "/reservation/", "/guide/", "/reviews/", "/customer/",
            "/privacy/", "/terms/", "/youth/",
            "/geumcheon-gu/hours/", "/geumcheon-gu/checklist/",
            "/geumcheon-gu/safety/", "/geumcheon-gu/faq/"]
    urls += [f"/geumcheon-gu/{d['slug']}/" for d in DONGS]
    urls += [f"/geumcheon-gu/stations/{s['slug']}/" for s in STATIONS]
    urls += [f"/themes/{t['slug']}/" for t in THEMES]
    urls += [f"/course/{c['slug']}/" for c in COURSE_DETAIL]
    urls += ["/magazine/"] + [f"/magazine/{p['slug']}/" for p in POSTS]
    prio = {"/": "1.0", "/geumcheon-gu/": "0.9", "/geumcheon-gu/area/": "0.85",
            "/geumcheon-gu/stations/": "0.85", "/themes/": "0.85", "/course/": "0.85",
            "/magazine/": "0.8"}
    items = ""
    for u in urls:
        p = prio.get(u, "0.8" if u.count("/") <= 2 else "0.75")
        freq = "daily" if u == "/" else "weekly"
        items += (f"  <url><loc>{BASE_URL}{u}</loc>"
                  f"<changefreq>{freq}</changefreq><priority>{p}</priority></url>\n")
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + items + "</urlset>\n")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    robots = ("User-agent: *\nAllow: /\nDisallow: /tools/\n\n"
              "User-agent: GPTBot\nAllow: /\n"
              "User-agent: ClaudeBot\nAllow: /\n"
              "User-agent: Google-Extended\nAllow: /\n\n"
              f"Sitemap: {BASE_URL}/sitemap.xml\n"
              f"Host: {BASE_URL.replace('https://','')}\n")
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)

    manifest = {
        "name": BRAND, "short_name": BRAND_SHORT,
        "description": "서울 금천구 방문 마사지·홈타이 예약 안내",
        "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#0b0b0e", "theme_color": "#0b0b0e",
        "lang": "ko-KR", "orientation": "portrait",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    with open(os.path.join(ROOT, "site.webmanifest"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    favicon = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
               '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
               '<stop offset="0" stop-color="#f4d29c"/><stop offset=".5" stop-color="#e9b8a7"/>'
               '<stop offset="1" stop-color="#c98a6b"/></linearGradient></defs>'
               '<rect width="64" height="64" rx="16" fill="#0b0b0e"/>'
               '<rect x="8" y="8" width="48" height="48" rx="13" fill="url(#g)"/>'
               '<text x="32" y="44" font-family="Georgia,serif" font-style="italic" '
               'font-size="34" font-weight="700" text-anchor="middle" fill="#1a1208">V</text></svg>')
    with open(os.path.join(ROOT, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(favicon)

    # IndexNow 인증 키 파일 — https://<도메인>/<KEY>.txt 로 노출되어야 함
    with open(os.path.join(ROOT, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


# ---------------------------------------------------------------------------
def main():
    build_home()
    build_geumcheon()
    build_homethai()
    build_coverage()
    build_area_hub()
    build_dong_pages()
    build_stations_hub()
    build_station_pages()
    build_themes_hub()
    build_theme_pages()
    build_course_hub()
    build_course_pages()
    build_about()
    build_magazine_hub()
    build_magazine_posts()
    build_reservation()
    build_guide()
    build_reviews()
    build_customer()
    build_policies()
    build_info_pages()
    build_meta_files()
    print("Build complete.")


if __name__ == "__main__":
    main()
