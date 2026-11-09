"""미국 DLC/액침 정량분석. 입력: ../clean (clean.py 결과). 출력: ../analysis/특허분석_결과.xlsx, ../figures/*.png
집계 단위
- 추이·CPC·출원인·HHI·신규 출원인·건물 연계: Lens simple family 1건 = 1 (us_*_families.csv), 연도 = 최우선일(Earliest Priority Date, 처음 출원한 날)
- S커브: 등록특허 누적 (us_*_granted.csv), 연도 = 최우선일(Earliest Priority Date)
- 공동출원: 완전계수(출원인마다 1건)를 기본으로, 분할계수(1/출원인 수)를 민감도로 함께 계산
"""
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

ASOF = pd.Timestamp('2026-11-09')
YEARS = range(2000, 2025)
TECHS = [('DLC', 'dlc'), ('Immersion', 'imm')]
BUILD = ('E04B', 'E04F', 'E04H', 'F24F')   # 건물 구조·특수건물(E04B/F/H), 공조(F24F). E04G(비계·거푸집) 제외
GROUPS = {
    '냉각판·열전달': ('H05K7/20254', 'H01L23/473', 'F28'),
    '침지·탱크': ('H05K7/20236', 'H01L23/44'),
    '펌프·순환·배관': ('H05K7/20272', 'H05K7/20281', 'F04', 'F16L'),
    '서버·랙 구조': ('H05K7/207', 'H05K7/14', 'G06F1/20'),
    '제어·모니터링': ('G05B', 'G05D', 'G06F1/206', 'H05K7/20836'),
    '건물·공조': BUILD,
    '냉각액(소재)': ('C09K5', 'C10M'),
}
EN = {'냉각판·열전달': 'cold plate / heat transfer', '침지·탱크': 'immersion / tank', '펌프·순환·배관': 'pump / loop / piping',
      '서버·랙 구조': 'server / rack', '제어·모니터링': 'control / monitoring', '건물·공조': 'building / HVAC', '냉각액(소재)': 'coolant (material)'}
COOLING_SPECIALISTS = ['GRC (GREEN REVOLUTION COOLING)', 'ASETEK', 'COOLIT SYSTEMS', 'LIQUIDCOOL SOLUTIONS (구 HARDCORE COMPUTER)',
                       'TMGCORE LLC', 'SUBMER', 'LIEBERT CORP', 'VERTIV', 'NAUTILUS DATA TECH INC', 'COOLIGY INC', 'VETTE CORP',
                       'CHILLDYNE', 'MOTIVAIR', 'ICEOTOPE', 'LIQUIDSTACK', 'ZUTACORE', 'JETCOOL', 'DOW GLOBAL TECHNOLOGIES LLC',
                       'SCHNEIDER ELECTRIC IT CORP', 'CALYOS SA', 'NEXALUS LTD', 'QNX COOLING SYSTEMS INC']


def codes(s):
    # 같은 코드가 한 패밀리에 여러 번 적힌 경우 1번만 센다
    return list(dict.fromkeys(c.strip() for c in str(s).split(';;') if c.strip() and str(s) != 'nan'))


def apps(s):
    return [x.strip() for x in str(s).split(';; ') if x.strip() and str(s) != 'nan']


def logistic(t, L, k, t0):
    return L / (1 + np.exp(-k * (t - t0)))


def gompertz(t, L, b, k):
    return L * np.exp(-b * np.exp(-k * t))


def stage_of(r):
    return '도입기' if r < 0.1 else '성장 전반' if r < 0.5 else '성장 후반' if r < 0.9 else '성숙기'


