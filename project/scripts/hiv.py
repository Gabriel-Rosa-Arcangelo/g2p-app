import sys
import time
import datetime
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import shutil
from Bio import SeqIO
import re
import pandas as pd
import subprocess
import logging
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import urllib3
from urllib3.exceptions import NewConnectionError, MaxRetryError
from pathlib import Path

# Configuração do logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Base paths
BASE_DIR = Path(__file__).resolve().parents[2]
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", str(BASE_DIR / "media"))

# Folder where the files are uploaded
folder = sys.argv[1]

# Path of the files
arquivos = sys.argv[2:-1]

# Remove duplicates
arquivos = list(set(arquivos))

user_id = sys.argv[-1]

'''logging.info('Upload directory: %s', folder)
logging.info('Uploaded files:')
for arquivo_path in arquivos:
    logging.info(arquivo_path)'''
    
# External dependency: directory that contains pleres_sysgeno_recipiente.py
folder_tropismo = os.environ.get(
    "TROPISMO_DIR",
    "",
)
temp_file = 'temp_pleres.txt'
desired_samples = [os.path.basename(file).split('.')[0] for file in arquivos]

def retrieve_pleres_data(arquivo_path, desired_samples, folder_tropismo, temp_file="temp_pleres.txt"):
    base_name = os.path.splitext(os.path.basename(arquivo_path))[0]
    #logging.info('Preparando nome da amostra: %s', base_name)
    desired_samples = [re.sub(r'\..*$', '', re.sub(r'_.*', '', re.sub(r'.*/', '', sample))) for sample in desired_samples]
    desired_samples = [sample for sample in desired_samples if not re.search(r'CN|CP|BRANCO|barcodes|NA', sample)]
    desired_samples = ','.join(["'" + re.sub(r'^0*', '', sample) + "'" for sample in set(desired_samples)])
    
    #logging.info('Script Pleres')
    command = f'python3 {folder_tropismo}/pleres_sysgeno_recipiente.py "{desired_samples}" {folder_tropismo}/{temp_file}'
    subprocess.run(command, shell=True)
    
    #logging.info('Output data')
    data = pd.read_csv(f'{folder_tropismo}/{temp_file}', sep='\t', index_col=0)
    return data

def execute_with_retry():
    retries = 3  
    for _ in range(retries):
        try:
            driver.get("https://bioinf.mpi-inf.mpg.de/apex/f?p=2001:8")
            break
        except (NewConnectionError, MaxRetryError) as e:
            #logging.info("An error occurred: %s", e)
            #logging.info("Retrying...")

            time.sleep(3)
    '''else:
        logging.info("Failed to establish a connection after multiple retries. Exiting...")'''

def add_text_to_existing_pdf(new_pdf_path, text, x=20, y=90, font_size=9):
    # Criar um buffer para o novo PDF com texto usando reportlab
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica", font_size) 
    can.drawString(x, y, text)
    can.save()
    packet.seek(0)

    # Ler o PDF existente
    existing_pdf = PdfReader(new_pdf_path)
    output = PdfWriter()

    # Adicionar texto a cada página do PDF existente
    new_pdf = PdfReader(packet)
    for i in range(len(existing_pdf.pages)):
        page = existing_pdf.pages[i]
        # Criar uma nova página em branco com o texto
        overlay_page = new_pdf.pages[0]
        # Fundir a página original com a sobreposição de texto
        page.merge_page(overlay_page)
        output.add_page(page)

    # Salvar o novo PDF com o texto adicionado, sobrescrevendo o arquivo original
    with open(new_pdf_path, 'wb') as output_pdf_file:
        output.write(output_pdf_file)

    #logging.info("PDF com texto adicionado: %s", new_pdf_path)
    
def add_mutations_to_pdf(csv_output_path, new_pdf_path):
    # Ler o CSV e extrair mutações
    df = pd.read_csv(csv_output_path)
    mutation_columns = df.columns[6:]  # Colunas de mutações começam a partir da coluna 7
    mutations = df[mutation_columns].apply(lambda x: ','.join(x.dropna().astype(str)), axis=1).values[0]

    # Adicionar mutações ao PDF
    text = f"Mutações: {mutations}"
    add_text_to_existing_pdf(new_pdf_path, text)
    
