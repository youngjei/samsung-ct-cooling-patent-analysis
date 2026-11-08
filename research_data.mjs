// Research facts transcribed from the visible KIPRIS search results on 2026-11-08.
// This module contains the query protocol and source-backed interpretation, not a scraper.
export const observedDate = '2026-11-08';
export const kipris = 'https://www.kipris.or.kr/khome/search/searchResult.do';
const builders = 'AP=[삼성물산+현대건설+지에스건설+GS건설+디엘이앤씨+대림산업+대우건설+에스케이에코플랜트+에스케이건설+SK건설]';
const dc = '서버+데이터센터+"데이터 센터"+server+"data center"';
const liquid = '액침+침지+immersion+콜드플레이트+"cold plate"+수랭+수냉+액냉+"liquid cooling"+"direct liquid"';
const affiliateLiquid = '액침+침지+immersion+콜드플레이트+"cold plate"+수랭+수냉+액냉+"liquid cooling"';
export const queries = [
  ['Q1','삼성물산 광범위 냉각 탐색',21,`AP=[삼성물산]*(${dc})*(냉각+냉방+cooling)*AD=[20000101~20241231]`,'보조 탐색. 국내 결과 21; 건설사 비교 분모에는 사용하지 않음.'],
  ['Q2','건설사 6개 표본 / IT+액체 기술',8,`${builders}*(${dc})*(${liquid})*AD=[20000101~20241231]`,'기술·IT 키워드 전문 검색. 8개 행 모두 별도 기록.'],
  ['Q3','건설사 6개 표본 / 기술 제목·초록',38,`${builders}*(TL=[${liquid}]+AB=[${liquid}])*AD=[20000101~20241231]`,'IT 조건을 제거한 보완 탐색. Q2와 출원번호 중복 2개.'],
  ['Q4','건설사 / IT 제목·초록+냉각',30,`${builders}*(TL=[${dc}]+AB=[${dc}])*(냉각+냉방+공조+cooling)*AD=[20000101~20241231]`,'보조 검토. 일반 관리서버 노이즈 다수; 비교 분모에는 사용하지 않음.'],
  ['Q5','삼성전자·삼성SDS 별도 탐색',22,`AP=[삼성전자+삼성에스디에스+삼성SDS]*(${dc})*(TL=[${affiliateLiquid}]+AB=[${affiliateLiquid}])*AD=[20000101~20241231]`,'22개 기록. 액침 관련 4, 인접 칩 분사냉각 1, 나머지 17 제외. 삼성물산에 합산 금지.']
];
export const claims = [
  ['10-2552810','삼성물산·데이터빈 / 등록','독립항 1·10·12','슬롯을 통과하도록 공급·배출부를 배치. 항1은 배출홀과 멀수록 공급홀 직경 증가; 항10은 기포 유입 방지용 제2배출홀; 항12는 유체 정체 방지용 제3배출홀.','유량의 공간적 분배: 모든 서버에 냉각액이 충분히 흐르게 하는 장치 구조.','특정 구성 조합의 기술 사례. 모든 액침 방식 독점 또는 실증 절감률 증거는 아님.','https://patents.google.com/patent/KR102552810B1/ko'],
  ['10-2815358','삼성물산·데이터빈 / 등록','독립항 1·9; 종속항 3·4·7·8','대상물·유체 온도센서, 순환펌프, 프로세서. 대상물의 정상 온도변화 여부를 판별하고 정상일 때 온도에 따라 펌프 속도를 조절. 종속항에 부품 사용량·속도표·운영정보.','시간에 따른 운전 제어: 부하 변화에 맞춰 필요한 유량 공급.','청구항의 프로세서를 곧바로 AI로 부르면 안 됨. 이 특허만으로 장치 효율 우월성은 입증되지 않음.','https://patents.google.com/patent/KR102815358B1/ko'],
  ['10-2024-0121468','삼성전자 / 공개출원','독립항 1·13; 종속항 4·12','저장공간 안 펌프 어레이를 보드별로 개별 제어. 냉각이 필요한 보드와 대응 펌프를 선택해 유량 증가. 종속항에 작업량 기반 판단과 보드 간 격벽.','국부 유량 제어도 별도 개발 주제: 탱크 전체 유량 제어와 구별.','KIPRIS 서지·청구항 직접 열람. 삼성전자 출원이지 삼성물산 소유가 아님. 공개 청구항은 심사 과정에서 바뀔 수 있음.',kipris],
  ['10-2026-0007962','삼성SDS / 공개출원','독립항 1·11·17; 종속항 12·14','항1은 사용·미사용 공간을 나누는 격벽; 항11은 서버로 향하는 흐름을 제어하는 배플; 항17은 둘을 결합. 종속항은 고발열 지점에 유동을 유도.','서버가 없는 공간으로의 유동과 국부 고발열을 설계 문제로 다룸.','2024년 출원·2026년 공개. 삼성물산에 합산 금지. 국내 목적표집 사례이며 미국 상위 10건 분석은 아님.','https://patents.google.com/patent/KR20260007962A/ko']
];
export const partnerships = [
  ['삼성물산–데이터빈','공동출원·공동권리 + 개발 협력','2022·2023년 출원; 2025-09-11 기사','2건의 등록특허와 회사 공식 개발 협력 설명이 상호 보완.','공동개발 경험은 확인. 투자액·지분·독점계약은 이 자료로 확인되지 않음.','https://news.samsungcnt.com/en/features/engineering-construction/2025-09-building-the-backbone-of-the-ai-era-samsung-cts-data-center-business-team/'],
  ['삼성물산–GRC / 삼성벤처투자–GRC','전략적 사업협력 / 투자 주체 구별','2025-06-03 GRC 발표','Samsung C&T의 Business Collaboration Agreement와 Samsung Ventures 투자를 구분하여 발표.','삼성물산 직접 지분투자로 단정 금지. 투자액·지분율·특허 독점실시권은 확인되지 않음.','https://www.grcooling.com/press_releases/in-response-to-explosive-growth-in-liquid-cooling-demand-samsung-ventures-invests-in-grc-as-samsung-ct-forms-strategic-partnership-in-latest-funding-round/'],
  ['신성이엔지–데이터빈','외부 협업 사례','2025-03-14 회사 발표','신성이엔지가 데이터빈과 데이터센터 액침냉각 협력을 발표.','파트너가 다른 회사와도 협업한다는 사실. 삼성물산 계약의 구체적 독점 범위는 별도 확인.','https://www.shinsung.co.kr/board/board.php?bbsid=news&idx=418&pg=4'],
  ['LG전자–SK엔무브–GRC','외부 MOU·공동 검증','2025-10-28 회사 발표','냉각 설비·유체·액침 시스템을 결합하는 협력 사례.','공급망 파트너만 확보했다고 독점적 차별화가 보장되지는 않는다는 전략적 시사점.','https://www.lg.com/global/newsroom/b2b/product-and-solutions/lg-sk-enmove-and-grc-sign-mou-to-advance-liquid-immersion-cooling-solutions-for-ai-data-centers/']
];
export const portfolio = [
  ['삼성물산 단독','10-2013-0147448 / 10-1536655','DC 모듈·냉각·전력 구성','소멸(Ended)','통합 시공의 과거 기술 활동 근거; 현존 독점권·DLC로 표시 금지.','https://patents.google.com/patent/KR101536655B1/ko'],
  ['삼성물산·하이멕 공동','10-2013-0125468','DC 건물 에너지 소비량 평가','등록(검색목록)','계산·평가 인접기술. 액침 장치 특허 총수에 포함하지 않음.',kipris],
  ['삼성물산 단독','10-2023-0039605','DC 사업성 평가','거절(Rejected)','기획 단계 연구 흔적; 등록 보유특허 아님.',kipris]
];

