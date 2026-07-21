"""
从 NIST Webbook 批量导入物种的 Shomate 热力学参数

用法:
  python import_nist_shomate.py

数据来源: https://webbook.nist.gov/chemistry/
"""
import sys, os, re, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Tools'))

import requests
from bs4 import BeautifulSoup

# ── 冶金相关的物种列表 (名称, 化学式, CAS, 相态) ──
SPECIES_LIST = [
    # 气体
    ("O2", "O2", "7782-44-7", "g"),
    ("N2", "N2", "7727-37-9", "g"),
    ("H2", "H2", "1333-74-0", "g"),
    ("CO", "CO", "630-08-0", "g"),
    ("CO2", "CO2", "124-38-9", "g"),
    ("H2O", "H2O", "7732-18-5", "g"),
    ("CH4", "CH4", "74-82-8", "g"),
    ("SO2", "SO2", "7446-09-5", "g"),
    ("H2S", "H2S", "7783-06-4", "g"),
    ("Cl2", "Cl2", "7782-50-5", "g"),
    ("F2", "F2", "7782-41-4", "g"),
    ("Ar", "Ar", "7440-37-1", "g"),
    # 金属单质
    ("Fe(alpha)", "Fe", "7439-89-6", "s"),
    ("Fe(gamma)", "Fe", "7439-89-6", "s"),
    ("Fe(l)", "Fe", "7439-89-6", "l"),
    ("Al(s)", "Al", "7429-90-5", "s"),
    ("Al(l)", "Al", "7429-90-5", "l"),
    ("Cu(s)", "Cu", "7440-50-8", "s"),
    ("Cu(l)", "Cu", "7440-50-8", "l"),
    ("Ni(s)", "Ni", "7440-02-0", "s"),
    ("Ni(l)", "Ni", "7440-02-0", "l"),
    ("Cr(s)", "Cr", "7440-47-3", "s"),
    ("Cr(l)", "Cr", "7440-47-3", "l"),
    ("Mn(s,alpha)", "Mn", "7439-96-5", "s"),
    ("Mn(l)", "Mn", "7439-96-5", "l"),
    ("Si(s)", "Si", "7440-21-3", "s"),
    ("Si(l)", "Si", "7440-21-3", "l"),
    ("Ti(s,alpha)", "Ti", "7440-32-6", "s"),
    ("Ti(beta)", "Ti", "7440-32-6", "s"),
    ("Ti(l)", "Ti", "7440-32-6", "l"),
    ("V(s)", "V", "7440-62-2", "s"),
    ("V(l)", "V", "7440-62-2", "l"),
    ("Mg(s)", "Mg", "7439-95-4", "s"),
    ("Mg(l)", "Mg", "7439-95-4", "l"),
    ("Ca(s)", "Ca", "7440-70-2", "s"),
    ("Ca(l)", "Ca", "7440-70-2", "l"),
    ("Zn(s)", "Zn", "7440-66-6", "s"),
    ("Zn(l)", "Zn", "7440-66-6", "l"),
    ("Mo(s)", "Mo", "7439-98-7", "s"),
    ("Mo(l)", "Mo", "7439-98-7", "l"),
    ("Co(s)", "Co", "7440-48-4", "s"),
    ("Co(l)", "Co", "7440-48-4", "l"),
    ("Sn(s,white)", "Sn", "7440-31-5", "s"),
    ("Sn(l)", "Sn", "7440-31-5", "l"),
    ("Pb(s)", "Pb", "7439-92-1", "s"),
    ("Pb(l)", "Pb", "7439-92-1", "l"),
    ("W(s)", "W", "7440-33-7", "s"),
    ("Nb(s)", "Nb", "7440-03-1", "s"),
    # 氧化物
    ("FeO(s)", "FeO", "1345-25-1", "s"),
    ("Fe2O3(s)", "Fe2O3", "1309-37-1", "s"),
    ("Fe3O4(s)", "Fe3O4", "1317-61-9", "s"),
    ("Al2O3(s)", "Al2O3", "1344-28-1", "s"),
    ("SiO2(s,alpha)", "SiO2", "14808-60-7", "s"),
    ("SiO2(s,beta)", "SiO2", "14808-60-7", "s"),
    ("CaO(s)", "CaO", "1305-78-8", "s"),
    ("MgO(s)", "MgO", "1309-48-4", "s"),
    ("MnO(s)", "MnO", "1344-43-0", "s"),
    ("MnO2(s)", "MnO2", "1313-13-9", "s"),
    ("Cr2O3(s)", "Cr2O3", "1308-38-9", "s"),
    ("NiO(s)", "NiO", "1313-99-1", "s"),
    ("Cu2O(s)", "Cu2O", "1317-39-1", "s"),
    ("CuO(s)", "CuO", "1317-38-0", "s"),
    ("TiO2(s,rutile)", "TiO2", "1317-80-2", "s"),
    ("TiO2(s,anatase)", "TiO2", "1317-70-0", "s"),
    ("V2O5(s)", "V2O5", "1314-62-1", "s"),
    ("ZnO(s)", "ZnO", "1314-13-2", "s"),
    ("PbO(s,yellow)", "PbO", "1317-36-8", "s"),
    ("MoO3(s)", "MoO3", "1313-27-5", "s"),
    ("WO3(s)", "WO3", "1314-35-8", "s"),
    ("Na2O(s)", "Na2O", "1313-59-3", "s"),
    ("K2O(s)", "K2O", "12136-45-7", "s"),
    # 碳化物/氮化物
    ("CaCO3(s)", "CaCO3", "471-34-1", "s"),
    ("Fe3C(s)", "Fe3C", "12011-67-5", "s"),
    ("SiC(s)", "SiC", "409-21-2", "s"),
    ("TiN(s)", "TiN", "25583-20-4", "s"),
    ("AlN(s)", "AlN", "24304-00-5", "s"),
    ("Si3N4(s)", "Si3N4", "12033-89-5", "s"),
    # 氟化物/氯化物
    ("CaF2(s)", "CaF2", "7789-75-5", "s"),
    ("NaCl(s)", "NaCl", "7647-14-5", "s"),
    ("MgCl2(s)", "MgCl2", "7786-30-3", "s"),
    # 硫化物
    ("FeS(s)", "FeS", "1317-37-9", "s"),
    ("FeS2(s)", "FeS2", "12068-85-8", "s"),
    ("CaS(s)", "CaS", "20548-54-3", "s"),
    # 炉渣相关
    ("CaSiO3(s)", "CaSiO3", "10101-39-0", "s"),
    ("Fe2SiO4(s)", "Fe2SiO4", "10178-37-3", "s"),
    ("Mg2SiO4(s)", "Mg2SiO4", "10034-94-3", "s"),
    ("CaAl2O4(s)", "CaAl2O4", "12042-68-1", "s"),
    # 碳
    ("C(s,graphite)", "C", "7440-44-0", "s"),
    ("C(s,diamond)", "C", "7782-40-3", "s"),
]


