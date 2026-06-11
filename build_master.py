# -*- coding: utf-8 -*-
"""
CMUEAA Master Builder — merge backend (alumni.eng.cmu.ac.th) + CSV (Entaneer_Alumni.csv)
into one cleansed, deduplicated master file with normalized phones.
Run: python3 build_master.py
Inputs:  /tmp/backend_all.csv (from admin export), Entaneer_Alumni.csv
Outputs: CMUEAA_Master_<date>.csv/.xlsx, CMUEAA_Removed_<date>.csv, stats json on stdout
"""
import pandas as pd
import re, json

DATE = "2026-06-11"
DIR = "/Users/chawanchiwarattanaphan/Desktop/Claude Code Data/CMUEAA Database"

be = pd.read_csv("/tmp/backend_all.csv", dtype=str).fillna("")
cs = pd.read_csv(f"{DIR}/Entaneer_Alumni.csv", dtype=str).fillna("")

# ---------- helpers ----------
ZW = re.compile(r"[​‌‍﻿ ]")
def clean_text(s):
    s = ZW.sub("", str(s))
    s = re.sub(r"\s+", " ", s).strip()
    return s

POSTCODE_PROVINCE = {
 "10":"กรุงเทพมหานคร","11":"นนทบุรี","12":"ปทุมธานี","13":"พระนครศรีอยุธยา","14":"อ่างทอง",
 "15":"ลพบุรี","16":"สิงห์บุรี","17":"ชัยนาท","18":"สระบุรี","20":"ชลบุรี","21":"ระยอง",
 "22":"จันทบุรี","23":"ตราด","24":"ฉะเชิงเทรา","25":"ปราจีนบุรี","26":"นครนายก","27":"สระแก้ว",
 "30":"นครราชสีมา","31":"บุรีรัมย์","32":"สุรินทร์","33":"ศรีสะเกษ","34":"อุบลราชธานี",
 "35":"ยโสธร","36":"ชัยภูมิ","37":"อำนาจเจริญ","38":"บึงกาฬ","39":"หนองบัวลำภู","40":"ขอนแก่น",
 "41":"อุดรธานี","42":"เลย","43":"หนองคาย","44":"มหาสารคาม","45":"ร้อยเอ็ด","46":"กาฬสินธุ์",
 "47":"สกลนคร","48":"นครพนม","49":"มุกดาหาร","50":"เชียงใหม่","51":"ลำพูน","52":"ลำปาง",
 "53":"อุตรดิตถ์","54":"แพร่","55":"น่าน","56":"พะเยา","57":"เชียงราย","58":"แม่ฮ่องสอน",
 "60":"นครสวรรค์","61":"อุทัยธานี","62":"กำแพงเพชร","63":"ตาก","64":"สุโขทัย","65":"พิษณุโลก",
 "66":"พิจิตร","67":"เพชรบูรณ์","70":"ราชบุรี","71":"กาญจนบุรี","72":"สุพรรณบุรี","73":"นครปฐม",
 "74":"สมุทรสาคร","75":"สมุทรสงคราม","76":"เพชรบุรี","77":"ประจวบคีรีขันธ์","80":"นครศรีธรรมราช",
 "81":"กระบี่","82":"พังงา","83":"ภูเก็ต","84":"สุราษฎร์ธานี","85":"ระนอง","86":"ชุมพร",
 "90":"สงขลา","91":"สตูล","92":"ตรัง","93":"พัทลุง","94":"ปัตตานี","95":"ยะลา","96":"นราธิวาส",
}

def normalize_phones(raw):
    """Return (primary, extra, invalid_raw). Primary = first valid Thai number 0XXXXXXXX(X)."""
    raw = clean_text(raw)
    if not raw or raw in ("-", "–"):
        return "", "", ""
    # split multiple numbers
    tokens = re.split(r"[,/;]|และ|\sor\s", raw)
    valid, extra, invalid = [], [], []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        intl = t.startswith("+") and not re.sub(r"\D", "", t).startswith("66")
        d = re.sub(r"\D", "", t)
        if not d:
            continue
        if d.startswith("66") and len(d) in (11, 12):       # +66 / 66 international
            d = "0" + d[2:]
        if len(d) == 9 and not d.startswith("0"):            # Excel stripped leading 0
            d = "0" + d
        if len(d) == 10 and d.startswith("0") and d[1] in "689":   # mobile
            valid.append(d)
        elif len(d) == 9 and d.startswith("0") and d[1] in "234567":  # landline
            valid.append(d)
        elif len(d) == 10 and d.startswith("0"):
            valid.append(d)                                   # other 10-digit 0x
        elif intl:
            extra.append(t)                                   # foreign number, keep as-is
        else:
            invalid.append(t)
    primary = valid[0] if valid else ""
    extras = valid[1:] + extra
    return primary, "; ".join(extras), "; ".join(invalid)

