"""보완 검색 C (시설 쪽 데이터센터 액체냉각) 출원인 분류.
목적: 기존 검색식이 서버·랙 표현을 요구해 시설 쪽 특허(냉각탑·칠러·배관·건물)가 덜 잡혔을 가능성을 점검하고,
      건설사·엔지니어링사가 실제로 특허를 내는지 확인한다.
입력: ../raw/us_facility_all.csv (Lens, 미국, 출원 2000–2024, Simple family)  출력: 시설검색_분석.xlsx
분류는 출원인(없으면 Owners의 최초 권리자) 이름과 회사 사업을 기준으로 분석자가 붙였다."""
import pandas as pd
import clean

CATEGORY = [  # (이름에 포함된 문자열, 유형)
    ('BAIDU', '클라우드·데이터센터 운영사'), ('BYTEDANCE', '클라우드·데이터센터 운영사'), ('GOOGLE', '클라우드·데이터센터 운영사'),
    ('EXAFLOP', '클라우드·데이터센터 운영사'), ('EQUINIX', '클라우드·데이터센터 운영사'), ('HEBEI QINHUAI', '클라우드·데이터센터 운영사'),
    ('OVH', '클라우드·데이터센터 운영사'), 
    ('NVIDIA', '서버·IT 제조사'), ('DELL', '서버·IT 제조사'), ('HPE', '서버·IT 제조사'), ('HEWLETT', '서버·IT 제조사'),
    ('IBM', '서버·IT 제조사'), ('INTERNATIONAL BUSINESS MACHINES', '서버·IT 제조사'), ('GLOBALFOUNDRIES', '서버·IT 제조사'),
    ('VETTE', '냉각·전력·인프라 설비 기업'), ('VERTIV', '냉각·전력·인프라 설비 기업'), ('AMERICAN POWER', '냉각·전력·인프라 설비 기업'),
    ('AMERCIAN POWER', '냉각·전력·인프라 설비 기업'), ('SCHNEIDER', '냉각·전력·인프라 설비 기업'), ('KEENCOOL', '냉각·전력·인프라 설비 기업'),
    ('HOFFMAN', '냉각·전력·인프라 설비 기업'), ('VARITEQ', '냉각·전력·인프라 설비 기업'), ('COMMSCOPE', '냉각·전력·인프라 설비 기업'),
    ('NAUTILUS', '냉각·전력·인프라 설비 기업'), ('SHUMATE', '설계·엔지니어링사(MEP)'),
]
CONSTRUCTION_WORDS = ['CONSTRUCTION', 'CONSTRUCT', 'BUILDERS', 'E&C', 'ENGINEERING & CONSTRUCTION', 'SAMSUNG C&T', 'HYUNDAI ENG',
                      'OBAYASHI', 'KAJIMA', 'SHIMIZU', 'TAISEI', 'TAKENAKA', 'TURNER', 'BECHTEL', 'FLUOR', 'JACOBS', 'SKANSKA',
                      'MORTENSON', 'DPR ', 'HOLDER CONSTRUCTION', 'AECOM']


def who(row):
    names = clean.norm_list(row['Applicants'], row['Owners'])
    text = ' '.join(names + [str(row['Owners']).upper()])
    for key, cat in CATEGORY:
        if key in text:
            return names, cat
    return names, '개인·기타'


if __name__ == '__main__':
    d = pd.read_csv('../raw/us_facility_all.csv')
    rows = []
    for _, r in d.iterrows():
        names, cat = who(r)
        cpcs = [c.strip() for c in str(r['CPC Classifications']).split(';;') if c.strip()]
        rows.append({'번호': r['Display Key'], '최우선일': r['Earliest Priority Date'], '제목': r['Title'],
                     '출원인(정규화)': '; '.join(names), '유형': cat,
                     '건설사 이름 포함': any(w in (str(r['Applicants']) + str(r['Owners'])).upper() for w in CONSTRUCTION_WORDS),
                     '건물·공조 CPC(E04B/F/H, F24F)': any(c.startswith(('E04B', 'E04F', 'E04H', 'F24F')) for c in cpcs),
                     '기존 DLC 데이터에도 있음': False, '기존 액침 데이터에도 있음': False, 'URL': r['URL']})
    out = pd.DataFrame(rows)
    for t, col in [('dlc', '기존 DLC 데이터에도 있음'), ('imm', '기존 액침 데이터에도 있음')]:
        f = pd.read_csv(f'../clean/us_{t}_families.csv')
        mem = set(';;'.join(f['Simple Family Members'].fillna('')).split(';;')) | set(f['Lens ID'])
        out[col] = [bool(set(str(m).split(';;')) & mem) or lid in mem for m, lid in zip(d['Simple Family Members'], d['Lens ID'])]
    out['기존 검색에서 빠진 것'] = ~(out['기존 DLC 데이터에도 있음'] | out['기존 액침 데이터에도 있음'])
    summ = out.groupby('유형').agg(패밀리수=('번호', 'size'), 기존검색에서_빠진_것=('기존 검색에서 빠진 것', 'sum')).sort_values('패밀리수', ascending=False)
    summ.loc['합계'] = [len(out), int(out['기존 검색에서 빠진 것'].sum())]
    with pd.ExcelWriter('시설검색_분석.xlsx') as w:
        summ.to_excel(w, sheet_name='유형별')
        out.to_excel(w, sheet_name='목록', index=False)
        pd.DataFrame({'항목': ['검색식', '필터', '검색일', '분류 기준', '건설사 확인'],
                      '내용': [open('../raw/검색식.txt', encoding='utf-8').read().split('[검색식 C')[-1].strip()[:2000] if '[검색식 C' in open('../raw/검색식.txt', encoding='utf-8').read() else '검색식 C (raw/검색식.txt)',
                              '미국, Filed 2000-01-01 ~ 2024-12-31, Simple family',
                              '2026-11-09', '출원인·최초 권리자의 회사 사업으로 분석자가 분류',
                              f"건설사 이름(국내·일본·미국 주요 건설·EPC사 목록) 포함 문헌 {int(out['건설사 이름 포함'].sum())}건"]}).to_excel(w, sheet_name='정의', index=False)
    print(summ.to_string()); print('건설사 이름 포함:', int(out['건설사 이름 포함'].sum()), '| 건물·공조 CPC:', int(out['건물·공조 CPC(E04B/F/H, F24F)'].sum()))
    print(out[out['유형'] == '개인·기타'][['번호', '출원인(정규화)', '제목']].to_string())
