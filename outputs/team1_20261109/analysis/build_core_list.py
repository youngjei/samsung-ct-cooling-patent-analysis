"""팀원2 반환용 미국 핵심특허 목록.
규칙: (1) Lens 등록특허(Granted Patent)만 (2) 같은 simple family는 1건 (3) 연평균 피인용 = 피인용 수 / 등록 공보 후 경과연수(최소 1년), 조회일 2026-11-09
(4) 최근 특허가 불리하지 않도록 출원연도 2개 층(2000–2016 / 2017–2024)에서 각 5건 (5) 초록 기준 관련성 확인, 경계 사례는 제외하고 기록."""
import re, pandas as pd
ASOF = pd.Timestamp('2026-11-09')
# 초록·청구항 확인으로 제외한 경계 사례 (번호: 이유)
EXCLUDE = {
    'US 6775137 B2': '랙 측면 공기-액체 열교환기로 공기를 식히는 방식. 칩·부품에 냉각액을 직접 보내는 DLC가 아니어서 경계 사례로 제외',
    'US 11516943 B2': '초록상 저장조(reservoir)에 랙을 넣는 구조로 액침과 경계. DLC 표본에서 제외',
    'US 9101078 B2': '공기측 이코노마이저 + 액냉 랙(DLC 계열). 액침 검색에 함께 걸렸으나 액침 기술이 아니어서 액침 표본에서 제외',
}
REASON = {  # 초록에서 확인한 기술 내용 (관련성 근거)
    'US 7318322 B2': '랙마운트 서버의 CPU 등 발열부품을 순환 냉각액으로 냉각',
    'US 6973801 B1': '랙 단위 냉각액 분배장치(CDU)와 폐루프 냉각, 미세 냉각구조',
    'US 7757506 B2': '모듈형 냉각유닛(MCU)이 서버 냉각판과 공기-액체 열교환기에 냉각액 병렬 공급 (청구항 1 확인)',
    'US 8583290 B2': '서버별 유량 제어기와 펌프 압력 제어로 냉각판 액냉 랙의 펌프 전력 절감',
    'US 7639499 B1': '랙 단위 냉각액 매니폴드와 이동식 섀시 단위 연결부',
    'US 10225958 B1': '랙 내 공급 매니폴드에 펌프를 내장한 데이터센터 액냉 시스템',
    'US 10917998 B2': '랙 정보처리시스템의 모듈형 액체 분배(MLD) 배관',
    'US 11129292 B1': '액냉 서버용 유체 커넥터: 커넥터 몸체와 수·암 인터페이스로 냉각액 연결',
    'US 10701838 B1': '랙 액냉 매니폴드에 서버를 꽂으면 자동 연결되는 커넥터',
    'US 11019752 B2': '서버용 냉각 모듈: 냉각액 공급·회수 채널이 있는 베이스 프레임과 냉각판',
    'US 10548240 B1': '서버 트레이의 마더보드에 장착하는 액체 냉각판(cold plate) 조립체',
    'US 7905106 B2': '여러 서버 케이스를 랙에 연결해 병렬로 냉각하는 액체 침지(submersion) 시스템',
    'US 8351206 B2': '침지 냉각 서버 서브시스템 + 수직형 증기 응축 유닛 (2상 액침)',
    'US 8184436 B2': '침지 냉각 서버 서브시스템 + 유전체 증기 응축 열교환기 (2상 액침)',
    'US 9049800 B2': '유전체 냉각액을 담은 랙 장착형 침지 서버 서랍',
    'US 9622379 B1': '서랍 단위 침지 냉각 인클로저 + 힌지형 액냉 방열판',
    'US 10939581 B1': '슬라이드 레일로 꺼낼 수 있는 침지 냉각 탱크 랙',
    'US 10925188 B1': '유전체 냉각액을 담은 밀폐형 침지 서버 조립체',
    'US 11006547 B2': '침지 탱크·열교환기·공급라인으로 구성된 데이터센터 침지 냉각과 유체 관리',
    'US 11076508 B2': '냉각액에 일부 잠긴 IT 장비 냉각 모듈과 외부 냉각 연결',
    'US 11665863 B2': '랙 트레이에 들어가는 밀폐형 침지 냉각 컴퓨팅 모듈',
    'US 9992914 B2': '유전체 냉각액 탱크에 랙 서버를 넣고 펌프로 유속 증강·부분 재순환',
}
# 원문(청구항 1)까지 직접 확인한 건. 나머지는 Lens 서지·초록으로 확인 (팀원2 근거표의 basis 열과 같은 방식)
G = 'Google Patents, 2026-11-09'
VERIFIED = {  # 원문 확인 결과: 기술 유형·청구항 1·권리자·상태·우선일 (상태 미표시 출처는 Lens 상태 유지)
    'US 7318322 B2': f'원문 확인({G}): 청구항 1 = 서버 모듈 발열부품을 순환 냉각액으로 냉각(DLC). 상태 Expired - Lifetime. 원 권리자 Hitachi, 현 권리자 Maxell',
    'US 6973801 B1': f'원문 확인({G}): 청구항 1 = 랙 CDU + 서브시스템 내 별도 냉각 루프(DLC). 상태 Expired - Lifetime(2025-01-10). 우선일 일치. 현 권리자 Lenovo',
    'US 7757506 B2': '원문 확인(Justia, 2026-11-08): 청구항 1 = MCU가 냉각판·열교환기에 냉각액 병렬 공급(DLC)',
    'US 8583290 B2': '원문 확인(Google Patents, 2026-11-08): 청구항 1 = 유량 제어기·펌프 압력 제어(DLC)',
    'US 7639499 B1': '원문 확인(uspto.report, 2026-11-09): 청구항 1 = 랙 매니폴드 → 섀시 매니폴드 → 냉각판(DLC). 출원일·권리자 일치. 상태는 출처에 없어 Lens 표기 유지',
    'US 10225958 B1': f'원문 확인({G}): 청구항 1 = 펌프 내장 공급·회수 매니폴드, 서버 냉각판(DLC). Active. 우선일 일치',
    'US 10701838 B1': f'원문 확인({G}): 청구항 1 = 랙 공급·회수 라인에 자동 결합되는 냉각액 커넥터(DLC). Active. 우선일 일치',
    'US 11019752 B2': f'원문 확인({G}): 청구항 1 = 공급·회수 채널과 냉각판 일체형 냉각 모듈(DLC). Active',
    'US 10548240 B1': f'원문 확인({G}): 청구항 1 = 서버 트레이 액체 냉각판과 유로 분배기(DLC). Active. 우선일 일치',
    'US 11129292 B1': f'원문 확인({G}): 청구항 1 = 수·암 커플링을 가진 유체 커넥터(DLC). Active. 우선일 일치',
    'US 7905106 B2': '원문 확인(Justia, 2026-11-09): 청구항 1 = 유전체 냉각액에 서버 보드를 담근 케이스를 랙에 연결(액침). 우선일 2008-04-21 일치',
    'US 8351206 B2': f'원문 확인({G}): 서브시스템을 유전체 유체에 침지 + 수직 증기 응축 유닛(2상 액침). Expired - Fee Related. 우선일 일치',
    'US 8184436 B2': f'원문 확인({G}): 서브시스템을 유전체 유체에 침지 + 증기 응축 열교환기(2상 액침). Expired - Fee Related. 현 권리자 Lenovo',
    'US 9049800 B2': '원문 확인(uspto.report 공개본, 2026-11-09): 청구항 1 = 냉각액을 담은 침지 서버 서랍(액침, HDD는 액면 위). 출원일·권리자 일치. 상태는 Lens 표기 유지',
    'US 9622379 B1': f'원문 확인({G}): 청구항 1 = 서랍 단위 인클로저에 유전체 액체로 부품 침지 + 힌지형 액냉 방열판(액침). Active. 우선일 일치',
    'US 10939581 B1': f'원문 확인({G}): 청구항 1 = 슬라이드 레일·바퀴 지지 구조의 냉각액 탱크 랙(액침). Active. 우선일 일치',
    'US 10925188 B1': '원문 확인(uspto.report, 2026-11-09): 청구항 1 = 유전체 냉각액이 부품을 잠기게 하는 밀폐 서버 + 내부 응축 코일(2상 액침). 출원일·권리자 일치. 상태는 Lens 표기 유지',
    'US 11006547 B2': '원문 확인(Justia, 2026-11-09): 청구항 1 = 침지 탱크·열교환기·구획별 하부 공급/상부 회수(액침). 출원일·권리자 일치. 상태는 Lens 표기 유지',
    'US 11076508 B2': f'원문 확인({G}): 냉각액에 일부 잠긴 IT 모듈 + 응축기·어큐뮬레이터(액침, 초록 기준). Active. 우선일 일치',
    'US 11665863 B2': f'원문 확인({G}): 밀폐 모듈 안 부품을 침지 유체가 둘러쌈(액침, 초록 기준). Active. 현 권리자 표기 Credit Suisse는 담보권 기록으로 보임, 원 권리자 Dell',
}
def current_owner(owners):
    items = []
    for x in str(owners).split(';;'):
        m = re.match(r'\s*(.+?)\s*\((\d{4}-\d{2}-\d{2})\)\s*$', x)
        if m:
            items.append((m.group(2), m.group(1)))
    return max(items)[1] if items else ''
