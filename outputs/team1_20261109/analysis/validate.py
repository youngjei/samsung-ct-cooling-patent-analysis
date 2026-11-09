"""팀원1 결과 자동 점검. 실행: python validate.py (analysis 폴더에서). 출력: ../validation.json
점검: 원본 파일 해시·행 수, 국가·출원일 필터, Filed 필터 흔적, 검색식 준수, 원본→정제 대조(빠진 건 = 제외 목록),
등록특허 문서 유형, 연도별 합계, HHI 재계산, 핵심특허 반환표 필수 필드, 시설 보완 검색 분류."""
import hashlib, json
import pandas as pd

RAW, CLEAN = '../raw/', '../clean/'
SERVER = ['server', 'data center', 'data centre', 'datacenter', 'rack']
QUERY = {
    'us_dlc_all': (['cold plate', 'direct liquid cool', 'direct to chip', 'coolant distribution unit', 'liquid cool'], SERVER, False),
    'us_imm_all': (['immers', 'submerg', 'dielectric fluid', 'dielectric liquid'], SERVER, True),
}
REQUIRED = ['technology', 'rank', 'application_number', 'publication_number', 'grant_number', 'family_id', 'dedup_rule', 'title',
            'applicant_raw', 'applicant_normalized', 'filing_date', 'priority_date', 'legal_status', 'status_checked_at',
            'source_url', 'claims_url', 'selection_reason', 'selection_metric', 'building_link', 'building_link_reason']
checks, ok = {}, []


def record(name, value, passed):
    checks[name] = value
    ok.append((name, bool(passed)))


def text(r):
    return (str(r['Title']) + ' ' + str(r['Abstract'])).lower().replace('-', ' ')


# 1. 원본 파일
for f in ['us_dlc_all', 'us_dlc_grant', 'us_imm_all', 'us_imm_grant', 'us_facility_all']:
    d = pd.read_csv(RAW + f + '.csv')
    app, pub = pd.to_datetime(d['Application Date']), pd.to_datetime(d['Publication Date'])
    v = {'sha256_12': hashlib.sha256(open(RAW + f + '.csv', 'rb').read()).hexdigest()[:12], 'rows': len(d),
         'jurisdictions': sorted(d['Jurisdiction'].unique().tolist()),
         'application_date_range': [str(app.min().date()), str(app.max().date())],
         'published_after_2024 (Filed 필터 흔적)': int((pub > '2024-12-31').sum())}
    record(f'raw/{f}', v, v['jurisdictions'] == ['US'] and app.min() >= pd.Timestamp('2000-01-01') and app.max() <= pd.Timestamp('2024-12-31'))

# 2. 검색식 준수 (제목·초록, 하이픈은 공백으로)
for f, (k1, k2, need_cool) in QUERY.items():
    d = pd.read_csv(RAW + f + '.csv')
    bad = [r['Display Key'] for _, r in d.iterrows()
           if not (any(k in text(r) for k in k1) and any(k in text(r) for k in k2) and ('cool' in text(r) or not need_cool))]
    record(f'query_conformance/{f}', {'rows': len(d), 'not_matching': bad}, not bad)
fac = pd.read_csv(RAW + 'us_facility_all.csv')
A = ['data center', 'data centre', 'datacenter', 'server room', 'computer room']
B = ['liquid cool', 'immersion', 'cold plate', 'coolant distribution unit', 'chilled water', 'facility water']
C = ['building', 'facilit', 'cooling tower', 'chiller', 'hvac', 'air handl', 'piping', 'prefabricat', 'modular']
bad = [r['Display Key'] for _, r in fac.iterrows()
       if not (any(k in text(r) for k in A) and any(k in str(r['Abstract']).lower().replace('-', ' ') for k in B)
               and any(k in str(r['Abstract']).lower() for k in C))]
record('query_conformance/us_facility_all', {'rows': len(fac), 'not_matching': bad}, not bad)

