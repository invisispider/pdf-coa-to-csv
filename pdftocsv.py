import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import pdfplumber
import re

print("Supported Labs: VIRIDIS, CAMBIUM")

def convertPdfToText():
    prj_dir = os.getcwd()
    if 'coa_pdftocsv' not in prj_dir:
        exit('Please rename the project directory "coa_pdftocsv" or edit the configuration')

    check = os.listdir(prj_dir)
    if 'output' not in check:
        exit('Please create output folder (for csv dataframe) and set permissions.')
    elif 'input' not in check:
        exit('Please create input folder (for pdf coas) and set permissions.')
    elif 'myenv' not in check:
        print('Being a little weird with the virtual environment, okay...')
    print('Project configuration check succeeded.')

    directory = os.listdir(os.path.join(prj_dir,'input'))

    pdf_files = [f for f in directory if f.endswith(r'.pdf')]

    print(str(len(pdf_files))+' PDF files found.')

    for pdf_idx in range(len(pdf_files)):
        with pdfplumber.open(os.path.join('input',pdf_files[pdf_idx])) as pdf:
            page_text = ''
            for pdf_page_idx in range(len(pdf.pages)):
                jth_page = pdf.pages[pdf_page_idx]
                page_text += jth_page.extract_text()
                pdf_page_idx += 1
            if pdf_files[pdf_idx].startswith('CAM-'):
                pred_string = 'cam_temp_file'
            elif pdf_files[pdf_idx].startswith('LN-') or pdf_files[pdf_idx].startswith('BC-'):
                pred_string = 'vir_temp_file'
            elif pdf_files[pdf_idx].endswith('.pdf'):
                pred_string = 'generic_temp_file'
            with open(pred_string+str(pdf_idx)+'.txt', 'w') as temp_txt_file:
                temp_txt_file.write(page_text)
        pdf_idx += 1
        if pdf_idx==1:
            print(str(pdf_idx)+' file converted.')
        else:
            print(str(pdf_idx)+' files converted.')

convertPdfToText()
print('All files converted to text.')

def cambium_date(c_date):
    month_dict = {
        'JAN': '01',
        'FEB': '02',
        'MAR': '03',
        'APR': '04',
        'MAY': '05',
        'JUN': '06',
        'JUL': '07',
        'AUG': '08',
        'SEP': '09',
        'OCT': '10',
        'NOV': '11',
        'DEC': '12'
    }
    if c_date[0:3] in month_dict:
        month = month_dict[c_date[0:3]]
        day = c_date[4:6].strip()
        return month+'/'+day+'/'
    else:
        print('error: month not found. Check abbreviation.')
        quit()

def get_strain(field):
    with open('strains.txt', 'r', encoding='utf-8') as strains:
        for strain in strains:
            field = field.lower()
            if strain.lower().strip() in field:
                return strain



def percent_handler(string):
    string = string.replace(' ', '')
    index = string.find('%')
    donoin_string = string[0:(index+1)]
    return donoin_string

def v_percent_handler(line, string):
    line = line.split(string)[1].replace(string, '')
    index = line.find('%')
    donoin_string = line[0:(index+1)]
    return donoin_string

def extract_metals(line, string):
    line = line.replace(string, '').strip()
    if line.startswith('ND'):
        return 0.0
    elif line.startswith('<LOQ'):
        return 0.0
    else:
        micro_elements = line.split('µg/g')
        micro_el = micro_elements[0].split('/')
        return micro_el[0].replace(' ', '').strip()

def terps_starts(line, string):
    line = line.replace(string, '')
    if '%' in line:
        return percent_handler(line)
    elif line.strip().startswith('ND'):
        return '0.0%'
    else:
        return line.strip().split(' ')[0]+'%'

def terps_contains(line, string):
    line = line.split(string)[1].replace(string, '')
    if '%' in line:
        return percent_handler(line)
    elif line.strip().startswith('ND'):
        return '0.0%'
    else:
        return line.strip().split(' ')[0]+'%'