def gp(key):
    return re.sub(r'[^A-Za-z0-9]', '', str(key))
rows, excl, ref = [], [], []
BUILD = ('E04B', 'E04F', 'E04H', 'F24F')  # 건축 구조·건물(E04B/F/H), 공조(F24F). E04G(비계·거푸집)는 제외
for tech, t in [('DLC', 'dlc'), ('Immersion', 'imm')]:
    raw = pd.read_csv(f'../raw/us_{t}_grant.csv')
    pre_map = raw[raw['Kind'].isin(['A1', 'A9'])].groupby('Application Number')['Display Key'].apply(lambda s: '; '.join(sorted(set(s)))).to_dict()
    g = pd.read_csv(f'../clean/us_{t}_granted.csv')
    g['years_since_grant'] = ((ASOF - pd.to_datetime(g['Publication Date'])).dt.days / 365.25).clip(lower=1)
    g['annual_citations'] = g['Cited by Patent Count'] / g['years_since_grant']
    g['family_key'] = g['Simple Family Members'].fillna(g['Display Key']).apply(lambda s: ';;'.join(sorted(str(s).split(';;'))))
    g = g.sort_values('annual_citations', ascending=False).drop_duplicates('family_key')
    g['filing_year'] = pd.to_datetime(g['Earliest Priority Date']).dt.year  # 최우선연도 기준 층화
    rank = 0
    for era, m in [('최우선 2000–2016', g['filing_year'] <= 2016), ('최우선 2017–2024', g['filing_year'] >= 2017)]:
        picked, era_rank = 0, 0
        for _, r in g[m].iterrows():
            era_rank += 1
            key = r['Display Key']
            if key in EXCLUDE:
                excl.append({'technology': tech, 'stratum': era, 'stratum_rank_by_metric': era_rank, 'grant_number': key,
                             'title': r['Title'], 'annual_citations': round(r['annual_citations'], 2), 'exclusion_reason': EXCLUDE[key]})
                continue
            if picked == 5:
                if tech == 'Immersion' and key == 'US 9992914 B2':
                    ref.append(r)
                if era_rank > 12:
                    break
                continue
            picked += 1; rank += 1
            fam = str(r['Simple Family Members']).split(';;')
            cpcs = [c.strip() for c in str(r['CPC Classifications']).split(';;') if c.strip()]
            bl = [c for c in cpcs if c.startswith(BUILD)]
            rows.append({
                'technology': tech, 'rank': rank, 'stratum': era,
                'application_number': r['Application Number'],
                'publication_number': pre_map.get(r['Application Number'], '(이 export에 등록 전 공개본 없음: B1은 공개 없이 등록되는 경우가 많음)'),
                'grant_number': key, 'claims_to_read': '등록본(' + key.split()[-1] + ') 청구항',
                'family_id': 'Lens simple family 구성원 Lens ID: ' + '; '.join(fam),
                'dedup_rule': '같은 simple family 중 연평균 피인용이 가장 높은 등록특허 1건만 남김',
                'title': r['Title'], 'applicant_raw': r['Applicants'], 'applicant_normalized': r['applicant_normalized'],
                'filing_date': r['Application Date'], 'priority_date': r['Earliest Priority Date'],
                'legal_status': r['Legal Status'], 'status_checked_at': '2026-11-09 Lens export(출원일 기준), 2026-11-08~09 원문 대조 (check_basis 참고)',
                'source_url': r['URL'], 'claims_url': f"https://patents.google.com/patent/{gp(key)}/en#claims",
                'selection_metric': f"연평균 피인용 {r['annual_citations']:.2f} = 피인용 {int(r['Cited by Patent Count'])}건 / 등록 후 {r['years_since_grant']:.1f}년",
                'selection_reason': f"{era} 층 연평균 피인용 {picked}위(관련성 확인 후). {REASON.get(key, '')}",
                'current_owner': current_owner(r['Owners']) + ' (Lens Owners 최신 기록)',
                'check_basis': VERIFIED.get(key, 'Lens 서지·초록 확인 (원문 청구항 확인 예정)'),
                'building_link': 'Y' if bl else 'N',
                'building_link_reason': ('CPC ' + ', '.join(bl)) if bl else 'E04B·E04F·E04H(건물)·F24F(공조) 분류 없음. 청구항 기준 판정은 미실시',
            })