# 3. 원본 → 정제 대조
ex = pd.read_csv(CLEAN + 'excluded_records.csv')
x = pd.ExcelFile('특허분석_결과.xlsx')
summary = x.parse('요약').set_index(x.parse('요약').columns[0])
for t, tech in [('dlc', 'DLC'), ('imm', 'Immersion')]:
    raw = pd.read_csv(RAW + f'us_{t}_all.csv')
    fam = pd.read_csv(CLEAN + f'us_{t}_families.csv')
    gone = set(raw['Display Key']) - set(fam['Display Key'])
    extra = set(fam['Display Key']) - set(raw['Display Key'])
    record(f'clean/{t}_families', {'raw': len(raw), 'kept': len(fam), 'removed': len(gone), 'removed_all_in_excluded_records': gone <= set(ex['Display Key']),
                                   'not_in_raw': sorted(extra), 'both_tech': int(fam['both_tech'].sum()),
                                   'boundary_tag': fam['boundary_tag'].fillna('').value_counts().drop('', errors='ignore').to_dict()},
           gone <= set(ex['Display Key']) and not extra)
    g = pd.read_csv(CLEAN + f'us_{t}_granted.csv'); rg = pd.read_csv(RAW + f'us_{t}_grant.csv')
    record(f'clean/{t}_granted', {'raw_granted': int((rg['Document Type'] == 'Granted Patent').sum()), 'kept': len(g),
                                  'all_granted': bool((g['Document Type'] == 'Granted Patent').all()),
                                  'all_in_raw': set(g['Display Key']) <= set(rg['Display Key'])},
           (g['Document Type'] == 'Granted Patent').all() and set(g['Display Key']) <= set(rg['Display Key']))
    # 4. 연도별 합계
    yr = x.parse(f'{tech}_연도별')
    record(f'sum/{tech}_yearly_equals_families', {'yearly_sum': int(yr.iloc[:, 1].sum()), 'families': len(fam)}, int(yr.iloc[:, 1].sum()) == len(fam))
    # 5. HHI 재계산 (2015–2024, 완전계수)
    f15 = fam[pd.to_datetime(fam['Earliest Priority Date']).dt.year.between(2015, 2024)]
    apps = f15['applicant_normalized'].fillna('').apply(lambda s: [a.strip() for a in s.split(';; ') if a.strip()]).explode().dropna()
    share = apps.value_counts() / apps.value_counts().sum()
    h = round(float((share ** 2).sum()), 4)
    reported = round(float(summary.loc['HHI 완전계수 (0–1)', tech]), 4)
    record(f'hhi/{tech}', {'recomputed': h, 'reported': reported, 'share_sum': round(float(share.sum()), 6)}, abs(h - reported) < 1e-4)

# 6. 핵심특허 반환표
core = pd.read_csv('../handoff/US_핵심특허_팀원2반환.csv')
granted = set(pd.read_csv(CLEAN + 'us_dlc_granted.csv')['Display Key']) | set(pd.read_csv(CLEAN + 'us_imm_granted.csv')['Display Key'])
missing_cols = [c for c in REQUIRED if c not in core.columns]
empty = {c: int(core[c].isna().sum()) for c in REQUIRED if c in core.columns and core[c].isna().sum()}
record('core_list', {'rows': len(core), 'per_technology': core.groupby('technology').size().to_dict(), 'missing_columns': missing_cols,
                     'empty_cells': empty, 'all_in_granted_data': set(core['grant_number']) <= granted,
                     'unique_families': int(core['family_id'].nunique())},
       not missing_cols and not empty and set(core['grant_number']) <= granted and core['family_id'].nunique() == len(core))

# 7. 시설 보완 검색 분류
fx = pd.ExcelFile('시설검색_분석.xlsx').parse('목록')
record('facility_search', {'families': len(fx), 'by_type': fx['유형'].value_counts().to_dict(),
                           'construction_name_hits': int(fx['건설사 이름 포함'].sum()),
                           'already_in_A_or_B': int((~fx['기존 검색에서 빠진 것']).sum())}, len(fx) == len(fac))

out = {'checked_at': '2026-11-09', 'all_passed': all(p for _, p in ok), 'failed': [n for n, p in ok if not p], 'checks': checks}
json.dump(out, open('../validation.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2, default=str)
print('all_passed:', out['all_passed'], '| failed:', out['failed'])