def v_mic_handler(line, string):
    split_list = line.replace(string, '').split(' ')
    if split_list[1].strip() == 'Not':
        return '0'
    elif split_list[1].strip() != 'PASS':
        return split_list[1].strip()
    elif split_list[2].strip() == 'Not':
        return '0'
    elif split_list[2].strip() != 'PASS':
        return split_list[2].strip()
    elif split_list[3].strip() == 'Not':
        return '0'
    elif split_list[3].strip() != 'PASS':
        quit("It should never get to here.")

def get_data_cambium(coa):
    r = dict()
    batch_id = False
    deltas = []
    r['Lab Name'] = 'Cambium Analytica'
    line_idx = 0
    for line in coa:
        line_idx+=1
        # HEAD ITEMS
        string = 'SAMPLE ID: '
        if string in line:
            r['Sample ID'] = line.replace(string, '').replace(' ','').strip()
            print("Reading COA: "+r['Sample ID'])
        string = 'SAMPLE: '
        if string in line:
            p_f = line[-6:].strip()
            if p_f.endswith('SS'):
                r['Pass/fail?'] = 'Passed'
            else:
                r['Pass/fail?'] = 'Failed'
            s_name = line.replace(string, '').strip().title()
            s_name = s_name.split('/')
            r['Sample Name'] = s_name[0]
            strain = get_strain(line)
            r['Strain'] = strain
        string = 'COLLECTED ON: '
        if string in line:
            line = line.replace(string, '').strip()
            month_day = cambium_date(line)
            year = line[-5:].replace(' ', '').strip()
            r['Date Completed'] = month_day + year
        string = 'RECEIVED ON: '
        if string in line:
            line = line.replace(string, '').strip()
            month_day = cambium_date(line)
            year = line[-5:].replace(' ', '').strip()
            r['Date Received'] = month_day + year
        string = 'MATRIX: '
        if string in line:
            cambium_type = line.replace(string, '').strip()
            if cambium_type == 'FLOWER':
                r['Category'] = 'Plant'
                r['Type'] = 'Flower - Cured'
            elif cambium_type in ('Kief(Plant)', 'Kief(Concentrate)', 'Kief'):
                r['Category'] = 'Plant'
                r['Type'] = 'Kief'
            elif cambium_type == 'Cannabis Plant Material':
                r['Category'] = 'Plant'
                r['Type'] = 'Trim'
            elif cambium_type == 'Vape Cartridge':
                r['Category'] = 'Extracts'
                r['Type'] = 'Vape Cart'
            elif cambium_type == 'Other Matrix':
                r['Category'] = 'Other'
                r['Type'] = 'NA'
            else:
                r['Category'] = 'Extracts'
                r['Type'] = 'Other'

        string = 'SRC PKG: '
        if string in line:
            r['Regulator Batch ID'] = line.replace(string, '').replace(" ","").strip()
        string = 'TEST PKG: '
        if string in line:
            r['Regulator ID'] = line.replace(string, '').replace(" ","").replace("CANNABINOIDOVERVIEW","").strip()


        string = 'BATCH NO.:'
        if string in line:
            r['Regulator Batch ID'] = line.replace(string, '').replace(' ','').replace('CANNABINOIDOVERVIEW','').strip()
        string = 'METRC TAG: '
        if string in line:
            r['Regulator ID'] = line.replace(string, '').replace(' ','').replace('CANNABINOIDOVERVIEW','').strip()

        # CANNABINOIDS
        string = 'THCA'
        if line.startswith(string):
            line = line.replace(string, '').replace(':','')
            if line.startswith('ND'):
                r['cannabinoids_thca'] = '0.00%'
            else:
                r['cannabinoids_thca'] = percent_handler(line)

        string = 'CBDA'
        if line.startswith(string):
            line = line.replace(string, '').strip()
            if 'ND' in line:
                r['cannabinoids_cbda'] = '0.00%'
            else:
                r['cannabinoids_cbda'] = percent_handler(line)
        elif line.startswith('CBD') and not line.startswith('CBDA'):
            line = line.replace(string, '')
            if 'ND' in line:
                r['cannabinoids_cbd'] = '0.00%'
            else:
                r['cannabinoids_cbd'] = percent_handler(line)

        string = 'CBGA'
        if line.startswith(string):
            line = line.replace(string, '')
            if line.startswith('ND'):
                r['cannabinoids_cbga'] = '0.00%'
            else:
                r['cannabinoids_cbga'] = percent_handler(line)
        elif line.startswith('CBG') and not line.startswith('CBGA'):
            line = line.replace('CBG', '')
            if 'ND' in line:
                r['cannabinoids_cbg'] = '0.00%'
            else:
                r['cannabinoids_cbg'] = percent_handler(line)

        string = 'CBC'
        if line.startswith(string):
            line = line.replace(string, '').strip()
            if line.startswith('ND'):
                r['cannabinoids_cbc'] = '0.00%'
            else:
                r['cannabinoids_cbc'] = percent_handler(line)

        string = 'CBDV'
        if line.startswith(string):
            line = line.replace(string, '')
            if 'ND' in line:
                r['cannabinoids_cbdv'] = '0.00%'
            else:
                r['cannabinoids_cbdv'] = percent_handler(line)


        string = 'CBN'
        if line.startswith(string):
            line = line.replace(string, '')
            if line.startswith('ND'):
                r['cannabinoids_cbn'] = '0.00%'
            else:
                r['cannabinoids_cbn'] = percent_handler(line)

        string = 'THCV'
        if line.startswith(string):
            line = line.replace(string, '')
            if line.startswith('ND'):
                r['cannabinoids_thcv'] = '0.00%'
            else:
                r['cannabinoids_thcv'] = percent_handler(line)

        string = 'Δ9-THC:'
        if line.startswith(string):
            line=line.replace(string,'')
            r['cannabinoids_d9_thc'] = line if 'ND' not in line else '0.00%'

        string = 'Δ8-THC:'
        if line.startswith(string):
            line=line.replace(string,'')
            r['cannabinoids_d8_thc'] = line if 'ND' not in line else '0.00%'


        # TERPENES
        string = 'TRANS-NEROLIDOL '
        if line.startswith(string):
            r['terpenes_cis_nerolidol'] = terps_starts(line, string)
        string = 'CAMPHOR '
        if string in line:
            r['terpenes_camphene'] = terps_contains(line, string)
        string = 'FENCHYL ALCOHOL '
        if string in line:
            r['terpenes_fenchol'] = terps_contains(line, string)
        string = 'GUAIOL '
        if string in line:
            r['terpenes_guaiol'] = terps_contains(line, string)
        string = 'α-TERPINENE '
        if string in line:
            r['terpenes_alpha_terpinene'] = terps_contains(line, string)
        string = 'α-BISABOLOL '
        if line.startswith(string):
            r['terpenes_alpha_bisabolol'] = terps_starts(line, string)
        string = 'FENCHONE '
        if string in line:
            r['terpenes_fenchone'] = terps_contains(line, string)
        string = '(-)-ISOPULEGOL '
        if line.startswith(string):
            r['terpenes_isopulegol'] = terps_starts(line, string)
        string = 'ISOBORNEOL '
        if line.startswith(string):
            r['terpenes_isoborneol'] = terps_starts(line, string)
        string = 'Δ3-CARENE '
        if string in line:
            r['terpenes_3_carene'] = terps_contains(line, string)
        string = 'α-PINENE '
        if line.startswith(string):
            r['terpenes_alpha_pinene'] = terps_starts(line, string)
        string = 'GERANYL ACETATE '
        if string in line:
            r['terpenes_geranyl_acetate'] = terps_contains(line, string)
        string = 'CARYOPHYLLENE OXIDE '
        if string in line:
            r['terpenes_caryophyllene_oxide'] = terps_contains(line, string)
        string = 'TRANS-CARYOPHYLLENE '
        if line.startswith(string):
            r['terpenes_beta_caryophyllene'] = terps_starts(line, string)
        string = 'LIMONENE '
        if line.startswith(string):
            r['terpenes_delta_limonene'] = terps_starts(line, string)
        string = 'γ-TERPINENE '
        if string in line:
            r['terpenes_gamma_terpinene'] = terps_contains(line, string)
        string = 'EUCALYPTOL '
        if line.startswith(string):
            r['terpenes_eucalyptol'] = terps_starts(line, string)
        string = 'GERANIOL '
        if line.startswith(string):
            r['terpenes_geraniol'] = terps_starts(line, string)
        string = 'α-HUMULENE '
        if line.startswith(string):
            r['terpenes_alpha_humulene'] = terps_starts(line, string)
        string = 'LINALOOL * '
        if line.startswith(string):
            r['terpenes_linalool'] = terps_starts(line, string)
        string = 'ISOPULEGOL '
        if string in line:
            r['terpenes_isopulegol'] = terps_contains(line, string)
        string = 'CIS-NEROLIDOL '
        if line.startswith(string):
            r['terpenes_trans_nerolidol'] = terps_starts(line, string)
        string = 'CIS-β-OCIMENE '
        if string in line:
            r['terpenes_ocimene'] = terps_contains(line, string)
        string = 'TRANS-β-OCIMENE '
        if line.startswith(string):
            r['terpenes_beta_ocimene'] = terps_starts(line, string)
        string = 'α-PHELLANDRENE '
        if string in line:
            r['terpenes_alpha_phellandrene'] = terps_contains(line, string)
        string = '-CYMENE '
        if string in line:
            r['terpenes_ro_cymene'] = terps_contains(line, string)
        string = 'β-MYRCENE '
        if line.startswith(string):
            r['terpenes_beta_myrcene'] = terps_starts(line, string)
        string = 'β-PINENE '
        if line.startswith(string):
            r['terpenes_beta_pinene'] = terps_starts(line, string)
        string = 'TERPINOLENE '
        if line.startswith(string):
            r['terpenes_terpinolene'] = terps_starts(line, string)

 
        # # MICROBIALS AND HEAVY METALS
        string = 'WATER ACTIVITY 0.65Aw '
        if line.startswith(string):
            line = line.replace(string, '').replace('PASS','').replace('FAIL','').replace('Aw','').strip()
            r['water_activity_water_activity'] = line.replace(' ','')
            continue

        if line.startswith('COLI'):
            line = coa[line_idx-2]
            if 'ND' in line or 'ANALYTE LIMIT AMT (' in line:
                r['microbials_ecoli'] = 0.0
            else:
                micro_elements = line.split('CFU/g')
                r['microbials_ecoli'] = micro_elements[0].strip()
            continue

        string = 'SALMONELLA SPP.'
        if line.startswith(string):
            line = line.replace(string, '').replace('Any amount in 1 gram ','').strip()
            if 'ND' in line:
                r['microbials_salmonella'] = 0.0
            else:
                micro_elements = line.split('CFU/g')
                r['microbials_salmonella'] = micro_elements[0].strip()
            continue

        string = 'ASPERGILLUS SPP.'
        if line.startswith(string):
            line = line.replace(string, '').replace('Any amount in 1 gram','').strip()
            if 'ND' in line:
                r['microbials_aspergillus'] = 0.0
            else:
                micro_elements = line.split('CFU/g')
                r['microbials_aspergillus'] = micro_elements[0].strip()
            continue

        string = 'YEAST & MOLD 1000 CFU/g '
        if line.startswith(string):
            line = line.replace(string, '').strip()
            if line.startswith('ND'):
                r['microbials_yeast_and_mold'] = 0.0
            else:
                micro_elements = line.split('CFU/g')
                r['microbials_yeast_and_mold'] = micro_elements[0].replace(' ','').strip()
        string = 'YEAST & MOLD 100000 CFU/g '
        if line.startswith(string):
            line = line.replace(string, '').strip()
            if line.startswith('ND'):
                r['microbials_yeast_and_mold'] = 0.0
            else:
                micro_elements = line.split('CFU/g')
                r['microbials_yeast_and_mold'] = micro_elements[0].replace(' ','').strip()

        string = 'COLIFORMS 100 CFU/g '
        if line.startswith(string):
            line = line.replace(string, '').strip()
            if line.startswith('ND'):
                r['microbials_coliforms'] = 0.0
            else:
                micro_elements = line.split('CFU/g')
                r['microbials_coliforms'] = micro_elements[0].replace(' ','').strip()
                continue
        string = 'COLIFORMS 1000 CFU/g '
        if line.startswith(string):
            line = line.replace(string, '').strip()
            if line.startswith('ND'):
                r['microbials_coliforms'] = 0.0
            else:
                micro_elements = line.split('CFU/g')
                r['microbials_coliforms'] = micro_elements[0].replace(' ','').strip()
                continue

        string = 'ARSENIC 0.2 µg/g '
        if line.startswith(string):
            r['metals_arsenic'] = extract_metals(line, string)
            continue
        string = 'ARSENIC 0.4 µg/g '
        if line.startswith(string):
            r['metals_arsenic'] = extract_metals(line, string)
            continue

        string = 'CADMIUM 0.2 µg/g '
        if line.startswith(string) and '<LOQ' not in line and 'ND' not in line:
            r['metals_cadmium'] = str(extract_metals(line, string)).replace('0.0256','0').replace('<LOQ','')
            continue
        string = 'CADMIUM 0.4 µg/g '
        if line.startswith(string) and '<LOQ' not in line and 'ND' not in line:
            r['metals_cadmium'] = str(extract_metals(line, string)).replace('0.0256','0').replace('<LOQ','')
            continue

        string = 'MERCURY 0.1 µg/g '
        if line.startswith(string):
            r['metals_mercury'] = extract_metals(line, string)
            continue
        string = 'MERCURY 0.2 µg/g '
        if line.startswith(string):
            r['metals_mercury'] = extract_metals(line, string)
            continue

        string = 'LEAD 0.5 µg/g '
        if line.startswith(string):
            r['metals_lead'] = extract_metals(line, string)
            continue
        string = 'LEAD 1 µg/g '
        if line.startswith(string):
            r['metals_lead'] = extract_metals(line, string)
            continue

        string = 'CHROMIUM 0.6 µg/g '
        if line.startswith(string):
            r['metals_chromium'] = str(extract_metals(line, string)).replace('0.027','0')
            continue
        string = 'CHROMIUM 1.2 µg/g '
        if line.startswith(string):
            r['metals_chromium'] = str(extract_metals(line, string)).replace('0.027','0')
            continue

        string = 'NICKEL 0.5 µg/g '
        if line.startswith(string):
            r['metals_nickel'] = extract_metals(line, string)
            continue
        string = 'NICKEL 1 µg/g '
        if line.startswith(string):
            r['metals_nickel'] = extract_metals(line, string)
            continue

        string = 'COPPER '
        if line.startswith(string):
            string2 = 'COPPER 3 µg/g '
            if line.startswith(string2):
                r['metals_copper'] = str(extract_metals(line, string2)).replace('0.045','')
                continue
            else:
                r['metals_copper'] = str(extract_metals(line, string)).replace('0.045','')
                continue


        # TOTAL CANNABINOIDS AND TERPS
        if line.startswith('TOTAL TERPENES * ') and not line.startswith('TOTAL TERPENES = '):
            r['terpenes_total'] = percent_handler(line.replace('TOTAL TERPENES * ',''))
        # print(line)
        # print(percent_handler(line.replace('Total Terpenes ','')))


        if line.startswith('TOTAL CANNABINOIDS: '):
            r['cannabinoids_total'] = percent_handler(line.replace('TOTAL CANNABINOIDS: ', ''))

    return r



