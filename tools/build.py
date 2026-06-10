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
        ("코스·요금과 상세 안내", [
            "홈타이의 시간 구성과 요금 기준은 코스 전용 페이지에서 확인하실 수 있습니다.",
            ("ul", ['<a href="/course/home-thai/">홈타이 코스 상세</a>',
                    '<a href="/themes/thai-massage/">타이마사지 테마 안내</a>',
                    '<a href="/course/price/">가격 안내</a>',
                    '<a href="/geumcheon-gu/checklist/">이용 전 확인사항</a>'])]),
    ]
    content_page("/geumcheon-gu/home-thai/", "geumcheon", trail,
        title="금천 홈타이 안내 | 금천구 방문 타이마사지 예약",
        desc="금천 홈타이 안내 - 자택·숙소에서 받는 건식 타이마사지 방문 서비스입니다. 이용 흐름, 추천 대상, 코스·요금 링크를 안내합니다.",
        eyebrow="금천구 · 홈타이", h1="금천 홈타이 안내",
        lead="타이마사지를 금천구 자택·숙소에서 그대로 받는 홈타이 예약 안내입니다.",
        sections=sections, faq=ht_faq,
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
        ("방문 가능 여부 확인 방법", [
            "같은 동 안에서도 정확한 위치·예약 시간·배정 상황에 따라 가능 여부와 도착 시간이 달라집니다.",
            "예약 시 정확한 주소(또는 가까운 역·건물)를 알려주시면 방문 가능 여부와 예상 도착 시간을 바로 확인해 드립니다."]),
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
        content_page(path, "area", trail,
            title=f"{name} 출장마사지 | 금천구 {name} 방문 마사지 예약 안내",
            desc=f"금천구 {name} 출장마사지 안내 페이지입니다. {st_names} 인근 방문 가능 생활권과 평균 도착 시간, 관련 테마·코스를 확인해보세요.",
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
            desc=f"{name} 인근 출장마사지·홈타이 안내 페이지입니다. 역세권 생활권별 방문 안내와 평균 도착 시간, 주변 대표 동 정보를 확인해보세요.",
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


def build_theme_pages():
    tt = [("/", "홈"), ("/themes/", "테마별 안내")]
    for t in THEMES:
        content_page(f"/themes/{t['slug']}/", "themes", tt + [(None, t["name"])],
            title=f"{t['name']} | 금천 방문 관리 테마 안내",
            desc=f"금천 방문 관리 {t['name']} 테마 안내 - {t['short']} 특징과 추천 대상, 진행 방식, 예약 전 확인사항을 확인하세요.",
            eyebrow=t["kicker"], h1=f"{t['name']} 테마 안내",
            lead=t["lead"], sections=t["sections"], faq=t["faq"],
            data_note=t.get("data_note"),
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
            data_note=c.get("data_note"), show_price=c.get("show_price", False),
            service=c.get("service"),
            top_links=[("tel:" + PHONE_TEL, "예약문의", True),
                       ("/course/", "전체 코스"), ("/course/price/", "가격 안내")])


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
        "author": {"@type": "Organization", "name": BRAND, "url": BASE_URL + "/"},
        "publisher": {"@type": "Organization", "name": COMPANY["name"], "url": BASE_URL + "/"},
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
        '예약 상담에서 실제로 가장 많이 받는 질문들을 글로 정리했습니다.</p>'
        '<p class="sec-lead" style="max-width:820px;margin-top:12px">각 글에는 관련된 '
        '<a href="/geumcheon-gu/area/" style="color:var(--gold);font-weight:700">지역별 안내</a>, '
        '<a href="/geumcheon-gu/stations/" style="color:var(--gold);font-weight:700">지하철역별 안내</a>, '
        '<a href="/themes/" style="color:var(--gold);font-weight:700">테마별 안내</a> 페이지가 연결되어 있어 '
        '글을 읽다가 바로 상세 안내로 이동할 수 있습니다. 읽는 순서가 고민된다면 처음 이용 가이드 → 압 세기 고르는 법 → '
        '관심 있는 테마 비교 순서를 권합니다.</p>'
        f'<div class="grid g3" style="margin-top:28px">{cards}</div>'
        '<div class="data-box" style="max-width:820px;margin-top:30px"><b>편집 기준</b>'
        '<p>매거진의 모든 글은 검색을 위한 키워드 나열이 아니라, 실제 예약 상담에서 반복되는 질문과 예약 데이터에서 보이는 '
        '이용 패턴을 바탕으로 작성합니다. 지역·역·테마를 조합한 중복성 글은 만들지 않으며, 글당 한 가지 주제를 깊이 있게 다룹니다.</p></div>'
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
    notes = [
        ("예약 방법", ["전화 또는 문의로 지역(또는 역 인근 위치)·희망 시간·코스를 말씀해 주세요.",
                     "상담 후 방문 가능 시간을 확정해 안내드립니다."]),
        ("예약 가능 시간", ["연중무휴 24시간 상담을 운영합니다.", "방문 가능 시간은 시간대와 위치에 따라 안내드립니다."]),
        ("방문 가능 장소", ["자택, 오피스텔, 호텔·숙소 등 방문 가능한 장소와 주소를 알려주세요."]),
        ("결제 안내", ["코스별 정찰 요금을 사전에 안내드리며, 결제 방법은 예약 시 함께 안내합니다."]),
        ("예약 변경·취소", ["일정 변경이나 취소는 가능한 한 빠르게 연락 주시면 도와드립니다."]),
        ("예약 전 체크사항", ["방문 장소·연락처·희망 코스·시간을 미리 정리해 두시면 빠르게 진행됩니다."]),
    ]
    res_faq = [
        ("당일 예약이 가능한가요?", "가능합니다. 다만 저녁·주말은 문의가 몰릴 수 있어 사전 예약을 권장드립니다."),
        ("예약을 변경하고 싶어요.", "확정된 일정 변경은 가능한 한 빠르게 연락 주시면 조정을 도와드립니다."),
        ("결제는 어떻게 하나요?", "정찰 요금을 사전에 안내드리며 결제 방법은 예약 시 함께 안내합니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block" style="padding-bottom:0"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>RESERVATION</span>'
        '<h2 class="sec">예약안내</h2>'
        '<p class="sec-lead">예약 방법부터 결제·변경까지 한눈에 안내드립니다.</p>'
        '</div></section>' +
        notes_block("HOW TO BOOK", "예약 진행 안내", "아래 순서대로 진행됩니다.", notes, _id="steps") +
        faq_block(res_faq) + cta_band())
    html = page("/reservation/", "예약안내 | 금천 출장마사지 예약 방법·결제 안내",
        "금천 출장마사지 예약안내 - 예약 방법, 예약 가능 시간, 방문 가능 장소, 결제와 변경·취소 안내를 제공합니다. 연중무휴 24시간 상담.",
        "reservation", body, [bc_ld(trail), faq_ld(res_faq)])
    write("/reservation/", html)


def build_guide():
    trail = [("/", "홈"), (None, "이용가이드")]
    notes = [
        ("처음 이용하시는 분", ["예약 시 지역·시간·코스만 말씀해 주시면 나머지는 안내해 드립니다."]),
        ("방문 전 준비사항", ["편하게 쉴 수 있는 공간과 연락 가능한 번호를 준비해 주세요."]),
        ("위생 및 안전 기준", ["용품 위생 관리와 안전 가이드라인을 준수합니다."]),
        ("관리 후 주의사항", ["관리 후에는 충분한 수분 섭취와 휴식을 권장드립니다."]),
        ("금지행위 안내", ["불법·퇴폐 행위 요구는 일절 제공하지 않으며, 요청 시 서비스가 중단될 수 있습니다."]),
    ]
    guide_faq = [
        ("처음인데 무엇을 준비하나요?", "편히 쉴 수 있는 공간과 연락 가능한 번호만 있으면 됩니다."),
        ("관리 후 주의할 점이 있나요?", "충분한 수분 섭취와 휴식을 권장드립니다."),
        ("이 서비스는 의료 행위인가요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상을 대상으로 합니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block" style="padding-bottom:0"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>GUIDE</span>'
        '<h2 class="sec">이용가이드</h2>'
        '<p class="sec-lead">처음 이용하시는 분도 안심할 수 있도록 안내드립니다.</p>'
        '</div></section>' +
        notes_block("USER GUIDE", "이용 안내", "방문 전후 확인하세요.", notes, _id="steps") +
        faq_block(guide_faq) + cta_band())
    html = page("/guide/", "이용가이드 | 금천 출장마사지 방문 전 준비·주의사항",
        "금천 출장마사지 이용가이드 - 처음 이용하시는 분을 위한 방문 전 준비사항, 위생·안전 기준, 관리 후 주의사항과 금지행위 안내입니다.",
        "guide", body, [bc_ld(trail), faq_ld(guide_faq)])
    write("/guide/", html)


# ---- 후기 ---------------------------------------------------------------------
def build_reviews():
    trail = [("/", "홈"), (None, "후기")]
    region_reviews = [
        ("가산동 · 30대", "홈타이", "야근 끝나고 오피스텔로 와주셨는데 도착 안내가 정확했습니다."),
        ("독산동 · 40대", "피로회복", "예약부터 마무리까지 깔끔했고 위생 안내가 꼼꼼했습니다."),
        ("시흥동 · 30대", "아로마", "주말 저녁에 받았는데 응대가 정중하고 편안했어요."),
    ]
    station_reviews = [
        ("가산디지털단지역 인근 · 30대", "스웨디시", "환승하고 숙소 도착할 때쯤 맞춰 와주셔서 좋았습니다."),
        ("독산역 인근 · 40대", "스포츠", "운동 후 받았는데 컨디션이 한결 가벼워졌어요."),
        ("금천구청역 인근 · 50대", "발마사지", "도착 시간을 미리 알려주셔서 기다림이 없었습니다."),
    ]
    def cards(rows):
        return "".join(
            f'<div class="review reveal"><div class="stars">★★★★★</div>'
            f'<p>“{q}”</p><div class="who">{w} · {c} 이용</div></div>' for w, c, q in rows)
    body = (breadcrumb(trail) +
        '<section class="block" id="all" style="padding-bottom:30px"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>REVIEWS</span>'
        '<h2 class="sec">전체 후기</h2>'
        '<p class="sec-lead">이용하신 고객들의 후기입니다. 후기는 실제 이용 고객의 동의 하에 게시되며, 개인을 특정할 수 있는 정보는 표시하지 않습니다.</p>'
        f'<h3 id="region" style="font-size:20px;font-weight:800;margin:38px 0 14px"><span class="grad">지역별 후기</span></h3>'
        f'<div class="grid g3">{cards(region_reviews)}</div>'
        f'<h3 id="station" style="font-size:20px;font-weight:800;margin:38px 0 14px"><span class="grad">역세권 후기</span></h3>'
        f'<div class="grid g3">{cards(station_reviews)}</div>'
        '<div class="data-box" id="write" style="max-width:820px;margin-top:38px"><b>후기 작성 안내</b>'
        '<p>이용 후 문자 또는 전화로 후기를 남겨주시면 동의를 받아 게시합니다. 개인정보(이름·연락처·상세 주소)는 게시하지 않으며, '
        '게시된 후기의 수정·삭제는 고객센터로 요청해 주세요.</p></div>'
        '</div></section>' + cta_band())
    html = page("/reviews/", "후기 | 금천 출장마사지 이용 후기",
        "금천 출장마사지 이용 후기 - 가산동·독산동·시흥동 지역별 후기와 역세권 후기, 후기 작성 안내를 확인하세요.",
        "reviews", body, [bc_ld(trail)])
    write("/reviews/", html)


# ---- 고객센터 / 정책 ------------------------------------------------------------
def build_customer():
    trail = [("/", "홈"), (None, "고객센터")]
    notes = [
        ("공지사항", ["서비스 운영과 관련된 안내를 이곳에 게시합니다."]),
        ("1:1 문의", [f"전화 {PHONE_DISP}로 문의해 주세요. 연중무휴 24시간 상담을 운영합니다."]),
        ("제휴·기업 문의", ["기업·단체 방문 관리 및 제휴 문의도 전화로 접수받습니다."]),
    ]
    cust_faq = [
        ("문의는 어디로 하나요?", f"전화 {PHONE_DISP}로 문의하실 수 있습니다. 연중무휴 24시간 상담을 운영합니다."),
        ("운영 시간이 어떻게 되나요?", "연중무휴 24시간 상담을 운영합니다."),
        ("개인정보는 어떻게 관리되나요?", "개인정보처리방침에 따라 안전하게 관리되며, 자세한 내용은 해당 페이지에서 확인하실 수 있습니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block" id="notice" style="padding-bottom:0"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>CUSTOMER</span>'
        '<h2 class="sec">고객센터</h2>'
        f'<p class="sec-lead">전화 {PHONE_DISP} · {HOURS}</p>'
        '</div></section>' +
        notes_block("HELP", "문의 안내", "궁금한 점은 언제든 문의해 주세요.", notes, _id="inquiry") +
        '<div class="wrap" id="partner"></div>' +
        faq_block(cust_faq) + cta_band())
    html = page("/customer/", "고객센터 | 금천 VIP 마사지 문의·공지",
        "금천 VIP 마사지 고객센터 - 공지사항, 자주 묻는 질문, 1:1 문의, 제휴·기업 문의 안내입니다. 연중무휴 24시간 상담.",
        "customer", body, [bc_ld(trail), faq_ld(cust_faq)])
    write("/customer/", html)


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
        [("수집하는 개인정보", ["예약 진행을 위해 연락처, 방문 장소 등 최소한의 정보를 수집합니다."]),
         ("이용 목적", ["수집한 정보는 예약 확정과 방문 안내 목적으로만 이용합니다."]),
         ("보유 및 파기", ["목적 달성 후에는 관련 법령에 따라 지체 없이 파기합니다."]),
         ("개인정보보호책임자", [f"{COMPANY['privacy_officer']} · 전화 {PHONE_DISP}"])],
        "금천 VIP 마사지 개인정보처리방침 - 수집 항목, 이용 목적, 보유 및 파기, 개인정보보호책임자 안내입니다.")
    policy_page("/terms/", "이용약관 | 금천 VIP 마사지", "이용약관",
        [("목적", ["본 약관은 금천 VIP 마사지 예약 서비스 이용 조건을 규정합니다."]),
         ("서비스 내용", ["본 서비스는 의료 행위가 아닌 이완·휴식 목적의 방문 건강관리 예약 서비스입니다."]),
         ("이용 자격", ["본 서비스는 만 19세 이상 성인만 이용할 수 있습니다."]),
         ("금지행위", ["불법·퇴폐 행위 요구 등은 금지되며, 위반 시 서비스가 중단될 수 있습니다."])],
        "금천 VIP 마사지 이용약관 - 서비스 내용, 이용 자격, 금지행위 등 이용 조건을 안내합니다.")
    policy_page("/youth/", "청소년보호정책 | 금천 VIP 마사지", "청소년보호정책",
        [("청소년 이용 제한", ["본 서비스는 만 19세 이상 성인을 대상으로 하며 청소년은 이용할 수 없습니다."]),
         ("건전한 운영", ["불법·퇴폐 행위를 일절 제공하지 않으며 건전한 건강관리 서비스를 지향합니다."]),
         ("책임자", [f"청소년보호 책임자 · {COMPANY['privacy_officer']} · 전화 {PHONE_DISP}"])],
        "금천 VIP 마사지 청소년보호정책 - 만 19세 이상 이용 제한과 건전한 운영 원칙을 안내합니다.")


# ---- 금천 공통 정보 페이지 (링크아웃 대상) ---------------------------------------
def build_info_pages():
    gt = [("/", "홈"), ("/geumcheon-gu/", "금천 출장마사지")]

    content_page("/geumcheon-gu/hours/", "geumcheon", gt + [(None, "예약 가능 시간")],
        title="예약 가능 시간 | 금천 출장마사지 24시간 상담·도착 안내",
        desc="금천 출장마사지 예약 가능 시간 안내 - 연중무휴 24시간 상담, 시간대별 특징, 지역별 평균 도착 시간, 예약 팁을 제공합니다.",
        eyebrow="금천 · 시간", h1="예약 가능 시간",
        lead="연중무휴 24시간 예약 상담을 운영합니다. 실제 방문 가능 시간은 시간대와 위치에 따라 안내드립니다.",
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
            ("도착 시간을 줄이는 방법", [
                "예약 시 정확한 주소와 공동현관·동·호수 등 출입 정보를 함께 알려주세요.",
                "가까운 지하철역이나 큰 건물 등 기준점을 알려주시면 위치 파악이 빨라집니다."]),
            ("예약 변경·취소", [
                "일정이 바뀌면 가능한 한 빠르게 연락 주세요. 빠를수록 다른 시간으로 조율하기 쉽습니다."]),
        ],
        data_note="지역 평균 도착 시간(예약 데이터 기준): 가산동 25분, 독산동 27분, 시흥동 30분 내외. 역세권 기준은 각 역 페이지에서 안내합니다.",
        faq=[
            ("새벽에도 예약되나요?", "상담은 24시간 가능합니다. 심야는 위치에 따라 도착 시간이 길어질 수 있어 상담 시 안내드립니다."),
            ("도착까지 얼마나 걸리나요?", "지역에 따라 평균 24~32분 내외이며, 시간대와 위치에 따라 달라집니다."),
            ("당일 예약이 가능한가요?", "가능합니다. 저녁·주말은 문의가 몰릴 수 있어 사전 예약을 권장드립니다.")])

    content_page("/geumcheon-gu/checklist/", "geumcheon", gt + [(None, "이용 전 확인사항")],
        title="이용 전 확인사항 | 금천 출장마사지 방문 준비 안내",
        desc="금천 출장마사지 이용 전 확인사항 - 방문 장소 준비, 예약 정보, 결제 준비, 이용 시 주의사항을 안내합니다. 만 19세 이상 건강관리 서비스입니다.",
        eyebrow="금천 · 확인", h1="이용 전 확인사항",
        lead="원활한 방문을 위해 예약 전 아래 사항을 미리 확인해 주세요.",
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
            ("이용 시 주의사항", [
                "본 서비스는 의료 행위가 아닌 건강관리 서비스이며 <strong>만 19세 이상</strong> 성인을 대상으로 합니다.",
                "불법·퇴폐 행위 요구는 일절 제공되지 않으며, 요청 시 서비스가 중단될 수 있습니다.",
                "음주가 심한 경우 안전을 위해 관리가 어려울 수 있습니다."]),
        ],
        data_note="예약 시 주소와 출입 방법을 함께 남겨주시면 도착 시간이 평균적으로 단축됩니다. 공동현관 비밀번호 등은 도착 직전 안내해 주셔도 됩니다.",
        faq=[
            ("무엇을 준비하면 되나요?", "편히 쉴 공간과 연락 가능한 번호, 정확한 주소면 충분합니다."),
            ("출입은 어떻게 하나요?", "출입 방법을 미리 알려주시면 도착이 수월합니다. 필요한 안내는 상담 시 도와드립니다."),
            ("예약을 변경할 수 있나요?", "가능한 한 빠르게 연락 주시면 일정 변경을 도와드립니다.")])

    content_page("/geumcheon-gu/safety/", "geumcheon", gt + [(None, "위생 및 안전 안내")],
        title="위생 및 안전 안내 | 금천 출장마사지 위생·안전 기준",
        desc="금천 출장마사지 위생 및 안전 안내 - 용품 위생 관리, 관리사·고객 안전 가이드라인, 비의료 서비스 고지, 개인정보 보호 원칙을 안내합니다.",
        eyebrow="금천 · 안전", h1="위생 및 안전 안내",
        lead="안심하고 받으실 수 있도록 위생과 안전을 운영의 기본 기준으로 둡니다.",
        sections=[
            ("위생 관리 기준", [
                "관리에 사용하는 수건·오일 등 용품은 위생 기준에 맞춰 관리합니다.",
                "방문 시 청결을 우선하며, 관리 종료 후 사용한 공간을 정돈합니다."]),
            ("관리사·고객 안전", [
                "관리사와 고객 모두의 안전을 위한 운영 가이드라인을 준수합니다.",
                "상호 존중을 원칙으로 하며, 부적절한 요구가 있을 경우 관리가 중단될 수 있습니다."]),
            ("비의료 서비스 고지", [
                "본 서비스는 의료 행위가 아닌 <strong>이완·휴식 목적의 건강관리(마사지) 서비스</strong>입니다.",
                "질환의 진단·치료를 목적으로 하지 않으며, 통증·부상은 의료기관 진료를 권유드립니다."]),
            ("개인정보 보호", [
                "예약을 위해 수집한 연락처·주소 등은 예약 진행 목적으로만 이용하고, 목적 달성 후 관련 법령에 따라 파기합니다.",
                "자세한 내용은 <a href='/privacy/'>개인정보처리방침</a>에서 확인하실 수 있습니다."]),
            ("고객님께 부탁드리는 점", [
                ("ul", ["만 19세 이상 본인 확인에 협조해 주세요.",
                        "관리사에 대한 존중과 기본 예의를 지켜주세요.",
                        "불법·퇴폐 행위 요구는 삼가주세요. 요청 시 서비스가 중단됩니다.",
                        "과도한 음주 상태에서는 안전을 위해 관리가 어려울 수 있습니다."])]),
        ],
        data_note="위생·안전은 운영의 기본 기준입니다. 관리사 교육과 응대 가이드라인으로 일관된 방문 경험을 유지합니다.",
        faq=[
            ("위생은 어떻게 관리되나요?", "수건·오일 등 용품을 위생 기준에 맞춰 관리하고, 관리 후 공간을 정돈합니다."),
            ("안전은 어떻게 보장되나요?", "관리사·고객 모두의 안전을 위한 가이드라인을 운영하며 상호 존중을 원칙으로 합니다."),
            ("의료적 효과가 있나요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 치료를 보장하지 않습니다.")])

    content_page("/geumcheon-gu/faq/", "geumcheon", gt + [(None, "자주 묻는 질문")],
        title="금천 출장마사지 FAQ | 예약·지역·요금 자주 묻는 질문",
        desc="금천 출장마사지 자주 묻는 질문 - 방문 가능 지역, 예약 방법, 도착 시간, 테마·코스, 요금, 안전까지 자주 들어오는 질문을 한곳에 정리했습니다.",
        eyebrow="금천 · FAQ", h1="자주 묻는 질문",
        lead="예약·지역·시간·테마·코스·요금 등 자주 들어오는 질문을 한곳에 정리했습니다.",
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
            ("이 서비스는 의료 행위인가요?", "아닙니다. 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상을 대상으로 합니다.")])


# ---- robots / sitemap / manifest / favicon --------------------------------------
def build_meta_files():
    urls = ["/", "/geumcheon-gu/", "/geumcheon-gu/home-thai/", "/geumcheon-gu/coverage/",
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