# Path for PDFs
dir_pdf = os.path.join(MEDIA_ROOT, "pdfs")

user_dir = os.path.join(dir_pdf, str(user_id))  

os.makedirs(user_dir, exist_ok=True)

# Configure Firefox profile to direct downloads to dir_pdf
profile = webdriver.FirefoxProfile()
profile.set_preference("browser.download.dir", dir_pdf)
profile.set_preference("browser.download.folderList", 2)
profile.set_preference("browser.download.manager.showWhenStarting", False)
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")

gecko_path = os.environ.get("GECKODRIVER_PATH", "geckodriver")

# Configure Firefox options with the profile
options = Options()
options.profile = profile
options.add_argument("--headless") 

service = Service(executable_path=gecko_path)

# Start Firefox driver with the configured options
driver = webdriver.Firefox(service=service, options=options)

url = "https://coreceptor.geno2pheno.org/"
name_xpath = '//*[@id="g2pmain"]/div/center/table/tbody/tr[1]/td/input'
fpr_xpath = '//*[@id="g2pmain"]/div/center/table/tbody/tr[5]/td/select/option[10]'
seq_css_selector = '#g2pmain > div > center > table > tbody > tr:nth-child(8) > td > input[type=file]'
go_xpath = '//*[@id="XactionCell"]/input'
pdf_css_selector = '#g2pmain > div > table.navBar > tbody > tr > td.navTab > input[type=submit]'

