# -*- coding: utf-8 -*-
"""
Generate dashboard.html from CMUEAA_Master CSV.
Single-file static dashboard (Chart.js CDN, Power BI dark theme, Sarabun font).
Run: python3 generate_dashboard.py
"""
import pandas as pd
import json

MASTER = "/Users/chawanchiwarattanaphan/Desktop/Claude Code Data/CMUEAA Database/CMUEAA_Master_2026-06-11.csv"
OUT = "/Users/chawanchiwarattanaphan/Desktop/Claude Code Data/CMUEAA Database/dashboard.html"
ASOF = "11 มิถุนายน 2569"

m = pd.read_csv(MASTER, dtype=str).fillna("")

total = len(m)
active = int((m["สถานะสมาชิก (Active/Inactive)"] == "Active").sum())
registered = int((m["วันที่สมัครสมาชิก"] != "").sum())
phone = int((m["เบอร์โทรศัพท์"] != "").sum())
email = int((m["อีเมล"] != "").sum())
prov_known = int((m["จังหวัด"] != "").sum())

g = pd.to_numeric(m["รุ่นเกียร์"], errors="coerce").dropna().astype(int)
gear = {int(k): int(v) for k, v in g.value_counts().sort_index().items() if k >= 1}

dept_s = m["ภาควิชา"].str.strip()
dept = dept_s[dept_s != ""].value_counts().to_dict()
dept["ไม่ระบุภาควิชา"] = int((dept_s == "").sum())
dept = {("กลุ่ม CMU EAA (ไม่ระบุภาคจริง)" if k == "cmu eaa" else k): v for k, v in dept.items()}
dept = dict(sorted(dept.items(), key=lambda x: -x[1]))

gender = m["เพศ"].value_counts().to_dict()

prov = m["จังหวัด"]
prov_top = prov[prov != ""].value_counts().head(15).to_dict()

yr = (pd.to_datetime(m.loc[m["วันที่สมัครสมาชิก"] != "", "วันที่สมัครสมาชิก"], errors="coerce").dt.year + 543).dropna().astype(int)
reg_year = {str(int(k)): int(v) for k, v in yr.value_counts().sort_index().items()}

occ_s = m["กลุ่มอาชีพ"].str.strip()
occ = occ_s[occ_s != ""].value_counts().head(10).to_dict()

D = dict(gear=gear, dept=dept, gender=gender, prov=prov_top, reg=reg_year, occ=occ)

html = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CMUEAA Alumni Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#0f1419;--panel:#1a2026;--panel2:#222a32;--border:#2d3741;--text:#e8ecef;--muted:#8b98a5;--accent:#34d399;--warn:#fbbf24;--bad:#f87171;--blue:#60a5fa}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:'Sarabun',sans-serif;padding:24px}
.header{margin-bottom:24px}
.header h1{font-size:26px;font-weight:700}
.header .sub{color:var(--muted);font-size:14px;margin-top:4px}
.badge{display:inline-block;background:var(--panel2);border:1px solid var(--border);border-radius:20px;padding:2px 12px;font-size:12px;color:var(--accent);margin-left:8px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:24px}
.kpi{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px 18px}
.kpi .label{color:var(--muted);font-size:13px}
.kpi .value{font-size:28px;font-weight:700;margin-top:4px}
.kpi .pct{font-size:13px;color:var(--muted);margin-top:2px}
.kpi.green .value{color:var(--accent)} .kpi.blue .value{color:var(--blue)} .kpi.warn .value{color:var(--warn)} .kpi.bad .value{color:var(--bad)}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:18px}
.card h3{font-size:15px;font-weight:600;margin-bottom:4px}
.card .note{color:var(--muted);font-size:12px;margin-bottom:12px}
.span12{grid-column:span 12}.span8{grid-column:span 8}.span6{grid-column:span 6}.span4{grid-column:span 4}
@media(max-width:900px){.span8,.span6,.span4{grid-column:span 12}}
.chartbox{position:relative}
.insight{background:var(--panel2);border-left:3px solid var(--accent);border-radius:6px;padding:10px 14px;font-size:13px;margin-top:12px;color:#c8d2da}
.insight b{color:var(--accent)} .insight .w{color:var(--warn)} .insight .b{color:var(--bad)}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--border)}
th{color:var(--muted);font-weight:500}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.footer{color:var(--muted);font-size:12px;margin-top:24px;text-align:center}
</style>
</head>
<body>
<div class="header">
  <h1>ฐานข้อมูลศิษย์เก่า คณะวิศวกรรมศาสตร์ มช. <span class="badge">CMUEAA</span></h1>
  <div class="sub">ข้อมูลหลัง Data Cleansing &amp; Merge จากระบบ alumni.eng.cmu.ac.th — ณ __ASOF__</div>