out = pd.DataFrame(rows)
crit = pd.DataFrame({'항목': ['데이터', '조회일', '대상', '중복 처리', '지표', '층화', '관련성', '건수', '주의'],
    '내용': ['Lens.org 미국 특허, 검색식 A(DLC)/B(액침), 출원 2000-01-01~2024-12-31',
             '2026-11-09 (Lens export, 출원일 Filed 필터)',
             '등록특허(Document Type = Granted Patent)만. 등록 전 출원은 피인용이 덜 쌓여 제외',
             '같은 simple family는 1건 (연평균 피인용 최고)',
             '연평균 피인용 = Cited by Patent Count / 등록 공보 후 경과연수(최소 1년)',
             '최근 특허가 불리하지 않도록 최우선연도(처음 출원한 해) 2000–2016 / 2017–2024 두 층에서 각 5건',
             '초록으로 데이터센터·서버 냉각 여부와 기술 유형(DLC/액침) 확인. 경계 사례는 제외 시트에 기록. 일부는 청구항 1까지 확인',
             f"DLC {len(out[out.technology=='DLC'])}건, 액침 {len(out[out.technology=='Immersion'])}건",
             '피인용은 영향력의 대리지표다. 법적 상태는 Lens 표기이며 침해·FTO 판단이 아니다']})
