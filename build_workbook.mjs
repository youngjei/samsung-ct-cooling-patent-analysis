import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
import {queries, claims, partnerships, portfolio, kipris, observedDate} from './research_data.mjs';
const base = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(base,'outputs','team2_20261108');
await fs.mkdir(out,{recursive:true});
function readTSV(txt){const lines=txt.trim().split('\n');const headers=lines.shift().split('\t');return lines.map(line=>Object.fromEntries(line.split('\t').map((v,i)=>[headers[i],v])));}
function applicationLabel(n){return n.replace(/^(\d{2})(\d{4})(\d{7})$/,'$1-$2-$3');}
const builder = readTSV(await fs.readFile(path.join(base,'records_builders.tsv'),'utf8'));
const affiliate = readTSV(await fs.readFile(path.join(base,'records_affiliates.tsv'),'utf8'));
if(builder.length!==44 || new Set(builder.map(x=>x.application)).size!==44) throw Error('Builder record reconciliation failed');
if(affiliate.length!==22 || new Set(affiliate.map(x=>x.application)).size!==22) throw Error('Affiliate record reconciliation failed');
for(const [qid,expected] of [['Q2',8],['Q3',38]]) if(builder.filter(x=>x.query_ids.split(';').includes(qid)).length!==expected) throw Error(qid+' failed');
const counts=Object.fromEntries(['액침 포함','인접기술','제외'].map(x=>[x,builder.filter(r=>r.decision===x).length]));
if(counts['액침 포함']!==2||counts['인접기술']!==1||counts['제외']!==41) throw Error('Screening reconciliation failed');
const wb=Workbook.create();
const sheets=Object.fromEntries(['건설사 비교','삼성 포트폴리오','청구항 비교','협력 근거','건설사 기록','계열사 기록','검색기록'].map(n=>[n,wb.worksheets.add(n)]));
const navy='#203864', blue='#EAF0FA', gray='#667085';
function init(sh,widths,lastRow){sh.showGridLines=false; const r=sh.getRangeByIndexes(0,0,lastRow,widths.length);r.format.font={name:'Arial',size:11,color:'#182230'};r.format.verticalAlignment='center';r.format.rowHeight=26;widths.forEach((w,i)=>sh.getRangeByIndexes(0,i,lastRow,1).format.columnWidth=w);}
function table(sh,row,headers,data,widths,rowHeight=54,name){init(sh,widths,row+data.length+2);sh.getRangeByIndexes(row-1,0,1,headers.length).values=[headers];if(data.length) sh.getRangeByIndexes(row,0,data.length,headers.length).values=data;const r=sh.getRangeByIndexes(row-1,0,data.length+1,headers.length);r.format.wrapText=true;r.format.verticalAlignment='top';r.format.rowHeight=rowHeight;const hr=sh.getRangeByIndexes(row-1,0,1,headers.length);hr.format.fill=navy;hr.format.font={name:'Arial',size:11,bold:true,color:'#FFFFFF'};hr.format.rowHeight=30;hr.format.horizontalAlignment='center';for(let i=0;i<data.length;i++) if(i%2===1)sh.getRangeByIndexes(row+i,0,1,headers.length).format.fill='#F3F6FA';if(name)sh.tables.add(r.address??`${'A'}${row}:${String.fromCharCode(64+headers.length)}${row+data.length}`,true,name);sh.freezePanes.freezeRows(row);}
function title(sh,t){sh.getRange('A2').values=[[t]];sh.getRange('A2').format.font={name:'Arial',size:16,bold:true,color:navy};sh.getRange('A2').format.wrapText=false;sh.getRange('A2').format.rowHeight=28;}

const b=sheets['건설사 기록'];
table(b,1,['출원번호','출원일','발명 명칭','출원인(검색목록)','상태(검색일)','검색ID','비교 묶음','선별','판단 이유','검토 근거'],builder.map(r=>[applicationLabel(r.application),r.filing_date,r.title,r.applicants,r.status,r.query_ids,r.company_bucket,r.decision,r.reason,r.basis]),[23,14,54,38,16,12,23,16,47,32],72,'BuilderRecords');
b.getRange('A2:A45').setNumberFormat('@');
const a=sheets['계열사 기록'];
table(a,1,['출원번호','표시 출원일','발명 명칭','출원인','상태(검색일)','선별','판단 이유'],affiliate.map(r=>[applicationLabel(r.application),r.filing_date,r.title,r.applicant,r.status,r.decision,r.reason]),[23,14,62,20,18,16,62],72,'AffiliateRecords');a.getRange('A2:A23').setNumberFormat('@');