</div>

<div class="kpis">
  <div class="kpi"><div class="label">สมาชิกทั้งหมด (ไม่ซ้ำ)</div><div class="value">__TOTAL__</div><div class="pct">หลังลบ spam 11 + รวมซ้ำ 106</div></div>
  <div class="kpi blue"><div class="label">สมัครผ่านระบบเอง</div><div class="value">__REG__</div><div class="pct">__REGPCT__% ของทั้งหมด</div></div>
  <div class="kpi warn"><div class="label">สมาชิกสถานะ Active</div><div class="value">__ACTIVE__</div><div class="pct">__ACTIVEPCT__% ของทั้งหมด</div></div>
  <div class="kpi green"><div class="label">เบอร์โทรติดต่อได้</div><div class="value">__PHONE__</div><div class="pct">__PHONEPCT__% (normalize แล้ว)</div></div>
  <div class="kpi green"><div class="label">อีเมลใช้ได้</div><div class="value">__EMAIL__</div><div class="pct">__EMAILPCT__%</div></div>
  <div class="kpi green"><div class="label">ระบุจังหวัดได้</div><div class="value">__PROV__</div><div class="pct">__PROVPCT__% (เดิม 16% → enrich จากรหัสไปรษณีย์)</div></div>
  <div class="kpi blue"><div class="label">LINE OA เข้าถึงได้</div><div class="value">5,289</div><div class="pct">34.2% ของสมาชิก (บล็อค 360)</div></div>
</div>

