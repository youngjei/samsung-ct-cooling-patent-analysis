"""등록특허 중 연평균 피인용 상위 후보 (같은 simple family는 1건만). 조회일 = Lens export일 2026-11-09"""
import pandas as pd
ASOF = pd.Timestamp('2026-11-09')
out = []
for tech, t in [('DLC', 'dlc'), ('Immersion', 'imm')]:
    g = pd.read_csv(f'../clean/us_{t}_granted.csv')
    pub = pd.to_datetime(g['Publication Date'])
    g['years_since_grant'] = ((ASOF - pub).dt.days / 365.25).clip(lower=1).round(2)
    g['annual_citations'] = (g['Cited by Patent Count'] / g['years_since_grant']).round(2)
    g['family_key'] = g['Simple Family Members'].fillna(g['Display Key']).apply(lambda s: ';;'.join(sorted(str(s).split(';;'))))
    g = g.sort_values('annual_citations', ascending=False).drop_duplicates('family_key')
    g['candidate_rank'] = range(1, len(g) + 1)
    out.append(g.head(30))
c = pd.concat(out)
c.to_csv('../clean/core_candidates_top30.csv', index=False, encoding='utf-8-sig')