def fit_stage(years, end):
    cum = years.value_counts().reindex(range(2000, end + 1), fill_value=0).cumsum()
    t = np.arange(len(cum), dtype=float); y = cum.values.astype(float)
    out = {}
    for name, f, p0, bounds in [('Logistic', logistic, [y[-1] * 2, 0.3, len(t)], ([y[-1], 0.01, 0], [y[-1] * 100, 3, 80])),
                                ('Gompertz', gompertz, [y[-1] * 2, 5, 0.1], ([y[-1], 0.01, 0.001], [y[-1] * 100, 200, 3]))]:
        try:
            p, cov = curve_fit(f, t, y, p0=p0, bounds=bounds, maxfev=100000)
            r2 = 1 - ((y - f(t, *p)) ** 2).sum() / ((y - y.mean()) ** 2).sum()
            se_L = float(np.sqrt(np.diag(cov))[0]) if np.all(np.isfinite(cov)) else np.inf
            ratio = y[-1] / p[0]
            out[name] = dict(f=f, p=p, r2=r2, L=p[0], ratio=ratio, stage=stage_of(ratio),
                             L_rel_se=se_L / p[0], at_bound=p[0] >= y[-1] * 99)
        except Exception as e:
            out[name] = dict(error=str(e))
    return cum, out


def hhi(counts):
    s = counts / counts.sum()
    return float((s ** 2).sum())