<div class="grid">
  <div class="card span12">
    <h3>การกระจายสมาชิกตามรุ่น (เกียร์ 1–57)</h3>
    <div class="note">จำนวนสมาชิกในฐานข้อมูลแยกตามรุ่น</div>
    <div class="chartbox" style="height:280px"><canvas id="cGear"></canvas></div>
    <div class="insight">รุ่น <b>36–42</b> มีข้อมูลมากที่สุด (600+ คน/รุ่น) ขณะที่รุ่น <span class="b">43–49 ลดฮวบเหลือ 72–357 คน/รุ่น</span> — ช่องว่างข้อมูลที่ควรเร่งเก็บ ส่วนรุ่น 50 กลับมาที่ 305 คน (ระบบลงทะเบียนกิจกรรมช่วยดึง)</div>
  </div>

  <div class="card span4">
    <h3>เพศ</h3>
    <div class="note">หลัง enrich จากสองแหล่งข้อมูล (รู้เพศ 58.6%)</div>
    <div class="chartbox" style="height:240px"><canvas id="cGender"></canvas></div>
  </div>
  <div class="card span8">
    <h3>ภาควิชา</h3>
    <div class="note">ระบุภาควิชาจริงได้เพียง 27% — ว่าง 64% และกลุ่ม CMU EAA อีก 9%</div>
    <div class="chartbox" style="height:240px"><canvas id="cDept"></canvas></div>
  </div>

  <div class="card span6">
    <h3>จังหวัด Top 15</h3>
    <div class="note">enrich จากรหัสไปรษณีย์ — coverage เพิ่มจาก 16.2% เป็น 73.6%</div>
    <div class="chartbox" style="height:300px"><canvas id="cProv"></canvas></div>
    <div class="insight"><b>เชียงใหม่ 3,708 คน</b> แซงกรุงเทพฯ (1,922) เมื่อใช้ข้อมูลรหัสไปรษณีย์ — ภาพเดิมที่ว่ากทม.อันดับ 1 มาจากข้อมูลจังหวัดที่กรอกเองเพียง 16%</div>
  </div>
  <div class="card span6">
    <h3>การสมัครสมาชิกรายปี (พ.ศ.)</h3>
    <div class="note">เฉพาะผู้สมัครผ่านระบบ 5,338 คน (34.5%) — ที่เหลือเป็นข้อมูล import</div>
    <div class="chartbox" style="height:300px"><canvas id="cReg"></canvas></div>
    <div class="insight">พีค <b>2560 (2,178)</b> และ <b>2565 (1,368)</b> | จุดต่ำสุด <span class="b">2567 เหลือ 31 คน</span> | ปี <b>2569 ฟื้นเป็น 60 คนในครึ่งปี</b> จากระบบลงทะเบียนกิจกรรม</div>
  </div>

  <div class="card span6">
    <h3>กลุ่มอาชีพ Top 10</h3>
    <div class="note">จากผู้ที่ระบุอาชีพ ~19% ของฐาน</div>
    <div class="chartbox" style="height:300px"><canvas id="cOcc"></canvas></div>
  </div>
  <div class="card span6">
    <h3>สถานะช่องทางสื่อสาร</h3>
    <div class="note">ความสามารถในการเข้าถึงสมาชิก 15,476 คน</div>
    <table>
      <tr><th>ช่องทาง</th><th class="num">เข้าถึงได้</th><th class="num">% ของสมาชิก</th></tr>
      <tr><td>อีเมล (ตรวจ format แล้ว)</td><td class="num">10,182</td><td class="num">65.8%</td></tr>
      <tr><td>เบอร์โทรศัพท์ (normalize แล้ว)</td><td class="num">7,765</td><td class="num">50.2%</td></tr>
      <tr><td>LINE OA (ทาร์เก็ตรีช)</td><td class="num">5,289</td><td class="num">34.2%</td></tr>
      <tr><td>ที่อยู่ไปรษณีย์ (มีรหัสไปรษณีย์)</td><td class="num">11,163</td><td class="num">72.1%</td></tr>
    </table>
    <div class="insight">LINE OA <span class="w">broadcast หยุดตั้งแต่ ต.ค. 2567</span> เพราะโควต้าแผนฟรี (300 ข้อความ/เดือน) ไม่พอส่งทั้งฐาน 5,289 คน — อีเมลคือช่องทางที่เข้าถึงได้กว้างที่สุดตอนนี้</div>
  </div>

  <div class="card span12">
    <h3>สรุปการทำ Data Cleansing (11 มิ.ย. 2569)</h3>
    <table>
      <tr><th>รายการ</th><th class="num">ก่อน</th><th class="num">หลัง</th><th>หมายเหตุ</th></tr>
      <tr><td>จำนวนรายชื่อ</td><td class="num">15,593</td><td class="num">15,476</td><td>ลบ spam/test 11 + รวมคนซ้ำ 106 (สมัคร 2 ครั้งด้วยรหัสพิมพ์ผิด)</td></tr>
      <tr><td>เบอร์โทรรูปแบบถูกต้อง</td><td class="num">4,635</td><td class="num">7,765</td><td>เติม 0 ที่ Excel ตัด + ลบขีด/วงเล็บ + แปลง +66</td></tr>
      <tr><td>ระบุจังหวัด</td><td class="num">16.2%</td><td class="num">73.6%</td><td>derive จากรหัสไปรษณีย์ 8,887 ราย</td></tr>
      <tr><td>ระบุเพศ</td><td class="num">20.2%</td><td class="num">58.6%</td><td>merge จากฐานข้อมูลเดิม + normalize ค่า</td></tr>
      <tr><td>อีเมล valid</td><td class="num">มีค่าเสียปน</td><td class="num">10,182 (100% valid)</td><td>ตัด format เสีย/ค่า "-" ออก</td></tr>
    </table>
  </div>