def parse_shomate_table(soup):
    """从 NIST Webbook 页面解析 Shomate 系数"""
    tables = soup.find_all('table')
    results = []

    for tbl in tables:
        rows = tbl.find_all('tr')
        if len(rows) < 3:
            continue
        first_row = [c.get_text(strip=True) for c in rows[0].find_all(['td', 'th'])]
        if not any('Temperature' in c for c in first_row):
            continue

        # 检查是否包含 Shomate 系数 (A, B, C, D, E, F, G, H 行)
        row_labels = set()
        for r in rows[1:]:
            cells = r.find_all(['td', 'th'])
            if cells:
                label = cells[0].get_text(strip=True)
                row_labels.add(label)

        required = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'}
        if not required.issubset(row_labels):
            continue

        # 解析温度范围
        temp_ranges = []
        for cell in rows[0].find_all(['td', 'th'])[1:]:
            val = cell.get_text(strip=True)
            if 'to' in val:
                parts = val.replace(',', '').split('to')
                try:
                    t_min = float(parts[0].strip())
                    t_max = float(parts[1].strip().rstrip('.'))
                    temp_ranges.append((t_min, t_max))
                except:
                    temp_ranges.append(None)
            else:
                temp_ranges.append(None)

        # 解析每行系数
        coeffs = {}
        for r in rows[1:]:
            cells = r.find_all(['td', 'th'])
            if not cells:
                continue
            label = cells[0].get_text(strip=True)
            if label in required:
                values = []
                for cell in cells[1:]:
                    val = cell.get_text(strip=True).replace('×10', 'e').replace('−', '-')
                    val = val.replace(' ', '').replace(',', '')
                    try:
                        values.append(float(val))
                    except:
                        values.append(0.0)
                coeffs[label] = values

        if len(coeffs) == 8:
            n_cols = len(coeffs['A'])
            for i in range(n_cols):
                if i < len(temp_ranges) and temp_ranges[i]:
                    entry = {
                        'T_min': temp_ranges[i][0],
                        'T_max': temp_ranges[i][1],
                    }
                    for label in required:
                        if i < len(coeffs[label]):
                            entry[label] = coeffs[label][i]
                        else:
                            entry[label] = 0.0
                    results.append(entry)

    return results