# Processando cada arquivo individualmente
for arquivo_path in arquivos:
    
    pleres_data = retrieve_pleres_data(arquivo_path, desired_samples, folder_tropismo, temp_file)
   
    '''if pleres_data is None or pleres_data.empty:
        #logging.warning('Dados do Pleres não encontrados para o arquivo: %s', arquivo_path)
        continue'''
    
    csv_output_path = os.path.join(MEDIA_ROOT, "pleres.csv")
    pleres_data.to_csv(csv_output_path, index=False)
    
    # Dicionário a partir do CSV gerado
    id_to_controle = dict(zip(pleres_data['IdRecipiente'], pleres_data['controle']))
    
    # Nome base do arquivo (sem extensão)
    base_name = os.path.splitext(os.path.basename(arquivo_path))[0]
    
    sample_id = base_name.lstrip('0')
    controle_val = id_to_controle.get(int(sample_id))
    
    '''if controle_val is None:
        logging.warning('Valor de controle não encontrado para a amostra: %s', sample_id)
        continue'''
    
    # Criar subdiretório para salvar os arquivos do usuário
    arquivo_dir = os.path.join(user_dir, base_name)
    if not os.path.exists(arquivo_dir):
        os.makedirs(arquivo_dir)

    # Convertendo arquivos para .fas
    records = list(SeqIO.parse(arquivo_path, "fasta"))
    fas_path = os.path.join(arquivo_dir, base_name + '.fas')
    SeqIO.write(records, fas_path, "fasta")
        
    # Nome do arquivo baseado no controle da linha correta do CSV
    #controle_val = pleres_data.iloc[indice, -1]
    novo_nome_base = f"{controle_val}_29SP_3"

    # Copiar o arquivo .fasta com o novo nome e alterar o identificador da sequência
    novo_fasta_path = os.path.join(arquivo_dir, novo_nome_base + '.fasta')
    with open(novo_fasta_path, 'w') as novo_fasta_file:
        for record in records:
            record.id = novo_nome_base
            record.description = ""
            SeqIO.write(record, novo_fasta_file, "fasta")
            
    #logging.info(f"Processado arquivo {arquivo_path} com controle {controle_val}")
            
    # Abrir a página
    #logging.info("Abrindo a página: %s", url)
    driver.get(url)

    # Nomear amostras
    #logging.info("Nomeando amostras...")
    name_input = driver.find_element(By.XPATH, name_xpath)
    name_input.clear()
    name_input.send_keys(base_name)

    # Definir FPR
    #logging.info("Definindo FPR...")
    fpr_select = driver.find_element(By.XPATH, fpr_xpath)
    fpr_select.click()

    # Enviar arquivo .fasta
    #logging.info("Carregando sequência: %s", novo_fasta_path)
    seq_input = driver.find_element(By.CSS_SELECTOR, seq_css_selector)
    seq_input.send_keys(novo_fasta_path)

    # Executar análise
    #logging.info("Executando análise...")
    go_button = driver.find_element(By.XPATH, go_xpath)
    go_button.click()

    time.sleep(2)  

    # Baixar o PDF
    #logging.info("Baixando PDF...")
    pdf_button = driver.find_element(By.CSS_SELECTOR, pdf_css_selector)
    pdf_button.click()

    # Esperar o download completar
    download_complete = False
    while not download_complete:
        if any(file.endswith('.part') for file in os.listdir(dir_pdf)):
            time.sleep(1)
        else:
            download_complete = True

    # Mover e renomear o PDF para a subpasta correspondente
    for pdf_file in os.listdir(dir_pdf):
        if pdf_file.startswith('pdf'):
            pdf_path = os.path.join(dir_pdf, pdf_file)
            new_pdf_name = f"{novo_nome_base}.pdf"
            new_pdf_path = os.path.join(arquivo_dir, new_pdf_name)
            if not pdf_file.endswith('.pdf'):
                pdf_path_with_ext = pdf_path + '.pdf'
                os.rename(pdf_path, pdf_path_with_ext)
                pdf_path = pdf_path_with_ext
            shutil.move(pdf_path, new_pdf_path)
            #logging.info("PDF movido para: %s", new_pdf_path)
            
            try:
                
                sample_element = driver.find_element(By.XPATH, '//*[@id="g2pmain"]/div/table[2]/tbody/tr[1]/td/table/tbody/tr[1]/td')
                sample = sample_element.text.strip()

                subtype_element = driver.find_element(By.XPATH, '//*[@id="g2pmain"]/div/table[2]/tbody/tr[1]/td/table/tbody/tr[5]/td')
                subtype = subtype_element.text.strip()

                med_element = driver.find_element(By.XPATH, '//*[@id="g2pmain"]/div/table[2]/tbody/tr[4]/td/table/tbody/tr[2]/td[2]')
                med = med_element.text.strip()

                fpr_element = driver.find_element(By.XPATH, '//*[@id="g2pmain"]/div/table[2]/tbody/tr[4]/td/table/tbody/tr[2]/td[3]/center')
                fpr = fpr_element.text.strip()
 
                fasta_sequences = []
                fasta_names = []

                for file_name in os.listdir(arquivo_dir):
                    if file_name.endswith('.fasta'):
                        fasta_file = os.path.join(arquivo_dir, file_name)
                        for record in SeqIO.parse(fasta_file, 'fasta'):
                            fasta_sequences.append(str(record.seq))
                            fasta_names.append(file_name)

                # Única string com todas as sequencias 
                fasta = ''.join(fasta_sequences)

                # Corrigindo o problema do DataFrame pandas
                '''if len(fasta_sequences) != len(fasta_names):
                    logging.info("Error: The number of sequences does not match the number of fasta names.")
                else:'''
                # DataFrame 'teste'
                teste = pd.DataFrame({
                    'Sample': [sample] * len(fasta_sequences),
                    'Subtype': [subtype] * len(fasta_sequences),
                    'Phrase': [med] * len(fasta_sequences),
                    'FPR': [fpr] * len(fasta_sequences),
                    'Sequence': fasta_sequences,
                    'Fasta_Name': fasta_names
                })
                #logging.info("DataFrame 'teste' created successfully.")
                    
                #logging.info("Fasta sequences combined into a single string:")
                
                execute_with_retry()
                
                try:
                    #logging.info("Clicking element...")
                    element = driver.find_element(By.XPATH, '//*[@id="B1861320711414522"]/span')
                    element.click()
                    time.sleep(1)

                    #logging.info("Selecting refseq set...")
                    refseq_set = driver.find_element(By.XPATH, '//*[@id="P7_REFSEQ_SET"]/option[1]')
                    refseq_set.click()
                    time.sleep(1)

                    #logging.info("Selecting ref sequences...")
                    ref_seqs = driver.find_element(By.XPATH, '//*[@id="P7_REF_SEQS"]/option[6]')
                    ref_seqs.click()
                    time.sleep(1)

                    #logging.info("Clicking button...")
                    button = driver.find_element(By.CSS_SELECTOR, '#B3950511621674168 > span')
                    button.click()
                    time.sleep(1)

                    #logging.info("Clearing nt sequence...")
                    nt_seq = driver.find_element(By.XPATH, '//*[@id="P8_NT_SEQ"]')
                    nt_seq.clear()
                    time.sleep(1)

                    #logging.info("Sending nt sequence...")
                    nt_seq.send_keys(fasta)
                    time.sleep(1)

                    #logging.info("Clicking mutation button...")
                    button_mut = driver.find_element(By.XPATH, '//*[@id="B1860502286414521"]/span')
                    button_mut.click()
                    time.sleep(1)

                    #logging.info("Getting mutations...")
                    mutations = driver.find_element(By.XPATH, '//*[@id="P8_MUTATIONS_1"]')
                    mut = mutations.text
                    time.sleep(1)

                    #logging.info("Getting deletions...")
                    deletions = driver.find_element(By.XPATH, '//*[@id="P8_DELETIONS_1"]')
                    del_val = deletions.text
                    time.sleep(1)

                    #logging.info("Getting insertions...")
                    insertions = driver.find_element(By.XPATH, '//*[@id="P8_INSERTIONS_1"]')
                    ins_val = insertions.text
                    time.sleep(1)

                    # Processing mutations
                    #logging.info("Processing mutations...")
                    a = [x.strip() for x in mut.split(",")]
                    a = [x for x in a if re.match('[A-Z][0-9]+', x)]
                    index = [int(re.sub('[A-Z]([0-9]*).*', '\\1', x)) for x in a]
                    
                    #fn = [str(idx + 28) + m for idx, m in zip(index, a)]
                    fn = [re.sub('([A-Z])([0-9]+)', lambda m: m.group(1) + str(int(m.group(2)) + 28), x) for x in a]
                    
                    a = [x for x in fn if int(re.sub('[A-Z]([0-9]*).*', '\\1', x)) in range(300, 336)]

                    # Processing deletions
                    #logging.info("Processing deletions...")
                    index_del = [int(re.sub('\\D', '', x)) for x in del_val.split(",")]
                    k_del = [x + 28 for x in index_del]
                    b = [f"del{x}" for x in k_del if x in range(300, 336)]

                    # Processing insertions
                    #logging.info("Processing insertions...")
                
                    ins_split = [re.sub("([0-9]+)([A-Z])", lambda m: str(int(m.group(1)) + 28) + "ins" + m.group(2), x.strip()) for x in ins_val.split(",")]
                    index_ins = [int(re.sub('\\D', '', x)) for x in ins_split]
                    fn_ins = [re.sub('([A-Z])([0-9]+)', lambda m: m.group(1) + str(int(m.group(2)) + 28), x) for x in ins_split]
                    c = [x for x in fn_ins if int(re.sub('[A-Za-z]([0-9]*)', '\\1', x)) in range(300, 336)]

                    
                    all_mut = a + b + c
                    all_mut.sort(key=lambda x: int(re.sub("\\D", "", x)))

                    # Converting all_mut to DataFrame
                    t = pd.DataFrame([all_mut])
                    v = pd.concat([teste, t], axis=1)
                    
                    # Removendo a extensão '.fasta' da coluna sample 
                    teste['Sample'] = teste['Sample'].str.replace('.fasta', '')
                    
                    # Nome do arquivo CSV com o mesmo nome base do PDF
                    csv_output_path = os.path.join(arquivo_dir, f"{novo_nome_base}.csv")
                    v.to_csv(csv_output_path, index=False)
                    #logging.info("CSV movido para: %s", csv_output_path)
                    
                    add_mutations_to_pdf(csv_output_path, new_pdf_path)
                    
                except Exception as e:
                    logging.info("Error in second part of processing:")
                    
            except Exception as e:
                logging.info("Error in first part of processing:")
                
# Closing the browser
#logging.info('Closing driver')
driver.quit()