</div>

<div class="grid" style="margin-top:14px">
  <div class="card span12" id="analysis">
    <h3 style="font-size:18px">บทวิเคราะห์ฐานข้อมูลศิษย์เก่า CMUEAA</h3>
    <div class="note">Executive Analysis — จากการประมวลและ cleansing ข้อมูล ณ __ASOF__</div>

    <h4 style="margin:14px 0 6px;color:var(--accent)">1. ฐานข้อมูลใหญ่ แต่เป็น "ฐานรายชื่อ" มากกว่า "ฐานสมาชิกที่มีส่วนร่วม"</h4>
    <p style="font-size:13.5px;color:#c8d2da;line-height:1.7">ฐานข้อมูลหลัง cleansing มี 15,476 รายชื่อไม่ซ้ำ ครอบคลุมศิษย์เก่า 57 รุ่น แต่มีเพียง <b style="color:var(--blue)">5,338 คน (34.5%)</b> ที่สมัครสมาชิกผ่านระบบด้วยตนเอง ที่เหลือ 10,138 รายชื่อเป็นข้อมูลที่ import เข้าระบบโดยเจ้าตัวไม่เคย interact เลย และมีสถานะ Active เพียง <b style="color:var(--warn)">1,057 คน (6.8%)</b> ต่ำกว่ามาตรฐานสมาคมศิษย์เก่าทั่วไป (20–30%) ถึง 3–4 เท่า — โจทย์หลักไม่ใช่การหารายชื่อเพิ่ม แต่คือการเปลี่ยนรายชื่อที่มีอยู่ให้กลายเป็นสมาชิกที่มีส่วนร่วม</p>

    <h4 style="margin:14px 0 6px;color:var(--accent)">2. Engagement Funnel แคบลงเป็นชั้น ๆ</h4>
    <p style="font-size:13.5px;color:#c8d2da;line-height:1.7">15,476 รายชื่อ → 5,338 สมัครผ่านระบบ → 5,289 เป็นเพื่อน LINE OA → 1,057 Active → ผู้ร่วมกิจกรรมล่าสุด ~38 คน ตัวเลขสมัครผ่านระบบกับเพื่อน LINE ใกล้กันมาก บ่งชี้ว่าเป็นคนกลุ่มเดียวกัน — กลุ่มนี้คือ "แกนกลาง" ที่เข้าถึงได้จริงและควรรักษาไว้ ขณะที่อีก ~10,000 รายชื่อต้องการช่องทางใหม่ในการ re-engage (email คือช่องที่เหลืออยู่ช่องเดียวสำหรับคนกลุ่มนี้)</p>

    <h4 style="margin:14px 0 6px;color:var(--accent)">3. โครงสร้างรุ่นมีช่องโหว่ที่รุ่น 43–49</h4>
    <p style="font-size:13.5px;color:#c8d2da;line-height:1.7">รุ่น 36–42 (จบช่วง ~2543–2553) มีข้อมูลแน่นที่สุด 600+ คน/รุ่น แต่รุ่น 43–49 ลดฮวบเหลือ 72–357 คน/รุ่น — เป็นช่วงรอยต่อที่ระบบเก็บข้อมูลขาดความต่อเนื่อง ไม่ใช่เพราะนักศึกษาน้อยลง ส่วนรุ่น 50+ เริ่มกลับมา (305 คน) เพราะระบบลงทะเบียนกิจกรรมออนไลน์ช่วยเก็บอัตโนมัติ ยืนยันว่า "เก็บข้อมูล ณ จุดที่มีกิจกรรม" ได้ผลจริง</p>

    <h4 style="margin:14px 0 6px;color:var(--accent)">4. ภาพการกระจายตัวเปลี่ยนไปเมื่อข้อมูลถูกเติมเต็ม</h4>
    <p style="font-size:13.5px;color:#c8d2da;line-height:1.7">หลัง enrich จังหวัดจากรหัสไปรษณีย์ (coverage 16.2% → 73.6%) พบว่า <b>เชียงใหม่คือฐานใหญ่ที่สุด (3,708 คน)</b> ไม่ใช่กรุงเทพฯ (1,922) อย่างที่ข้อมูลเดิมชี้ และภาคเหนือรวมกันถือสัดส่วน &gt;50% สอดคล้องกับ demographics ของเพื่อน LINE OA (เหนือ 51.5%) — กิจกรรม physical ควร anchor ที่เชียงใหม่เป็นหลัก โดยมี chapter กทม. เป็นรอง</p>

    <h4 style="margin:14px 0 6px;color:var(--accent)">5. ช่องทางติดต่อ: อีเมลคือ asset ที่ใหญ่ที่สุดแต่ยังไม่ถูกใช้</h4>
    <p style="font-size:13.5px;color:#c8d2da;line-height:1.7">หลัง normalize เบอร์โทร (กู้เบอร์ที่ Excel ตัดเลข 0 ได้ 3,400+ เบอร์) เข้าถึงทางโทรศัพท์ได้ 7,765 คน (50.2%) และมีอีเมล valid 10,182 คน (65.8%) ขณะที่ LINE OA ซึ่งเคยเป็นช่องหลัก broadcast ไม่ได้ตั้งแต่ ต.ค. 2567 เพราะโควต้าแผนฟรี (300 ข้อความ/เดือน) ไม่พอส่งหาเพื่อน 5,289 คน — ระยะสั้นควรใช้ email campaign เป็นช่องหลัก (ต้นทุนต่ำ เข้าถึง 2 เท่าของ LINE) ระยะกลางจึงตัดสินใจเรื่องอัปเกรดแผน LINE (~1,200 บาท/เดือน)</p>

    <h4 style="margin:14px 0 6px;color:var(--accent)">6. คุณภาพข้อมูลที่ยังเป็นหนี้ค้าง</h4>
    <p style="font-size:13.5px;color:#c8d2da;line-height:1.7">ข้อมูลที่ยังขาดมาก: ภาควิชา (ว่าง 64.3% + กลุ่ม CMU EAA อีก 8.6%), วันเกิด (ว่าง 94%), อาชีพ (ว่าง 80.5%) — สามอย่างนี้กรอกแทนกันไม่ได้ ต้องให้เจ้าตัวอัปเดตเอง ข้อเสนอคือผูกการอัปเดตข้อมูลเข้ากับสิ่งที่สมาชิกอยากได้ เช่น ลงทะเบียนกิจกรรม รับสิทธิพิเศษ หรือ directory ค้นหาเพื่อนร่วมรุ่น</p>

    <div class="insight" style="margin-top:16px"><b>ข้อเสนอเชิงกลยุทธ์ 5 ข้อ:</b><br>
    1. Email re-engagement campaign หาสมาชิก 10,182 คนที่มีอีเมล — เป้าหมายดึงกลับมาอัปเดตข้อมูล + แอด LINE<br>
    2. ตัดสินใจแผน LINE OA (อัปเกรด Basic หรือใช้ targeted broadcast ≤300/เดือน + LINE VOOM)<br>
    3. แคมเปญ "ยืนยันตัวตน" ผ่าน LIFF ผูก LINE userId ↔ รหัสนักศึกษา เพื่อ map เพื่อน 5,289 คนเข้าฐานข้อมูล<br>
    4. เร่งเก็บข้อมูลรุ่น 43–49 ผ่านตัวแทนรุ่น (ช่องโหว่ใหญ่สุดของฐาน)<br>
    5. ตั้ง data governance: validation ตอนกรอก, รอบ review รายไตรมาส, ห้าม import โดยไม่มี dedup</div>
  </div>