const comp=sheets['건설사 비교'];init(comp,[28,16,16,16,16,66],28);title(comp,'국내 건설사 표본 비교');comp.tabColor=navy;
comp.getRange('A4').values=[['2000–2024년 출원 / KIPRIS 국내 특허 / 검색일 '+observedDate]];comp.getRange('A4').format.font={italic:true,color:gray};
comp.getRange('A6:F6').values=[['비교 기업','액침 확인(건)','DLC 확인(건)','인접기술(건)','후보(건)','해석 범위']];
comp.getRange('A6:F6').format={fill:navy,font:{name:'Arial',size:11,color:'#FFFFFF',bold:true},wrapText:true,rowHeight:36};
const names=['삼성물산','현대건설','GS건설','DL계열(옛 대림산업)','대우건설','SK에코플랜트'];
names.forEach((n,i)=>{const row=7+i;comp.getRange(`A${row}`).values=[[n]];comp.getRange(`B${row}:E${row}`).formulas=[[
 `=COUNTIFS('건설사 기록'!$G$2:$G$45,A${row},'건설사 기록'!$H$2:$H$45,"액침 포함")`,
 `=COUNTIFS('건설사 기록'!$G$2:$G$45,A${row},'건설사 기록'!$H$2:$H$45,"DLC 포함")`,
 `=COUNTIFS('건설사 기록'!$G$2:$G$45,A${row},'건설사 기록'!$H$2:$H$45,"인접기술")`,
 `=COUNTIFS('건설사 기록'!$G$2:$G$45,A${row})`]];comp.getRange(`F${row}`).values=[[i===0?'액침 2건 모두 데이터빈 공동등록. 인접 1건은 소멸.':i===3?'디엘이앤씨·옛 대림산업 검색. 후보 2건은 디엘 주식회사; 현 권리 자동 귀속 금지.':'이 검색에서 액침·DLC 해당 건 미확인. 특허·기술역량 부재를 뜻하지 않음.']];});
comp.getRange('A7:F12').format.wrapText=true;comp.getRange('A7:F12').format.rowHeight=52;comp.getRange('B7:E12').setNumberFormat('0');
comp.getRange('A14').values=[['선별 흐름(출원번호 중복 제거)']];comp.getRange('A14').format.font.bold=true;
comp.getRange('A15:E15').values=[['Q2 검색','Q3 보완검색','중복','고유 후보','일차 제외']];
comp.getRange('A16:C16').formulas=[['=COUNTIFS(\'건설사 기록\'!F2:F45,"Q2")+C16','=COUNTIFS(\'건설사 기록\'!F2:F45,"Q3")+C16','=COUNTIFS(\'건설사 기록\'!F2:F45,"Q2;Q3")']];
comp.getRange('D16:E16').formulas=[['=A16+B16-C16','=COUNTIFS(\'건설사 기록\'!H2:H45,"제외")']];
comp.getRange('A15:E16').format.fill=blue;
const lines=[
 '표본: 삼성물산·현대건설·GS건설·DL이앤씨(옛 대림산업 포함)·대우건설·SK에코플랜트.',
 '전국 순위가 아님. 0은 선택한 검색식·기간에서 확인되지 않았다는 뜻.',
 '독립 국내 출원번호를 단위로 집계. 등록특허 총수·특허 패밀리 수·시장점유율과 다름.',
 'DLC는 칩/콜드플레이트 직접액체냉각 기준. 건물 냉수배관만으로 DLC에 넣지 않음.',
 '고유 후보 44건 = 액침 2건 + 인접 모듈러 DC 1건 + 일차 제외 41건.',
 '검색식·분류 근거는 검색기록/건설사 기록에 보존. 과거 144→114 수치는 재사용하지 않음.'
];lines.forEach((t,i)=>{comp.getRange(`A${19+i}`).values=[[t]];comp.getRange(`A${19+i}`).format.wrapText=false;});