writer = pd.ExcelWriter('특허분석_결과.xlsx')
summary, mix_all, defs = [], {}, []
for tech, t in TECHS:
    a = pd.read_csv(f'../clean/us_{t}_families.csv')
    g = pd.read_csv(f'../clean/us_{t}_granted.csv')
    a['year'] = pd.to_datetime(a['Earliest Priority Date']).dt.year   # 패밀리의 최초 출원(최우선일) 연도
    g['pyear'] = pd.to_datetime(g['Earliest Priority Date']).dt.year
    a['cpcs'] = a['CPC Classifications'].apply(codes)
    a['apps'] = a['applicant_normalized'].apply(apps)
    a['link'] = a['cpcs'].apply(lambda cs: any(c.startswith(BUILD) for c in cs))
    a['cited'] = a['Cited by Patent Count'].fillna(0)
    a['ann_cite'] = a['cited'] / ((ASOF - pd.to_datetime(a['Publication Date'])).dt.days / 365.25).clip(lower=1)
    r = a[a['year'].between(2015, 2024)]

    # 1-1 연도별 추이 (패밀리, 출원연도) + 등록(최우선일)
    trend = pd.DataFrame({'패밀리 수(최우선연도)': a['year'].value_counts().reindex(YEARS, fill_value=0),
                          '등록특허 수(최우선연도)': g['pyear'].value_counts().reindex(YEARS, fill_value=0)})
    trend.index.name = '연도'
    trend.to_excel(writer, sheet_name=f'{tech}_연도별')
    ax = trend.plot(marker='o', title=f'{tech}: US patents by year (Lens, searched 2026-11-09, filed-date filter)')
    ax.axvspan(2022.5, 2024.5, color='grey', alpha=0.15); ax.text(2022.6, ax.get_ylim()[1] * 0.9, 'incomplete\n(pub. lag)', fontsize=8)
    plt.savefig(f'../figures/{tech}_1_trend.png', dpi=200, bbox_inches='tight'); plt.close()

    # 1-2 성장률: 기간 합계 비교 (작은 연도값의 왜곡을 피하려고 5년 합계 사용)
    p1, p2 = trend.loc[2013:2017, '패밀리 수(최우선연도)'].sum(), trend.loc[2018:2022, '패밀리 수(최우선연도)'].sum()
    growth = pd.DataFrame([{'기간 A': '2013–2017', 'A 패밀리 수': p1, '기간 B': '2018–2022', 'B 패밀리 수': p2,
                            '증가율 (B/A−1)': round(p2 / p1 - 1, 3) if p1 else np.nan,
                            '연평균 증가율 ((B/A)^(1/5)−1)': round((p2 / p1) ** 0.2 - 1, 3) if p1 else np.nan,
                            '비고': '2023–2024 출원은 공개 지연(약 18개월)으로 덜 잡혀 제외'}])
    growth.to_excel(writer, sheet_name=f'{tech}_성장률', index=False)

    # 1-3 S커브 (등록 누적) + 종료연도 민감도
    sens = []
    for end in (2019, 2020, 2021):
        cum_e, fx = fit_stage(g['pyear'], end)
        row = {'적합 마지막 연도': end, '누적 등록': int(cum_e.iloc[-1])}
        for m, v in fx.items():
            if 'error' in v:
                row[f'{m}'] = '적합 실패'
                continue
            row.update({f'{m} R2': round(v['r2'], 3), f'{m} L': round(v['L']), f'{m} 누적/L': round(v['ratio'], 2),
                        f'{m} 단계': v['stage'], f'{m} L 상대표준오차': round(v['L_rel_se'], 2), f'{m} L 상한도달': bool(v['at_bound'])})
        sens.append(row)
    sens = pd.DataFrame(sens)
    sens.to_excel(writer, sheet_name=f'{tech}_S커브', index=False)
    cum, fits = fit_stage(g['pyear'], 2021)
    stages = {m: v.get('stage') for m, v in fits.items()}
    # 단계 판정: 포화수준 L은 아직 식별되지 않아(상대표준오차 큼·상한 도달) '누적/L = 몇 %'는 쓰지 않는다.
    # 대신 2021년이 각 모형의 변곡점(Logistic L/2, Gompertz L/e) 앞인지 뒤인지로 판정한다.
    INFL = {'Logistic': 0.5, 'Gompertz': 1 / np.e}
    pos = {m: ('변곡점 이전' if v['ratio'] < INFL[m] else '변곡점 이후') for m, v in fits.items() if 'error' not in v}
    stable_L = all(('error' not in v) and v['L_rel_se'] < 0.5 and not v['at_bound'] for v in fits.values())
    if len(set(pos.values())) == 1 and '변곡점 이전' in pos.values():
        verdict = '성장기 초입 (2021년 기준 두 모형 모두 변곡점 이전)' + ('' if stable_L else ', 포화수준은 미식별')
    elif len(set(pos.values())) == 1:
        verdict = '성장 후반 이후 (두 모형 모두 변곡점 통과)'
    else:
        verdict = '모형에 따라 다름: ' + ', '.join(f'{m} {p}' for m, p in pos.items())
    sens['Logistic 변곡점 위치'] = np.where(sens['Logistic 누적/L'] < 0.5, '이전', '이후')
    sens['Gompertz 변곡점 위치'] = np.where(sens['Gompertz 누적/L'] < 1 / np.e, '이전', '이후')
    sens.to_excel(writer, sheet_name=f'{tech}_S커브', index=False)
    # 검증 구간 분리(인계서 4): 2000–2018로 적합하고 2019–2021 누적을 예측해 실제와 비교
    cum_tr, fx_tr = fit_stage(g['pyear'], 2018)
    actual = g['pyear'].value_counts().reindex(range(2000, 2022), fill_value=0).cumsum()
    hold = []
    for m, v in fx_tr.items():
        if 'error' in v:
            continue
        for yr in (2019, 2020, 2021):
            pred = float(v['f'](yr - 2000, *v['p']))
            hold.append({'모형': m, '연도': yr, '실제 누적': int(actual.loc[yr]), '예측 누적(2000–2018 적합)': round(pred, 1),
                         '오차율': round(pred / actual.loc[yr] - 1, 3)})
    hold = pd.DataFrame(hold)
    hold.to_excel(writer, sheet_name=f'{tech}_S커브', index=False, startrow=len(sens) + 3)
    holdout_err = {m: float(hold[(hold['모형'] == m) & (hold['연도'] == 2021)]['오차율'].iloc[0]) for m in hold['모형'].unique()}
    tt = np.arange(0, 31)
    plt.plot(cum.index, cum.values, 'o', label='granted, cumulative (priority year)')
    for m, v in fits.items():
        if 'error' not in v:
            plt.plot(2000 + tt, v['f'](tt, *v['p']), label=f"{m} (R2={v['r2']:.3f})")
    plt.ylim(0, cum.values[-1] * 3)
    plt.title(f'{tech}: S-curve, data to 2021 -> before inflection in both models', fontsize=10); plt.legend(fontsize=8)
    plt.savefig(f'../figures/{tech}_2_scurve.png', dpi=200, bbox_inches='tight'); plt.close()

    # 1-6 발명자 (강의: 출원인과 함께 발명자 분석)
    inv = a.assign(invs=a['Inventors'].apply(lambda s: list(dict.fromkeys(x.strip().upper() for x in str(s).split(';;') if x.strip() and str(s) != 'nan'))))
    inv_tbl = pd.DataFrame({
        '고유 발명자 수': [inv[inv['year'].between(2015, 2019)]['invs'].explode().nunique(), inv[inv['year'].between(2020, 2024)]['invs'].explode().nunique()],
        '패밀리당 평균 발명자 수': [round(inv[inv['year'].between(2015, 2019)]['invs'].str.len().mean(), 2), round(inv[inv['year'].between(2020, 2024)]['invs'].str.len().mean(), 2)]},
        index=['2015–2019', '2020–2024'])
    inv_tbl.to_excel(writer, sheet_name=f'{tech}_발명자')
    ie = inv[inv['year'].between(2015, 2024)][['invs', 'applicant_normalized']].explode('invs').dropna()
    top_inv = ie.groupby('invs').agg(패밀리수=('invs', 'size'), 소속출원인=('applicant_normalized', lambda x: x.value_counts().index[0])).sort_values('패밀리수', ascending=False).head(10)
    top_inv.to_excel(writer, sheet_name=f'{tech}_발명자', startcol=4)

    # 1-7 비특허문헌 인용 (강의: 비특허문헌을 많이 인용할수록 원천적인 경우가 많음)
    npl = a.assign(npl=a['NPL Citation Count'].fillna(0))
    npl_tbl = pd.DataFrame({'패밀리 수': [int(npl['year'].between(*p).sum()) for p in [(2000, 2014), (2015, 2019), (2020, 2024)]],
                            '평균 비특허문헌 인용 수(이상치 영향 큼)': [round(npl[npl['year'].between(*p)]['npl'].mean(), 2) for p in [(2000, 2014), (2015, 2019), (2020, 2024)]],
                            '중앙값': [float(npl[npl['year'].between(*p)]['npl'].median()) for p in [(2000, 2014), (2015, 2019), (2020, 2024)]],
                            '비특허문헌 1건 이상 비율': [round((npl[npl['year'].between(*p)]['npl'] > 0).mean(), 3) for p in [(2000, 2014), (2015, 2019), (2020, 2024)]]},
                           index=['2000–2014', '2015–2019', '2020–2024'])
    npl_tbl.to_excel(writer, sheet_name=f'{tech}_비특허인용')

    # 1-8 패밀리 출원국 (강의: 주요 5개국·PCT. 미국 데이터가 다른 나라 출원을 얼마나 함께 담는지)
    jur = a['Simple Family Member Jurisdictions'].fillna('').str.split(';;').apply(lambda xs: set(x.strip() for x in xs if x.strip()))
    jur_tbl = pd.DataFrame({'동시 출원 비율': {c: round(jur.apply(lambda s: c in s).mean(), 3) for c in ['CN', 'EP', 'JP', 'KR', 'WO']}})
    jur_tbl.loc['미국에만 출원'] = round(jur.apply(lambda s: s <= {'US'}).mean(), 3)
    jur_tbl.to_excel(writer, sheet_name=f'{tech}_패밀리국가')

    # 1-4 CPC 상위 코드 기간 비교 (완전계수: 한 패밀리가 여러 코드면 각각 1)
    cp = r[['year', 'cpcs']].explode('cpcs').dropna()
    top = cp['cpcs'].value_counts().head(10).index
    crow = []
    for code in top:
        n1 = ((cp['cpcs'] == code) & cp['year'].between(2015, 2019)).sum()
        n2 = ((cp['cpcs'] == code) & cp['year'].between(2020, 2024)).sum()
        crow.append({'CPC': code, '2015–2019': n1, '2020–2024': n2, '합계': n1 + n2,
                     '증가율': round(n2 / n1 - 1, 2) if n1 >= 5 else '기준기간 5건 미만'})
    pd.DataFrame(crow).to_excel(writer, sheet_name=f'{tech}_CPC', index=False)

    # 1-5 CPC 그룹 구성비 (패밀리 중 해당 그룹 코드가 하나라도 있는 비율; 합계 100% 아님)
    def share(df, pref):
        return round(df['cpcs'].apply(lambda cs: any(c.startswith(pref) for c in cs)).mean(), 3) if len(df) else np.nan
    early, late = r[r['year'] <= 2019], r[r['year'] >= 2020]
    mix = pd.DataFrame({'2015–2019': {k: share(early, v) for k, v in GROUPS.items()},
                        '2020–2024': {k: share(late, v) for k, v in GROUPS.items()},
                        '2015–2024': {k: share(r, v) for k, v in GROUPS.items()}})
    mix['변화(%p)'] = ((mix['2020–2024'] - mix['2015–2019']) * 100).round(1)
    mix.loc['(분모: 패밀리 수)'] = [len(early), len(late), len(r), np.nan]
    mix.to_excel(writer, sheet_name=f'{tech}_CPC구성비')
    mix_all[tech] = mix.loc[list(GROUPS), '2015–2024']

    # 2-1 출원인 순위·HHI (2015–2024)
    full = r['apps'].explode().dropna().value_counts()
    frac = r.assign(w=r['apps'].apply(lambda x: 1 / len(x) if len(x) else 0)).explode('apps').dropna(subset=['apps']).groupby('apps')['w'].sum().sort_values(ascending=False)
    rank_tbl = pd.DataFrame({'패밀리 수(완전계수)': full, '점유율(완전계수)': (full / full.sum()).round(4)})
    rank_tbl['패밀리 수(분할계수)'] = frac.reindex(rank_tbl.index).round(2)
    rank_tbl['냉각 전문기업'] = [n in COOLING_SPECIALISTS for n in rank_tbl.index]
    rank_tbl.index.name = '출원인(정규화)'
    rank_tbl.head(30).to_excel(writer, sheet_name=f'{tech}_출원인')
    h_full, h_frac = hhi(full), hhi(frac)
    # HHI 계산표 (인계서 2: 비중의 합과 분모 확인). 완전계수 분모 = 출원인-패밀리 쌍 수, 분할계수 분모 = 패밀리 수
    ht = pd.DataFrame({'패밀리 수(완전계수)': full, '비중(완전)': full / full.sum()})
    ht['비중²(완전)'] = ht['비중(완전)'] ** 2
    ht['패밀리 수(분할계수)'] = frac.reindex(ht.index).fillna(0)
    ht['비중(분할)'] = ht['패밀리 수(분할계수)'] / frac.sum()
    ht['비중²(분할)'] = ht['비중(분할)'] ** 2
    ht.index.name = '출원인(정규화)'
    chk = pd.DataFrame({'항목': ['대상 패밀리 수(2015–2024)', '완전계수 분모(출원인-패밀리 쌍)', '분할계수 분모(= 패밀리 수, 출원인 없는 패밀리 제외)',
                                '출원인 수', '비중 합(완전)', '비중 합(분할)', 'HHI 완전 = Σ비중²', 'HHI 분할 = Σ비중²', '비고'],
                        '값': [len(r), int(full.sum()), round(float(frac.sum()), 2), len(ht), round(ht['비중(완전)'].sum(), 6),
                              round(ht['비중(분할)'].sum(), 6), round(h_full, 4), round(h_frac, 4),
                              '두 계수 방식의 HHI는 서로 직접 비교하지 않고 각각의 민감도로만 본다']})
    chk.to_excel(writer, sheet_name=f'{tech}_HHI계산', index=False)
    ht.round(5).to_excel(writer, sheet_name=f'{tech}_HHI계산', startcol=3)
    cr4 = float((full / full.sum()).head(4).sum())

    # 2-2 신규 출원인 (검색범위 안에서 처음 등장한 연도)
    ex = a[['year', 'apps']].explode('apps').dropna()
    first = ex.groupby('apps')['year'].min()
    new = first.value_counts().reindex(YEARS, fill_value=0)
    new_tbl = pd.DataFrame({'신규 출원인 수': new, '전체 출원인 수': ex.groupby('year')['apps'].nunique().reindex(YEARS, fill_value=0)})
    new_tbl.index.name = '연도'
    new_tbl.to_excel(writer, sheet_name=f'{tech}_신규출원인')
    nb, na_ = new.loc[2015:2019].mean(), new.loc[2020:2024].mean()

    # 3 건물·설비 연계 (CPC 기준 proxy)
    link = r.groupby('year')['link'].agg(['count', 'sum'])
    link.columns = ['패밀리 수(분모)', '건물·공조 분류 포함(분자)']
    link['비중'] = (link.iloc[:, 1] / link.iloc[:, 0]).round(3)
    link.loc['2015–2019'] = [len(early), int(early['link'].sum()), round(early['link'].mean(), 3)]
    link.loc['2020–2024'] = [len(late), int(late['link'].sum()), round(late['link'].mean(), 3)]
    link.loc['2015–2024'] = [len(r), int(r['link'].sum()), round(r['link'].mean(), 3)]
    link.to_excel(writer, sheet_name=f'{tech}_건물연계')
    lt = r[r['link']]['apps'].explode().dropna().value_counts().head(10)
    lt.rename('건물·공조 분류 포함 패밀리 수').to_frame().to_excel(writer, sheet_name=f'{tech}_건물연계', startcol=6)
    r[r['link']][['Display Key', 'Application Date', 'Title', 'applicant_normalized', 'CPC Classifications']].to_excel(
        writer, sheet_name=f'{tech}_건물연계목록', index=False)
    pp = link.loc[['2015–2019', '2020–2024']]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(['2015-2019', '2020-2024'], pp['비중'] * 100, color=['#9db4d0', '#2f5d8c'])
    for i, (n, k) in enumerate(zip(pp.iloc[:, 0], pp.iloc[:, 1])):
        ax.text(i, pp['비중'].iloc[i] * 100 + 0.2, f'{int(k)} / {int(n)}', ha='center')
    ax.set_ylabel('% of families'); ax.set_ylim(0, max(10, pp['비중'].max() * 130))
    ax.set_title(f'{tech}: families also classified as building (E04B/F/H) or HVAC (F24F)', fontsize=9)
    plt.savefig(f'../figures/{tech}_4_building_link.png', dpi=200, bbox_inches='tight'); plt.close()

    # 4 협력 후보 매트릭스 (출원인 상위 20, 2015–2024)
    ex2 = a.explode('apps').dropna(subset=['apps'])
    rows = []
    for name in full.head(20).index:
        d = ex2[ex2['apps'] == name]
        b4, af = d['year'].between(2015, 2019).sum(), d['year'].between(2020, 2024).sum()
        rows.append({'출원인': name, '냉각 전문기업': name in COOLING_SPECIALISTS, '패밀리 수(2015–2024)': int(full[name]),
                     '2015–2019': int(b4), '2020–2024': int(af),
                     '증가율': round(af / b4 - 1, 2) if b4 >= 3 else '기준기간 3건 미만',
                     '평균 연간 피인용': round(d['ann_cite'].mean(), 2)})
    mat = pd.DataFrame(rows)
    mat.to_excel(writer, sheet_name=f'{tech}_협력후보', index=False)
    spec = rank_tbl[rank_tbl['냉각 전문기업']].head(10)
    spec.to_excel(writer, sheet_name=f'{tech}_냉각전문기업')
    mat['최근 5년 비중(2020–24 / 2015–24)'] = (mat['2020–2024'] / mat['패밀리 수(2015–2024)']).round(2)
    mat.to_excel(writer, sheet_name=f'{tech}_협력후보', index=False)
    plt.figure(figsize=(9, 6))
    q = mat['평균 연간 피인용'].fillna(0)
    yv = mat['최근 5년 비중(2020–24 / 2015–24)']
    plt.scatter(mat['패밀리 수(2015–2024)'], yv, s=30 + 300 * q / max(q.max(), 0.01), alpha=0.5,
                c=['tab:red' if s else 'tab:blue' for s in mat['냉각 전문기업']])
    for i, rr in mat.head(12).iterrows():
        plt.annotate(rr['출원인'][:20], (rr['패밀리 수(2015–2024)'], yv[i]), fontsize=7, xytext=(4, 4 if i % 2 else -9), textcoords='offset points')
    plt.xlabel('families 2015-2024 (size)'); plt.ylabel('share filed in 2020-2024 (momentum)')
    plt.title(f'{tech}: top-20 applicants (bubble = avg annual citations, red = cooling specialist, labels = top 12)')
    plt.savefig(f'../figures/{tech}_3_matrix.png', dpi=200, bbox_inches='tight'); plt.close()

    core = pd.read_csv('../handoff/US_핵심특허_팀원2반환.csv')
    core = core[core['technology'] == tech]
    core_apps = core['applicant_normalized'].apply(apps).explode().value_counts()
    def rank_of(w):  # 동점은 같은 순위 (1 + 나보다 많은 출원인 수)
        hit = [n for n in full.index if w in n]
        if not hit:
            return '2015–2024 출원 없음'
        k = int(full[hit[0]])
        return f"공동 {int((full > k).sum()) + 1}위 ({k}건)" if (full == k).sum() > 1 else f"{int((full > k).sum()) + 1}위 ({k}건)"
    signals = {'HHI(완전계수) ≥ 0.18': h_full >= 0.18, '핵심특허 10건 중 한 기업 3건 이상': int(core_apps.iloc[0]) >= 3,
               '신규 출원인 감소(2020–24 평균 < 2015–19 평균)': na_ < nb}
    summary.append({
        '기술': tech, '패밀리 수(2000–2024)': len(a), '패밀리 수(2015–2024)': len(r), '등록특허 수': len(g),
        '패밀리 증가율 2013–17 → 2018–22': growth.iloc[0]['증가율 (B/A−1)'],
        'S커브 판정': verdict, 'Logistic 단계(2021)': stages.get('Logistic'), 'Gompertz 단계(2021)': stages.get('Gompertz'),
        'HHI 완전계수 (0–1)': round(h_full, 4), 'HHI 분할계수 (0–1)': round(h_frac, 4), 'HHI ×10,000': round(h_full * 10000),
        'CR4': round(cr4, 3), '상위 4 출원인': ', '.join(full.head(4).index),
        '핵심특허 최다 보유': f'{core_apps.index[0]} ({int(core_apps.iloc[0])}건)',
        '신규 출원인 연평균 2015–19 → 2020–24': f'{nb:.1f} → {na_:.1f}',
        '참고 신호 수(팀 잠정 규칙)': int(sum(signals.values())),
        '참고 신호 내용': '; '.join(f"{k}: {'예' if v else '아니오'}" for k, v in signals.items()),
        '건물·공조 분류 비중 2015–19 → 2020–24': f"{early['link'].mean():.3f} → {late['link'].mean():.3f}",
        '건물·공조 분류 포함 상위 출원인': ', '.join(lt.head(3).index) if len(lt) else '없음',
        '고유 발명자 수 2015–19 → 2020–24': f"{inv_tbl.iloc[0, 0]} → {inv_tbl.iloc[1, 0]}",
        '비특허문헌 1건 이상 인용 비율 2000–14 / 15–19 / 20–24': ' / '.join(f'{x:.0%}' for x in npl_tbl['비특허문헌 1건 이상 비율']),
        '패밀리 동시출원 비율 CN·EP·JP·KR·WO': ' · '.join(f"{c} {jur_tbl.loc[c].iloc[0]:.0%}" for c in ['CN', 'EP', 'JP', 'KR', 'WO']),
        '미국에만 출원한 패밀리 비율': f"{jur_tbl.loc['미국에만 출원'].iloc[0]:.0%}",
        '삼성 순위': rank_of('SAMSUNG'), 'GRC 순위': rank_of('GRC'),
        '출원인 중 냉각 전문기업 최상위': f"{spec.index[0]} ({rank_of(spec.index[0])})" if len(spec) else '없음',
        'S커브 검증: 2000–18 적합 → 2021 누적 예측 오차율': ', '.join(f'{m} {e:+.0%}' for m, e in holdout_err.items()),
        '분류 경계 태그 패밀리 수': '; '.join(f'{k} {v}' for k, v in a['boundary_tag'].fillna('').value_counts().items() if k) or '없음'})