def fetch_species(name, formula, cas, phase):
    """获取单个物种的 NIST 数据"""
    # 去除 CAS 中的横线
    cas_clean = cas.replace('-', '')
    url = f"https://webbook.nist.gov/cgi/cbook.cgi?ID=C{cas_clean}&Units=SI&cTG=on&cTC=on"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'lxml')
        coeffs = parse_shomate_table(soup)

        if not coeffs:
            return None

        # 只取第一个相态的温度区间（最常见的那个）
        # 排除明显非主相的数据（如 H 值异常）
        main = coeffs[0]
        if abs(main.get('H', 0)) > 50000:  # 明显异常
            if len(coeffs) > 1:
                main = coeffs[1]

        species_name = f"{formula}({phase})" if phase else formula
        if name and name != formula:
            species_name = f"{formula}({phase})"

        return {
            'name': species_name,
            'T_min': main['T_min'],
            'T_max': main['T_max'],
            'A': main['A'], 'B': main['B'], 'C': main['C'],
            'D': main['D'], 'E': main['E'],
            'F': main['F'], 'G': main['G'], 'H': main['H'],
        }
    except Exception as e:
        return None


def main():
    print(f"共 {len(SPECIES_LIST)} 个物种\n")

    success = 0
    failed = 0
    imported = []

    for i, (name, formula, cas, phase) in enumerate(SPECIES_LIST):
        sys.stdout.write(f"\r[{i+1}/{len(SPECIES_LIST)}] {formula}({phase})... ")
        sys.stdout.flush()

        result = fetch_species(name, formula, cas, phase)
        if result:
            success += 1
            imported.append(result)
            print(f"✅ {result['name']} [{result['T_min']}-{result['T_max']}K]")
        else:
            failed += 1
            print(f"❌")

        time.sleep(0.3)  # 礼貌延迟

    print(f"\n\n成功: {success}, 失败: {failed}")

    # 输出 Python 代码
    if imported:
        print(f"\n=== 生成的 SHOMATE_PARAMS 代码 ({len(imported)} 个) ===\n")
        print('    # ===== NIST 批量导入 =====')
        for s in imported:
            print(f'    "{s["name"]}": {{"T_min": {s["T_min"]:.0f}, "T_max": {s["T_max"]:.0f},')
            print(f'        "A": {s["A"]:.6f}, "B": {s["B"]:.6f}, "C": {s["C"]:.6f},')
            print(f'        "D": {s["D"]:.6f}, "E": {s["E"]:.6f}, "F": {s["F"]:.6f},')
            print(f'        "G": {s["G"]:.6f}, "H": {s["H"]:.6f}}},')


if __name__ == '__main__':
    main()
