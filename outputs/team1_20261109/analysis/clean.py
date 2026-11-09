"""raw Lens export -> clean data. 실행: python clean.py (analysis 폴더에서)"""
import re, pandas as pd
RAW, CLEAN = '../raw/', '../clean/'
# 같은 회사(그룹) 통합: 원 명칭 -> 통합 명칭. 근거는 회사명 자체(자회사·라이선스 법인)
SAME_NAME = {
    'BAIDU USA LLC': 'BAIDU', 'BEIJING BAIDU NETCOM SCI & TEC': 'BAIDU',
    'INVENTEC CORP': 'INVENTEC', 'INVENTEC PUDONG TECH CORP': 'INVENTEC',
    'MICROSOFT TECHNOLOGY LICENSING LLC': 'MICROSOFT', 'MICROSOFT CORP': 'MICROSOFT',
    'NVIDIA CORP': 'NVIDIA', 'DELL PRODUCTS LP': 'DELL', 'GOOGLE LLC': 'GOOGLE', 'GOOGLE INC': 'GOOGLE',
    'QUANTA COMP INC': 'QUANTA', 'HEWLETT PACKARD ENTPR DEV LP': 'HPE',
    'HEWLETT PACKARD DEVELOPMENT CO': 'HP', 'FULIAN PREC ELECTRONICS TIANJIN CO LTD': 'FOXCONN (HON HAI)',
    'HON HAI PREC IND CO LTD': 'FOXCONN (HON HAI)', 'GREEN REVOLUTION COOLING INC': 'GRC (GREEN REVOLUTION COOLING)',
    'ASETEK AS': 'ASETEK', 'ASETEK DANMARK AS': 'ASETEK', 'HUAWEI TECH CO LTD': 'HUAWEI',
    'INTERNATIONAL BUSINESS MACHINES CORP': 'IBM', 'INTERNATIONAL BUSINESS MACHINES CORPORATION': 'IBM',
    'HEWLETT PACKARD ENTERPRISE DEVELOPMENT LP': 'HPE', 'HEWLETT-PACKARD DEVELOPMENT COMPANY L.P': 'HP',
    'BEIJING BAIDU NETCOM SCIENCE AND TECHNOLOGY CO. LTD': 'BAIDU', 'COOLIT SYSTEMS INC': 'COOLIT SYSTEMS',
    'COOLIT SYSTEMS INC.': 'COOLIT SYSTEMS', 'GREEN REVOLUTION COOLING, INC.': 'GRC (GREEN REVOLUTION COOLING)', 'HONGFUJIN PREC ELECTRONICS TIANJIN CO LTD': 'FOXCONN (HON HAI)', 'NORTEK AIR SOLUTION CANADA INC': 'NORTEK AIR SOLUTIONS CANADA INC', 'HARDCORE COMPUTER INC': 'LIQUIDCOOL SOLUTIONS (구 HARDCORE COMPUTER)', 'LIQUIDCOOL SOLUTIONS INC': 'LIQUIDCOOL SOLUTIONS (구 HARDCORE COMPUTER)',
}
CORP = re.compile(r'\b(INC|CORP|CORPORATION|LLC|LTD|LP|LLP|CO|AS|A/S|SAS|SA|AG|GMBH|BV|NV|PLC|KK|LIMITED|COMPANY|TECH|TECHNOLOGIES|GROUP|UNIV|UNIVERSITY|INST|LAB|LABS|IBM|OVH|SYSTEMS|ELECTRONICS|IND|SCI|NETCOM|INTERNAT|INTERNATIONAL|B V|B\.V)\b')
def first_owner(owners):
    # Owners 예: 'VERTIV CORPORATION (2016-12-07);;COOLIGY INC (2007-05-01)' -> 가장 이른 날짜 = 최초 권리자
    items = []
    for x in str(owners).split(';;'):
        m = re.match(r'\s*(.+?)\s*\((\d{4}-\d{2}-\d{2})\)\s*$', x)
        if m:
            items.append((m.group(2), m.group(1).upper()))
    return [min(items)[1]] if items else []