with pd.ExcelWriter('../handoff/US_핵심특허_팀원2반환.xlsx') as w:
    out.to_excel(w, sheet_name='핵심특허', index=False)
    crit.to_excel(w, sheet_name='선정기준', index=False)
    pd.DataFrame(excl).to_excel(w, sheet_name='제외한 경계사례', index=False)
    if ref:
        r = ref[0]
        pd.DataFrame([{'grant_number': r['Display Key'], 'title': r['Title'], 'applicant': r['applicant_normalized'],
                       'annual_citations': round(r['annual_citations'], 2), 'note': '2000–2016 층 6위로 10건에는 들지 않음. 삼성물산의 협력사(GRC) 특허라 청구항 비교 참고용으로 추가',
                       'claims_url': f"https://patents.google.com/patent/{gp(r['Display Key'])}/en#claims"}]).to_excel(w, sheet_name='참고(GRC)', index=False)
out.to_csv('../handoff/US_핵심특허_팀원2반환.csv', index=False, encoding='utf-8-sig')
print(out[['technology', 'rank', 'grant_number', 'applicant_normalized', 'filing_date', 'legal_status', 'selection_metric', 'building_link']].to_string())
print(pd.DataFrame(excl)[['technology', 'grant_number', 'stratum_rank_by_metric']].to_string()); print('ref', len(ref))
