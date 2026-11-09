"""냉각 전문기업의 미국 특허 현황 (전 기간, 2000–2024 최우선일).
run_analysis.py의 *_냉각전문기업 시트는 2015–2024만 보므로, 전 기간 현황은 이 스크립트로 만든다.
입력: ../clean/us_{dlc,imm}_families.csv, us_{dlc,imm}_granted.csv  출력: 냉각전문기업_특허현황.csv
평균 연간 피인용 = 해당 기업 등록특허의 (피인용 수 ÷ 등록 후 경과연수, 최소 1년) 평균. 기준일 2026-11-09."""
import pandas as pd
from run_analysis import COOLING_SPECIALISTS

REF = pd.Timestamp('2026-11-09')
rows = []
for t, label in [('dlc', 'DLC'), ('imm', 'Immersion')]:
    f = pd.read_csv(f'../clean/us_{t}_families.csv'); g = pd.read_csv(f'../clean/us_{t}_granted.csv')
    f['py'] = pd.to_datetime(f['Earliest Priority Date']).dt.year
    g['yrs'] = ((REF - pd.to_datetime(g['Publication Date'])).dt.days / 365.25).clip(lower=1)
    g['acit'] = g['Cited by Patent Count'].fillna(0) / g['yrs']
    for name in COOLING_SPECIALISTS:
        fm = f[f['applicant_normalized'].fillna('').str.split(';; ').apply(lambda L: name in L)]
        if fm.empty:
            continue
        gm = g[g['applicant_normalized'].fillna('').str.split(';; ').apply(lambda L: name in L)]
        rows.append({'technology': label, 'company': name, 'families_2000_2024': len(fm),
                     'families_2020_2024': int((fm['py'] >= 2020).sum()),
                     'first_priority_year': int(fm['py'].min()), 'last_priority_year': int(fm['py'].max()),
                     'avg_annual_citations': round(gm['acit'].mean(), 2) if len(gm) else 0.0})
out = pd.DataFrame(rows).sort_values(['technology', 'families_2000_2024', 'avg_annual_citations'], ascending=[True, False, False])
out.to_csv('냉각전문기업_특허현황.csv', index=False, encoding='utf-8-sig')
print(out.to_string(index=False))