comp = pd.DataFrame(mix_all)
comp.to_excel(writer, sheet_name='CPC구성비_비교')
comp.rename(index=EN).plot(kind='barh', title='Share of families with each CPC group (2015-2024)')
plt.savefig('../figures/5_cpc_mix.png', dpi=200, bbox_inches='tight'); plt.close()
pd.DataFrame(summary).set_index('기술').T.to_excel(writer, sheet_name='요약')
pd.DataFrame({'CPC 그룹': list(GROUPS), '포함 코드(앞자리 일치)': [', '.join(v) for v in GROUPS.values()],
              '설명': ['H05K7/20254 전자기기용 냉각판, H01L23/473 반도체 패키지 액체 냉각, F28 열교환기 일반',
                     'H05K7/20236 전자기기 침지 냉각, H01L23/44 반도체 패키지 침지 냉각',
                     'H05K7/20272 냉각액 펌프·순환, H05K7/20281 냉각액 배관·연결, F04 펌프, F16L 배관',
                     'H05K7/207 랙·캐비닛 냉각 구조, H05K7/14 랙 장착 구조, G06F1/20 컴퓨터 냉각 수단',
                     'G05B·G05D 제어 시스템, G06F1/206 온도 기반 컴퓨터 제어, H05K7/20836 냉각 감시·제어',
                     'E04B 건물 구조, E04F 마감, E04H 특수 목적 건물(데이터센터 포함), F24F 공조. E04G(비계·거푸집) 제외',
                     'C09K5 열전달 매체, C10M 윤활·절연유']}).to_excel(writer, sheet_name='CPC정의', index=False)