</div>

<div class="footer">CMUEAA Alumni Dashboard — สร้างจาก CMUEAA_Master_2026-06-11.csv | อัปเดต __ASOF__</div>

<script>
const D = __DATA__;
Chart.defaults.color = '#8b98a5';
Chart.defaults.font.family = 'Sarabun';
Chart.defaults.borderColor = '#2d3741';
const GRID = {color:'#222a32'};

new Chart(document.getElementById('cGear'), {type:'bar', data:{
  labels:Object.keys(D.gear), datasets:[{data:Object.values(D.gear),
  backgroundColor:Object.keys(D.gear).map(k=>{const g=+k; return (g>=43&&g<=49)?'#f87171':(g>=36&&g<=42)?'#34d399':'#3b82f6'}), borderRadius:3}]},
  options:{plugins:{legend:{display:false}}, maintainAspectRatio:false,
  scales:{x:{grid:{display:false},ticks:{autoSkip:true,maxRotation:0}},y:{grid:GRID}}}});

new Chart(document.getElementById('cGender'), {type:'doughnut', data:{
  labels:Object.keys(D.gender), datasets:[{data:Object.values(D.gender),
  backgroundColor:['#3b82f6','#475569','#ec4899'], borderColor:'#1a2026', borderWidth:3}]},
  options:{maintainAspectRatio:false, plugins:{legend:{position:'bottom'}}, cutout:'62%'}});