def normalize_gender(*vals):
    for v in vals:
        v = clean_text(v).lower()
        if v in ("ชาย", "male", "m"): return "ชาย"
        if v in ("หญิง", "female", "f"): return "หญิง"
    return "ไม่ระบุ"

EMAIL_RE = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")
def normalize_email(*vals):
    for v in vals:
        v = clean_text(v).lower().rstrip(".")
        if v and EMAIL_RE.match(v):
            return v
    return ""

# ---------- prepare keys ----------
be["sid"] = be["รหัสสมาชิก"].map(clean_text)
cs["sid"] = cs["รหัสนักศึกษา"].map(clean_text)
cs_dedup = cs[cs["sid"] != ""].drop_duplicates(subset="sid", keep="first")
cs_map = cs_dedup.set_index("sid")

# ---------- remove spam/test records ----------
SPAM_SIDS = {
    "1206129",    # ทีเอ็มเอ ดิจิทัล (company/test, gear 0)
    "1406129",    # ทดสอบ เทส
    "3706706",    # ทดสอบ ระบบลงทะเบียน
    "3706888",    # สมชาย ใจดี (placeholder test, reg 2026-03-02)
    "2234568",    # สายน้ำทิพย์ ทดสอบ (schoolwebthailand test 2016)
    "650600001",  # test test
    "2244", "4564", "5136", "1815",  # Barnypok x4 (form-spam bot)
}
removed = be[be["sid"].isin(SPAM_SIDS) | (be["sid"] == "")].copy()
removed["เหตุผลที่ลบ"] = removed["sid"].map(
    lambda s: "spam/test record" if s in SPAM_SIDS else "ไม่มีรหัสนักศึกษา/ไม่มีชื่อ")
work = be[~be.index.isin(removed.index)].copy()

# ---------- merge + normalize ----------
rows = []
stats = {"phone_fixed_from_csv": 0, "gender_from_csv": 0, "email_from_csv": 0,
         "dept_from_csv": 0, "prov_from_field": 0, "prov_from_postcode": 0,
         "prov_from_address": 0, "phone_invalid": 0}

prov_names = sorted(POSTCODE_PROVINCE.values(), key=len, reverse=True) + ["กรุงเทพ"]