##############################################################

def get_data_viridis(coa):
    r = dict()
    r['Lab Name'] = 'Viridis Labs'
    for line in coa:
        # HEAD ITEMS
        string = 'Sample No.: '
        if string in line:
            r['Sample ID'] = line.split(string)[1].replace(string, '').strip()
            # r['Sample ID'] = line.replace(string, '').strip()
        string = 'Customer Unique ID: '
        if string in line:
            r['Sample Name'] = line.replace(string, '').strip()
            strain = get_strain(line)
            r['Strain'] = strain
        string = 'Date Sample Collected/Received: '
        if string in line:
            r['Date Received'] = line.replace(string, '').strip()
        string = 'Report Date:'
        if string in line:
            r['Date Completed'] = line.split(string)[1].replace(string, '').strip()
        string = 'Date Testing Completed: '
        if string in line:
            r['Date Completed'] = line.split(string)[1].replace(string, '').strip()
        string = 'Sample Matrix: '
        if string in line:
            viridis_type = line.replace(string, '').strip()
            if viridis_type == 'Bud/ Flower':
                r['Category'] = 'Plant'
                r['Type'] = 'Flower - Cured'
            elif viridis_type in ('Kief(Plant)', 'Kief(Concentrate)', 'Kief'):
                r['Category'] = 'Plant'
                r['Type'] = 'Kief'
            elif viridis_type == 'Cannabis Plant Material':
                r['Category'] = 'Plant'
                r['Type'] = 'Trim'
            elif viridis_type == 'Vape Cartridge':
                r['Category'] = 'Extracts'
                r['Type'] = 'Vape Cart'
            elif viridis_type == 'Other Matrix':
                r['Category'] = 'Other'
                r['Type'] = 'NA'
            else:
                r['Category'] = 'Extracts'
                r['Type'] = 'Other'

        string = 'Overall Result: '
        if string in line:
            string2 = 'PASS'
            if string2 in line:
                r['Pass/fail?'] = 'Passed'
            else:
                r['Pass/fail?'] = 'Failed'
        string = 'Source METRC ID: '
        if string in line:
            r['Regulator Batch ID'] = line.split(string)[1].replace(string, '')[0:24].strip()
        string1 = 'Sample METRC ID: '
        string2 = 'METRC ID: '
        if string1 in line:
            r['Regulator ID'] = line.replace(string1, '').strip()
        elif string2 in line and not string1 in line and not string in line:
            r['Regulator ID'] = line.split(string2)[1].replace(string2, '').strip()

        # CANNABINOIDS
        string = 'Tetrahydrocannabinolic Acid (THCA) '
        if string in line:
            r['cannabinoids_thca'] = v_percent_handler(line, string)
        string = 'Cannabidiolic Acid (CBDA) '
        if string in line:
            r['cannabinoids_cbda'] = v_percent_handler(line, string)
        string = 'Cannabidiol (CBD) '
        if string in line:
            r['cannabinoids_cbd'] = v_percent_handler(line, string)
        string = 'Delta 9-Tetrahydrocannabinol (THC) '
        if string in line:
            r['cannabinoids_d9_thc'] = v_percent_handler(line, string)
        string = 'Cannabigerolic Acid (CBGA) '
        if line.startswith(string):
            r['cannabinoids_cbga'] = v_percent_handler(line, string)
        string = 'Cannabigerol (CBG) '
        if line.startswith(string):
            r['cannabinoids_cbg'] = v_percent_handler(line, string)
        string = 'Delta-8-Tetrahydrocannabinol (Delta 8- '
        if line.startswith(string):
            r['cannabinoids_d8_thc'] = v_percent_handler(line, string)
        string = 'Cannabichromene (CBC) '
        if line.startswith(string):
            r['cannabinoids_cbc'] = v_percent_handler(line, string)
        string = 'Cannabinol (CBN) '
        if line.startswith(string):
            r['cannabinoids_cbn'] = v_percent_handler(line, string)

        # TERPENES
        string = '(-)-Isopulegol '
        if line.startswith(string):
            r['terpenes_isopulegol'] = v_percent_handler(line, string)
        string = '3-Carene '
        if line.startswith(string):
            r['terpenes_3_carene'] = v_percent_handler(line, string)
        string = 'a-Pinene '
        if line.startswith(string):
            r['terpenes_alpha_pinene'] = v_percent_handler(line, string)
        string = 'Caryophyllene '
        if line.startswith(string):
            r['terpenes_beta_caryophyllene'] = v_percent_handler(line, string)
        string = 'D-Limonene '
        if line.startswith(string):
            r['terpenes_delta_limonene'] = v_percent_handler(line, string)
        string = 'Eucalyptol '
        if line.startswith(string):
            r['terpenes_eucalyptol'] = v_percent_handler(line, string)
        string = 'Geraniol '
        if line.startswith(string):
            r['terpenes_geraniol'] = v_percent_handler(line, string)
        string = 'Humulene '
        if line.startswith(string):
            r['terpenes_alpha_humulene'] = v_percent_handler(line, string)
        string = 'Linalool '
        if line.startswith(string):
            r['terpenes_linalool'] = v_percent_handler(line, string)
        string = 'cis-Ocimene '
        if line.startswith(string):
            r['terpenes_ocimene'] = v_percent_handler(line, string)
        string = 'Ocimene '
        if line.startswith(string):
            r['terpenes_beta_ocimene'] = v_percent_handler(line, string)
        string = 'p-Cymene '
        if line.startswith(string):
            r['terpenes_ro_cymene'] = v_percent_handler(line, string)
        string = 'ß-Myrcene '
        if line.startswith(string):
            r['terpenes_beta_myrcene'] = v_percent_handler(line, string)
        string = 'ß-Pinene '
        if line.startswith(string):
            r['terpenes_beta_pinene'] = v_percent_handler(line, string)
        string = 'Terpinolene '
        if line.startswith(string):
            r['terpenes_terpinolene'] = v_percent_handler(line, string)

        # MICROBIALS
        string = 'Total Yeast & Mold '
        if line.startswith(string):
            r['microbials_yeast_and_mold'] = v_mic_handler(line, string)
        string = 'Total Coliform Bacteria '
        if line.startswith(string):
            r['microbials_coliforms'] = v_mic_handler(line, string)
        string = 'Moisture Content TESTED '
        if line.startswith(string):
            r['moisture_percent_moisture'] = v_mic_handler(line, string)
        string = 'Water activity '
        if line.startswith(string):
            r['water_activity_water_activity'] = v_mic_handler(line, string)
        string = 'Aspergillus spp. '
        if line.startswith(string):
            r['microbials_aspergillus'] = v_mic_handler(line, string)
        string = 'Salmonella spp. '
        if line.startswith(string):
            r['microbials_salmonella'] = v_mic_handler(line, string)
        string = 'STEC E. Coli '
        if line.startswith(string):
            r['microbials_ecoli'] = v_mic_handler(line, string)


        # METALS
        if line.startswith('Arsenic'):
            split_list = line.replace(string, '')
            r['metals_arsenic'] = split_list.split(' ')[2]
        if line.startswith('Cadmium'):
            split_list = line.replace(string, '')
            r['metals_cadmium'] = split_list.split(' ')[2]
        if line.startswith('Mercury'):
            split_list = line.replace(string, '')
            r['metals_mercury'] = split_list.split(' ')[2]
        if line.startswith('Lead'):
            split_list = line.replace(string, '')
            r['metals_lead'] = split_list.split(' ')[2]
        if line.startswith('Chromium'):
            split_list = line.replace(string, '')
            r['metals_chromium'] = split_list.split(' ')[2]
        if line.startswith('Nickel'):
            split_list = line.replace(string, '')
            if len(split_list.split(' ')) > 2:
                r['metals_nickel'] = split_list.split(' ')[2]
        if line.startswith('Copper'):
            split_list = line.replace(string, '')
            r['metals_copper'] = split_list.split(' ')[2]

        # TOTAL CANNABINOIDS AND TERPS
        string = 'Total Terpenes '
        if line.startswith(string) and not line.startswith('Total Terpenes = '):
            r['terpenes_total'] = v_percent_handler(line, string)
        string = 'Total Cannabinoids '
        if line.startswith(string) and not line.startswith('Total Cannabinoids = '):
            r['cannabinoids_total'] = v_percent_handler(line, string)


    return r


##############################################################

with open('column_heads_list.txt', "r") as headers:
    csv_headers = headers.readline()

text_coas = []

rows = []
for file in os.listdir():
    if file.startswith('cam_temp_file'):
        with open(file, "r", encoding='utf-8') as f:
            text_coa = f.readlines()
            text_coa = [coa.rstrip() for coa in text_coa]
            rows.append(get_data_cambium(text_coa))
    elif file.startswith('vir_temp_file'):
        with open(file, 'r', encoding='utf-8') as f:
            text_coa = f.readlines()
            text_coa = [coa.rstrip() for coa in text_coa]
            rows.append(get_data_viridis(text_coa))

results_df = pd.DataFrame.from_dict(rows)

new_headers = csv_headers.split(',')
columnar_df = pd.DataFrame(columns=new_headers)
df = columnar_df.append(results_df)
df.to_csv(os.path.join('output','dataframe.csv'))

print('Removing temporary files.')
for f in listdir():
    if f.startswith('vir_temp_file') or f.startswith('generic_temp_file') or f.startswith('cam_temp_file'):
        os.remove(f)

exit(r'Output saved to local output/dataframe.csv')