new Chart(document.getElementById('cDept'), {type:'bar', data:{
  labels:Object.keys(D.dept), datasets:[{data:Object.values(D.dept),
  backgroundColor:Object.keys(D.dept).map(k=>k.includes('ไม่ระบุ')?'#475569':k.includes('CMU EAA')?'#fbbf24':'#34d399'), borderRadius:3}]},
  options:{indexAxis:'y', plugins:{legend:{display:false}}, maintainAspectRatio:false,
  scales:{x:{grid:GRID},y:{grid:{display:false},ticks:{font:{size:11}}}}}});

new Chart(document.getElementById('cProv'), {type:'bar', data:{
  labels:Object.keys(D.prov), datasets:[{data:Object.values(D.prov), backgroundColor:'#60a5fa', borderRadius:3}]},
  options:{indexAxis:'y', plugins:{legend:{display:false}}, maintainAspectRatio:false,
  scales:{x:{grid:GRID},y:{grid:{display:false},ticks:{font:{size:11}}}}}});

new Chart(document.getElementById('cReg'), {type:'bar', data:{
  labels:Object.keys(D.reg), datasets:[{data:Object.values(D.reg),
  backgroundColor:Object.keys(D.reg).map(y=>y==='2567'?'#f87171':y==='2569'?'#34d399':'#3b82f6'), borderRadius:3}]},
  options:{plugins:{legend:{display:false}}, maintainAspectRatio:false,
  scales:{x:{grid:{display:false}},y:{grid:GRID}}}});

new Chart(document.getElementById('cOcc'), {type:'bar', data:{
  labels:Object.keys(D.occ), datasets:[{data:Object.values(D.occ), backgroundColor:'#a78bfa', borderRadius:3}]},
  options:{indexAxis:'y', plugins:{legend:{display:false}}, maintainAspectRatio:false,
  scales:{x:{grid:GRID},y:{grid:{display:false},ticks:{font:{size:11}}}}}});
</script>
</body>
</html>"""

def fmt(n): return f"{n:,}"
def pct(n): return f"{n/total*100:.1f}"

postal = int((m["รหัสไปรษณีย์"] != "").sum())
html = (html
    .replace("__ASOF__", ASOF)
    .replace("__TOTAL__", fmt(total))
    .replace("__REGPCT__", pct(registered)).replace("__REG__", fmt(registered))
    .replace("__ACTIVEPCT__", pct(active)).replace("__ACTIVE__", fmt(active))
    .replace("__PHONEPCT__", pct(phone)).replace("__PHONE__", fmt(phone))
    .replace("__EMAILPCT__", pct(email)).replace("__EMAIL__", fmt(email))
    .replace("__PROVPCT__", pct(prov_known)).replace("__PROV__", fmt(prov_known))
    .replace("__DATA__", json.dumps(D, ensure_ascii=False)))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written {OUT} ({len(html)//1024} KB) | postal={postal}")