pd.DataFrame({'항목': ['데이터', '검색일', '추이·HHI 등 단위', 'S커브 단위', '공동출원', '출원인 정규화', '건물 연계', 'CPC 구성비', '피인용', '분류 경계 표시', 'S커브 검증'],
              '정의': ['Lens.org 미국, 검색식 A(DLC)·B(액침), 출원일(Filed) 2000-01-01~2024-12-31', '2026-11-09',
                      'Lens simple family 1건 = 1, 최우선연도(처음 출원한 해) 기준. 강의: 우선권 주장 시 처음 출원 시점으로 판단', '등록특허 누적, 최우선연도 기준, 종료연도 2019/2020/2021 비교',
                      '완전계수 기본, 분할계수(1/출원인 수) 병기', 'clean.py: 회사명이 있으면 개인 발명자 제외, 개인만 있으면 최초 권리자(Owners), 계열 법인 통합표',
                      'CPC E04B·E04F·E04H·F24F가 함께 붙은 패밀리 비중 (proxy, 청구항 판정 아님)',
                      '패밀리 중 해당 그룹 코드를 하나라도 가진 비율 (그룹 간 중복 가능, 합 100% 아님)',
                      '연평균 피인용 = Cited by Patent Count / 공개 후 경과연수(최소 1년), 조회일 2026-11-09',
                      'clean.py의 boundary_tag 열: 분사·제트 냉각, 냉매·상변화 표현(2상 냉각 경계). 제외하지 않고 표시만 함',
                      '2000–2018로 적합해 2019–2021 누적을 예측(각 기술 S커브 시트 아래 표). 종료연도 2019/2020/2021 민감도와 함께 봄']}).to_excel(writer, sheet_name='정의', index=False)
writer.close()
print(pd.DataFrame(summary).set_index('기술').T.to_string())