// Supplementary search checks. These are separate retrieval routes, NOT additions
// to the original Q2/Q3 cohort of 44. Q8 is exploratory title screening only.
const buildersExpanded = 'AP=[삼성물산+현대건설+지에스건설+GS건설+엘지건설+LG건설+디엘이앤씨+대림산업+대우건설+에스케이에코플랜트+에스케이건설+SK건설]';
export const supplementaryQueries = [
 ['Q6','전자장비 냉각 IPC',3,`${buildersExpanded}*IPC=[H05K7/20]*AD=[20000101~20241231]`,'삼성물산 액침 2건 + 현대건설 DC 전력량계 1건. DC는 직류이며 데이터센터가 아님.'],
 ['Q7','전자장비·컴퓨터 냉각 IPC',4,`${buildersExpanded}*(IPC=[H05K7/20]+IPC=[G06F1/20])*AD=[20000101~20241231]`,'액침 2건, 기존 모듈러 DC 1건, 직류 전력량계 1건. Q6을 포함하므로 합산 금지.'],
 ['Q8','시설·공조 표현 확장',82,`${buildersExpanded}*(데이터센터+"데이터 센터"+"data center"+전산실+컴퓨터실+서버실+IDC)*(냉각+냉방+공조+방열+냉수+cooling)*AD=[20000101~20241231]`,'82건 제목 확인, 근접 후보 초록 추가 확인. 시설·건물 에너지·관리서버 노이즈가 많음. 모든 건 청구항 심사 또는 최종 관련특허 집합으로 사용하지 않음.']
];
export const classificationCheck = [
 ['1020220169453','삼성물산·데이터빈','침지 냉각 장치','Q6;Q7','핵심 액침','기존 포함 건 재확인'],
 ['1020230011622','삼성물산·데이터빈','침지 냉각 방식의 유량 제어장치 및 그 방법','Q6;Q7','핵심 액침','기존 포함 건 재확인'],
 ['1020130147448','삼성물산','데이터센터 확장모듈 및 이를 이용하여 모듈러 방식으로 데이터센터를 시공하는 방법','Q7','인접기술','시설 모듈 구성. 서버 직접 액체냉각과 구분'],
 ['1020170005313','현대건설','DC 전력량계','Q6;Q7','제외','직류 전력 측정용 션트 저항·방열판·팬. 데이터센터 냉각 특허가 아님']
];
export const boundaryChecks = [
 ['1020210189384;1020230108447','배터리 재사용·렌탈·ESS','Q8 초록 재확인','제외 유지','사용후 배터리와 PCS를 이용한 건설현장 전력 공급. 서버 액침·DLC가 아님'],
 ['1020220154834;1020230095369','연료전지 배열 활용 흡수식 냉방','Q8 초록','시설 냉방 후보로만 분리','연료전지 배기가스·흡수식 냉동기·냉각탑 구성. 서버 액침·콜드플레이트와 다름. 접힌 공동출원인 전체는 미확인'],
 ['1020200081012','GS건설 항온 폐열 지역냉난방','Q8 초록','시설 열관리 인접기술','히트펌프·제습냉방장치로 수요처 간 열 활용. 액침 핵심 건수에 포함하지 않음'],
 ['1020130138074','삼성물산 HVAC&R 에너지 예측·평가','Q8 초록','건물 에너지 인접기술','공조·열원·반송 에너지 예측과 경제성 평가. 서버 액침 성능의 실증 자료가 아님'],
 ['1020100057414','삼성물산 BEMS 냉동기 최적 운전','Q8 초록','건물 제어 인접기술','냉동기 상태정보와 COP 기반 제어. 서버 펌프 제어와 구분'],
 ['1020240102497','삼성물산 디지털 트윈 건물 에너지 관리','Q8 초록','건물 제어 인접기술','재실·구역 전력·공조·열원 운전과 디지털 트윈. DC 특화 또는 액침 AI 제어로 단정 금지']
];