for _, r in work.iterrows():
    sid = r["sid"]
    c = cs_map.loc[sid] if sid in cs_map.index else None

    gear = clean_text(r["รุ่นเกียร์"])
    dept = clean_text(r["ภาควิชา"])
    if not dept and c is not None:
        dept = clean_text(c["ภาควิชา"])
        if dept: stats["dept_from_csv"] += 1

    # phone: backend first; if no valid primary, try CSV
    p1, p_extra, p_inv = normalize_phones(r["เบอร์โทรศัพท์ ที่ติดต่อได้"])
    if not p1 and c is not None:
        cp1, cp_extra, cp_inv = normalize_phones(c["เบอร์โทรศัพท์"])
        if cp1:
            p1, stats["phone_fixed_from_csv"] = cp1, stats["phone_fixed_from_csv"] + 1
            p_extra = "; ".join(x for x in (p_extra, cp_extra) if x)
    if p_inv: stats["phone_invalid"] += 1

    gender_be = clean_text(r["เพศ"])
    gender = normalize_gender(gender_be) if gender_be != "ไม่ระบุ" else "ไม่ระบุ"
    if gender == "ไม่ระบุ" and c is not None:
        g2 = normalize_gender(c["เพศ"])
        if g2 != "ไม่ระบุ":
            gender, stats["gender_from_csv"] = g2, stats["gender_from_csv"] + 1

    email = normalize_email(r["Email ที่ติดต่อได้"])
    if not email and c is not None:
        email = normalize_email(c["อีเมล"])
        if email: stats["email_from_csv"] += 1

    # province: field > postcode > address text
    prov = clean_text(r["ที่อยู่ติดต่อได้ จังหวัด"])
    if not prov and c is not None:
        prov = clean_text(c["จังหวัด"])
    if prov:
        stats["prov_from_field"] += 1
    else:
        pc = re.sub(r"\D", "", clean_text(r["ที่อยู่ติดต่อได้ รหัสไปรษณีย์"]))[:5]
        if len(pc) == 5 and pc[:2] in POSTCODE_PROVINCE:
            prov = POSTCODE_PROVINCE[pc[:2]]
            stats["prov_from_postcode"] += 1
        else:
            addr_all = " ".join([clean_text(r["ที่อยู่ติดต่อได้ เลขที่ ซอย/ถนน"]),
                                 clean_text(c["ที่อยู่"]) if c is not None else ""])
            for pn in prov_names:
                if pn in addr_all:
                    prov = "กรุงเทพมหานคร" if pn == "กรุงเทพ" else pn
                    stats["prov_from_address"] += 1
                    break
    # normalize Bangkok variants
    if prov in ("กรุงเทพ", "กรุงเทพฯ", "กทม.", "กทม"): prov = "กรุงเทพมหานคร"

    rows.append({
        "รหัสนักศึกษา": sid,
        "รุ่นเกียร์": gear,
        "คำนำหน้า": clean_text(r["คำนำหน้า"]) or (clean_text(c["คำนำหน้า"]) if c is not None else ""),
        "ชื่อ": clean_text(r["ชื่อ"]),
        "นามสกุล": clean_text(r["นามสกุล"]),
        "ชื่อเล่น": clean_text(r["ชื่อเล่น"]),
        "First Name (EN)": clean_text(c["First Name"]) if c is not None else "",
        "Last Name (EN)": clean_text(c["Last Name"]) if c is not None else "",
        "เพศ": gender,
        "วันเกิด": clean_text(c["วันเกิด"]) if c is not None else "",
        "ภาควิชา": dept,
        "เบอร์โทรศัพท์": p1,
        "เบอร์โทรเพิ่มเติม": p_extra,
        "เบอร์โทรใช้ไม่ได้ (ดิบ)": p_inv,
        "อีเมล": email,
        "ที่อยู่ เลขที่/ซอย/ถนน": clean_text(r["ที่อยู่ติดต่อได้ เลขที่ ซอย/ถนน"]) or (clean_text(c["ที่อยู่"]) if c is not None else ""),
        "ตำบล/แขวง": clean_text(r["ที่อยู่ติดต่อได้ ตําบล/แขวง"]),
        "อำเภอ/เขต": clean_text(r["ที่อยู่ติดต่อได้ อําเภอ/เขต"]),
        "จังหวัด": prov,
        "รหัสไปรษณีย์": re.sub(r"\D", "", clean_text(r["ที่อยู่ติดต่อได้ รหัสไปรษณีย์"]))[:5],
        "กลุ่มอาชีพ": clean_text(r["กลุ่มอาชีพ"]) or (clean_text(c["อาชีพ"]) if c is not None else ""),
        "องค์กร/สังกัด": clean_text(r["องค์กร/สังกัด"]),
        "ตำแหน่ง": clean_text(r["ตำแหน่ง"]),
        "ชื่อบริษัท/ที่ทำงาน": clean_text(r["ชื่อบริษัท/ที่ทำงาน"]),
        "ที่อยู่บริษัท/ที่ทำงาน": clean_text(r["ที่อยู่บริษัท/ที่ทำงาน"]),
        "ประเภทธุรกิจ": clean_text(r["ประเภทธุรกิจ"]) or (clean_text(c["ประเภทธุรกิจ"]) if c is not None else ""),
        "รายละเอียดธุรกิจ": clean_text(r["รายละเอียดธุรกิจ"]),
        "สังกัดกระทรวง": clean_text(r["สังกัดกระทรวง"]),
        "หน่วยงาน": clean_text(r["หน่วยงาน"]),
        "สถานะใบ กว.": clean_text(r["สถานะใบ กว."]),
        "วันที่สมัครสมาชิก": clean_text(r["วันที่สมัครสมาชิก"]) or (clean_text(c["วันที่สมัคร"]) if c is not None else ""),
        "สถานะเว็บไซต์": clean_text(r["สถานะการเข้าใช้งานเว็บไซต์"]),
        "สถานะสมาชิก (Active/Inactive)": clean_text(c["สถานะสมาชิก"]) if c is not None else "",
        "รหัสสมาชิกเดิม (CSV)": clean_text(c["รหัสสมาชิก"]) if c is not None else "",
    })

master = pd.DataFrame(rows)