const p=sheets['삼성 포트폴리오'];
table(p,6,['귀속','유형','확인 수(건)','핵심 의미','과장하면 안 되는 점'],[
 ['삼성물산·데이터빈','액침 / 공동등록',null,'10-2552810: 유로 / 10-2815358: 펌프 제어','삼성물산 단독 특허 또는 전체 냉각 특허 총수 아님.'],
 ['삼성SDS','액침 관련 공개출원',null,'격벽·배플 / 국소 소화 / 히트싱크','삼성물산에 합산 금지. 2024년 출원, 2026년 공개.'],
 ['삼성전자','액침 공개출원',null,'보드별 펌프 어레이 제어','삼성물산에 합산 금지. 공개상태는 등록과 다름.'],
 ['삼성전자','칩 분사냉각 인접출원',null,'칩 양면 노즐·배출 경로','콜드플레이트 DLC나 서버 액침과 무조건 합치지 않음.']
],[28,30,16,63,65],72,'Portfolio');title(p,'삼성물산과 계열사는 별도 집계');
p.getRange('C7').formulas=[["='건설사 비교'!B7"]];p.getRange('C8').formulas=[['=COUNTIFS(\'계열사 기록\'!D2:D23,"삼성에스디에스",\'계열사 기록\'!F2:F23,"액침 포함")']];p.getRange('C9').formulas=[['=COUNTIFS(\'계열사 기록\'!D2:D23,"삼성전자",\'계열사 기록\'!F2:F23,"액침 포함")']];p.getRange('C10').formulas=[['=COUNTIFS(\'계열사 기록\'!D2:D23,"삼성전자",\'계열사 기록\'!F2:F23,"인접기술")']];
p.getRange('A13').values=[['삼성물산의 추가 인접기술 — 위 액침 수에 합산하지 않음']];
p.getRange('A15:F15').values=[['귀속','번호','기술','검색상태','사용 가능한 해석','출처']];p.getRange('A16:F18').values=portfolio;p.getRange('A15:F18').format.wrapText=true;p.getRange('A16:F18').format.rowHeight=88;p.getRange('F1:F18').format.columnWidth=60;p.getRange('A15:F15').format.fill=blue;

const c=sheets['청구항 비교'];table(c,5,['번호','귀속·상태','검토 청구항','구성요소 요약','해결 문제','해석 한계','원문'],claims,[21,28,28,75,49,65,65],140,'ClaimComparison');title(c,'국내 목적표집 4건의 청구항 비교');c.getRange('A3').values=[['미국 Top 10이 아님. 기술 구성의 비교이며 침해·유효성 판단이 아님.']];
const part=sheets['협력 근거'];table(part,5,['당사자','관계 종류','근거 시점','확인 사실','한계·시사점','1차 출처'],partnerships,[38,33,30,70,70,75],120,'PartnershipEvidence');title(part,'공동개발·사업협력·투자는 구별');