def norm_list(raw, owners=None):
    names = [x.strip().upper() for x in str(raw).split(';;') if x.strip() and str(raw) != 'nan']
    corps = [n for n in names if CORP.search(n)]
    if corps:
        keep = corps                           # 회사가 있으면 개인(발명자) 이름은 뺀다
    else:
        keep = first_owner(owners) or names    # 개인만 있으면 최초 권리자(Owners), 없으면 개인 이름 유지
    out = []
    for n in keep:
        m = SAME_NAME.get(n, n)
        if m not in out:
            out.append(m)
    return out
# 무작위 50건 precision 점검(액침 76%) 후, 제목·초록 키워드로 찾은 명백한 비대상 문헌을 제외 (번호: 이유)
EXCLUDE = {
    'imm': {
        'US 2015/0382511 A1': '바닷속에 데이터센터 모듈을 두는 방식. 서버를 냉각액에 담그는 액침이 아님',
        'US 2015/0321739 A1': '해저 데이터센터 선박. 액침 아님',
        'US 2009/0295167 A1': '수상 데이터센터. 액침 아님',
        'US 2022/0074431 A1': '역삼투 담수화 시스템. 데이터센터 냉각 아님',
        'US 8959941 B2': '공기측 이코노마이저 + 액냉 랙(DLC 계열). 액침 아님',
        'US 8966922 B2': '공기측 이코노마이저 + 액냉 랙(DLC 계열). 액침 아님',
        'US 2017/0030632 A1': '맥주 급속 냉각. 데이터센터 아님',
        'US 2017/0004894 A1': '원자력 시설. 데이터센터 아님',
        'US 2016/0035444 A1': '사용후핵연료 습식 저장. 데이터센터 아님',
        'US 7594582 B2': '음식 보온 수조. 데이터센터 아님',
        'US 2011/0195167 A1': '음식 보온 수조. 데이터센터 아님',
        'US 2007/0253646 A1': '음식 보온 수조. 데이터센터 아님',
        'US 2018/0010817 A1': '수상(바지선형) 데이터센터 시설. 서버를 냉각액에 담그는 액침이 아님',
        'US 2017/0071143 A1': '식물 복제(삽목) 장치. 데이터센터 아님 (정제 후 2차 표본에서 발견)',
        'US 2025/0172250 A1': 'LNG 냉열 회수(얼음 슬러리). 데이터센터는 활용처 중 하나로만 언급, 서버 액침 아님',
        'US 2023/0131311 A1': '천연가스 감압 발전기 시스템. 서버 냉각이 본 기술이 아님 (정제 후 2차 표본에서 발견)',
    },
    'dlc': {
        'US 2023/0077114 A1': '자동차 제어기(ECU)용 랙. 데이터센터 서버 냉각 아님',
        'US 12262506 B2': '자동차 제어기(ECU)용 랙(Aptiv). 위 공개본의 등록본. 데이터센터 서버 냉각 아님',
    },
}
def members(s):
    return set(str(s).split(';;')) if str(s) != 'nan' else set()

# 분류 경계 기술 표시 (인계서: "칩 분사냉각처럼 분류 경계에 있는 기술은 별도 표시").
# 제외하지 않고 태그만 단다. 판정은 제목·초록의 표현 기준이다.
SPRAY = r'spray|jet impingement|impinging jet|microjet|micro-jet'
TWO_PHASE = r'two[- ]phase|phase[- ]change|multi-?phase|refrigerant|thermosiphon|thermosyphon|boiling|vapori[sz]'


def boundary(r):
    text = (str(r['Title']) + ' ' + str(r['Abstract'])).lower()
    tags = []
    if pd.Series([text]).str.contains(SPRAY, regex=True).iloc[0]:
        tags.append('분사·제트 냉각')
    if r['technology'] == 'DLC' and pd.Series([text]).str.contains(TWO_PHASE, regex=True).iloc[0]:
        tags.append('냉매·상변화 표현(2상 냉각 경계)')
    return '; '.join(tags)