# ---------- dedupe ----------
before = len(master)
master = master.drop_duplicates(subset="รหัสนักศึกษา", keep="first")
stats["dedupe_by_sid"] = before - len(master)

# merge same-person groups: identical ชื่อ+นามสกุล+เกียร์ (mostly re-registrations
# with a mistyped student id — confirmed by shared phone/email in many groups)
master["อีเมลเพิ่มเติม"] = ""
master["รหัสนักศึกษาซ้ำที่ถูกรวม"] = ""
is_dup = master.duplicated(subset=["ชื่อ", "นามสกุล", "รุ่นเกียร์"], keep=False) & (master["ชื่อ"] != "")
merged_log = []
keep_rows, drop_idx = [], set()
for key, g in master[is_dup].groupby(["ชื่อ", "นามสกุล", "รุ่นเกียร์"]):
    scores = g.apply(lambda r: int((r != "").sum()), axis=1)
    surv_idx = scores.idxmax()
    surv = master.loc[surv_idx].copy()
    others = g.drop(index=surv_idx)
    for col in master.columns:
        if surv[col] == "":
            vals = [v for v in others[col] if v != ""]
            if vals:
                surv[col] = vals[0]
    extra_ph = sorted({p for p in others["เบอร์โทรศัพท์"] if p and p != surv["เบอร์โทรศัพท์"]})
    if extra_ph:
        surv["เบอร์โทรเพิ่มเติม"] = "; ".join(filter(None, [surv["เบอร์โทรเพิ่มเติม"]] + extra_ph))
    extra_em = sorted({e for e in others["อีเมล"] if e and e != surv["อีเมล"]})
    if extra_em:
        surv["อีเมลเพิ่มเติม"] = "; ".join(extra_em)
    surv["รหัสนักศึกษาซ้ำที่ถูกรวม"] = "; ".join(others["รหัสนักศึกษา"])
    master.loc[surv_idx] = surv
    drop_idx.update(others.index)
    for _, o in others.iterrows():
        merged_log.append({"เก็บไว้ (sid)": surv["รหัสนักศึกษา"], "ลบรวม (sid)": o["รหัสนักศึกษา"],
                           "ชื่อ": key[0], "นามสกุล": key[1], "เกียร์": key[2],
                           "เบอร์ที่ถูกรวม": o["เบอร์โทรศัพท์"], "อีเมลที่ถูกรวม": o["อีเมล"]})
master = master.drop(index=drop_idx)
merged_df = pd.DataFrame(merged_log)
stats["same_person_merged"] = len(merged_log)

# sort
master["_g"] = pd.to_numeric(master["รุ่นเกียร์"], errors="coerce")
master = master.sort_values(["_g", "รหัสนักศึกษา"]).drop(columns="_g")

# ---------- save ----------
master.to_csv(f"{DIR}/CMUEAA_Master_{DATE}.csv", index=False, encoding="utf-8-sig")
removed.drop(columns=["_gear_file"], errors="ignore").to_csv(
    f"{DIR}/CMUEAA_Removed_{DATE}.csv", index=False, encoding="utf-8-sig")

with pd.ExcelWriter(f"{DIR}/CMUEAA_Master_{DATE}.xlsx", engine="openpyxl") as xw:
    master.to_excel(xw, sheet_name="Master", index=False)
    removed.drop(columns=["_gear_file"], errors="ignore").to_excel(xw, sheet_name="Removed", index=False)
    merged_df.to_excel(xw, sheet_name="Merged_Duplicates", index=False)
    ws = xw.sheets["Master"]
    # force phone columns to text format so Excel keeps leading zeros
    for col_idx, col in enumerate(master.columns, 1):
        if "เบอร์โทร" in col or col == "รหัสไปรษณีย์":
            for cell in list(ws.iter_cols(min_col=col_idx, max_col=col_idx, min_row=2))[0]:
                cell.number_format = "@"

# ---------- summary ----------
stats["master_rows"] = len(master)
stats["removed_rows"] = len(removed)
stats["phone_primary"] = int((master["เบอร์โทรศัพท์"] != "").sum())
stats["email"] = int((master["อีเมล"] != "").sum())
stats["gender_known"] = int((master["เพศ"] != "ไม่ระบุ").sum())
stats["province"] = int((master["จังหวัด"] != "").sum())
stats["dept"] = int((master["ภาควิชา"] != "").sum())
stats["dob"] = int((master["วันเกิด"] != "").sum())
print(json.dumps(stats, ensure_ascii=False, indent=1))