const q=sheets['검색기록'];table(q,6,['ID','목적','국내 결과(건)','실제 검색식','기록 방식'],queries,[10,34,18,135,75],120,'QueryLog');title(q,'KIPRIS 검색 재현 정보');q.getRange('A4').values=[['검색일 2026-11-08 / 국내 특허 / 행정상태 전체 / 실용신안 제외(Q2~Q5)']];
const protocol=[
 ['집계 단위','국내 출원번호. 공개공보와 등록공보를 별도 발명으로 중복 계산하지 않음.'],
 ['관할·기간','국내(KR), AD 20000101~20241231. 국가 전체의 2026년 보유권리 총수는 아님.'],
 ['선별 방식','Q2·Q3 합집합 44건: 제목 중심 1차 선별; Q2 초록 및 포함 2건/경계 모듈러 1건 청구항 추가 검토.'],
 ['알려진 사례 검증','기존 삼성물산 2건 모두 Q2·Q3에서 재검색. 2/2 회수는 전체 재현율 100%를 뜻하지 않음.'],
 ['임의 50건 검증','미실시. 건설사 후보는 고유 44건이고 전부 1차 선별. 국가 전체 특허 검색 정확도로 보고하지 않음.'],
 ['회사 정규화','GS·SK 옛 표기 포함. 대림산업→DL 분할 관련 후보는 디엘이앤씨 현 권리에 자동 귀속시키지 않음.'],
 ['공개 지연','현재 검색 시 확인 가능한 2024년까지 출원. 2025~2026년 신규 출원 제외; 미공개 누락 가능.'],
 ['외삽 제한','0건은 미확인. 전체 냉각 포트폴리오·실제 성능·매출·미국 기술수명주기·AHP 점수로 외삽 금지.'],
 ['데이터 접근','KIPRIS 화면 결과를 전사. 회원 전용 다운로드를 사용한 공식 일괄 Excel export는 아님.'],
 ['검색주소',kipris]
];q.getRange('A13:B22').values=protocol;q.getRange('A13:A22').format.columnWidth=34;q.getRange('B13:E22').format.columnWidth=34; // restored below: query column remains wide
q.getRange('D1:D22').format.columnWidth=135;q.getRange('E1:E22').format.columnWidth=75;
q.getRange('B13:B22').format.wrapText=false;
// Keep the evidence sheets compact; these are working tables, not slide cards.
comp.getRange('A6:F6').format.horizontalAlignment='center';
comp.getRange('A7:F12').format.rowHeight=38;
p.getRange('A7:E10').format.rowHeight=42;
p.getRange('A16:F18').format.rowHeight=48;
b.getRange('A2:J45').format.rowHeight=46;
b.getRange('A7:J7').format.rowHeight=72;
a.getRange('A2:G23').format.rowHeight=46;
c.getRange('A6:G9').format.rowHeight=74;
part.getRange('A6:F9').format.rowHeight=76;
q.getRange('A7:E11').format.rowHeight=68;
q.getRange('A1:A22').format.columnWidth=26;
q.getRange('B1:B22').format.columnWidth=30;
q.getRange('C1:C22').format.columnWidth=18;
for(const sh of Object.values(sheets)) for(const t of sh.tables.items) t.style='TableStyleMedium2';
wb.recalculate();
const funnel=comp.getRange('A16:E16').values[0].map(Number);
if(JSON.stringify(funnel)!==JSON.stringify([8,38,2,44,41])) throw Error('Formula reconciliation failed: '+JSON.stringify(funnel));
if(b.getRange('A3').values[0][0]!=='10-2022-0169453') throw Error('Application identifier changed');
console.log((await wb.inspect({kind:'region',sheetId:'건설사 비교',range:'A6:F16',maxChars:6000,tableMaxRows:12,tableMaxCols:6})).ndjson);
console.log((await wb.inspect({kind:'region',sheetId:'삼성 포트폴리오',range:'A6:E10',maxChars:3500})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!',options:{useRegex:true,maxResults:20},maxChars:2000})).ndjson);
const result=await SpreadsheetFile.exportXlsx(wb);await result.save(path.join(out,'팀원2_국내특허_근거표.xlsx'));
for(const name of Object.keys(sheets)){
 try {const preview=await wb.render({sheetName:name,range:name==='건설사 기록'?'A1:J12':name==='계열사 기록'?'A1:G12':undefined,autoCrop:'all',scale:1,format:'png'});await fs.writeFile(path.join(out,name+'_검수.png'),new Uint8Array(await preview.arrayBuffer()));}
 catch(e){console.log('RENDER_ERROR '+name+': '+e.message);}
}
await fs.writeFile(path.join(out,'validation.json'),JSON.stringify({observedDate,builderRecords:builder.length,query2:8,query3:38,overlap:2,screening:counts,affiliateRecords:affiliate.length,affiliateIncluded:affiliate.filter(r=>r.decision==='액침 포함').length,companyResults:names.map(n=>({company:n,candidates:builder.filter(r=>r.company_bucket===n).length,immersion:builder.filter(r=>r.company_bucket===n&&r.decision==='액침 포함').length})),source:kipris},null,2));
console.log('OUTPUT '+path.join(out,'팀원2_국내특허_근거표.xlsx'));