if __name__ == '__main__':
    log, excluded = [], []
    for tech, t in [('DLC', 'dlc'), ('Immersion', 'imm')]:
        a0 = pd.read_csv(RAW + f'us_{t}_all.csv'); g0 = pd.read_csv(RAW + f'us_{t}_grant.csv')
        ex = EXCLUDE.get(t, {})
        drop = a0['Display Key'].isin(ex) | (a0['Document Type'] == 'Design Right')  # 디자인 특허는 기술 특허가 아니어서 제외
        bad_members = set().union(*[members(m) | {lid} for m, lid in zip(a0.loc[drop, 'Simple Family Members'], a0.loc[drop, 'Lens ID'])]) if drop.any() else set()
        excluded.append(a0.loc[drop, ['Display Key', 'Title']].assign(technology=tech, reason=a0.loc[drop, 'Display Key'].map(ex).fillna('디자인 특허(Design Right). 외관 권리라 기술 분석에서 제외')))
        a = a0[~drop].copy()
        g = g0[g0['Document Type'] == 'Granted Patent'].copy()
        g_drop = g['Lens ID'].isin(bad_members) | g['Simple Family Members'].apply(lambda m: bool(members(m) & bad_members)) | g['Display Key'].isin(ex)
        g = g[~g_drop].copy()
        for df in (a, g):
            df.insert(0, 'technology', tech)
            df['applicant_normalized'] = [';; '.join(norm_list(r, o)) for r, o in zip(df['Applicants'], df['Owners'])]
        a.to_csv(CLEAN + f'us_{t}_families.csv', index=False, encoding='utf-8-sig')
        g.to_csv(CLEAN + f'us_{t}_granted.csv', index=False, encoding='utf-8-sig')
        log.append({'technology': tech, 'raw_all_rows(simple families)': len(a0), 'excluded_families(noise)': int(drop.sum()),
                    'kept_families': len(a), 'excluded_granted(noise)': int(g_drop.sum()), 'raw_grant_export_rows': len(g0),
                    'kept_granted_rows': len(g), 'dropped_non_granted': len(g0) - len(g),
                    'dropped_types': g0.loc[g0['Document Type'] != 'Granted Patent', 'Document Type'].value_counts().to_dict()})
    # 두 검색에 모두 걸린 패밀리 표시 (각 기술에 모두 포함하는 '중복 태그' 규칙)
    fam = {t: pd.read_csv(CLEAN + f'us_{t}_families.csv') for t in ['dlc', 'imm']}
    mem = lambda r: members(r['Simple Family Members']) | {r['Lens ID']}
    allm = {t: set().union(*[mem(r) for _, r in fam[t].iterrows()]) for t in fam}
    for t, o in [('dlc', 'imm'), ('imm', 'dlc')]:
        fam[t]['both_tech'] = [bool(mem(r) & allm[o]) for _, r in fam[t].iterrows()]
        fam[t]['boundary_tag'] = fam[t].apply(boundary, axis=1)
        fam[t].to_csv(CLEAN + f'us_{t}_families.csv', index=False, encoding='utf-8-sig')
        log[0 if t == 'dlc' else 1]['families_in_both_searches'] = int(fam[t]['both_tech'].sum())
        for tag, n in fam[t]['boundary_tag'].value_counts().items():
            if tag:
                log[0 if t == 'dlc' else 1][f'boundary: {tag}'] = int(n)
    pd.DataFrame(log).to_csv(CLEAN + 'cleaning_log.csv', index=False, encoding='utf-8-sig')
    pd.concat(excluded).to_csv(CLEAN + 'excluded_records.csv', index=False, encoding='utf-8-sig')
    print(pd.DataFrame(log).to_string())
