#libraries for QR code reading and image processing
import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar
import urllib.request
from datetime import datetime

#libraries for Google Sheets and Drive
from google.oauth2.service_account import Credentials
import gspread

# --- Configurações Iniciais ---
# IP address of the ESP32-CAM
url_cam='http://192.168.0.10/'  #substitua pelo Endereço IP encontrado no monitor serial ao executar o arquivo .ino na sua ESP32
# Caminho para o arquivo de credenciais
credentials_filename = 'credentials.json'  #credenciais do Google Cloud API
# Nome da Planilha Google
spreadsheet_name = "Nome-da-sua-planilha"

# Escopos de permissão necessários
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# --- Bloco Principal de Execução ---
try:
    # --- Autenticação e Conexão com Google Sheets ---
    print("Iniciando autenticação com Google API...")
    creds = Credentials.from_service_account_file(credentials_filename, scopes=scopes)
    gc = gspread.authorize(creds)
    print("Autenticação bem-sucedida!")
    
    print(f"Abrindo a planilha '{spreadsheet_name}'...")
    spreadsheet = gc.open(spreadsheet_name)
    worksheet = spreadsheet.sheet1 # Seleciona a primeira página da planilha
    print(f"Planilha '{spreadsheet.title}' e aba selecionada com sucesso. Iniciando leitor de QR Code.")
    
    # --- Inicialização da Câmera e Variáveis ---
    font = cv2.FONT_HERSHEY_PLAIN
    cv2.namedWindow("live transmission", cv2.WINDOW_AUTOSIZE)
    prev_data = ""

    # --- Loop Principal de Leitura do QR Code ---
    # Este loop só começa se a autenticação e a abertura da planilha derem certo.
    while True:
        img_resp=urllib.request.urlopen(url_cam+'cam-lo.jpg')
        imgnp=np.array(bytearray(img_resp.read()),dtype=np.uint8)
        frame=cv2.imdecode(imgnp,-1)
    
        decodedObjects = pyzbar.decode(frame)
        for obj in decodedObjects:
            present_data = obj.data
            if prev_data == present_data:
                pass
            else:
                print("\n--- Novo QR Code Detectado ---")
                prev_data = present_data
                raw_data = obj.data.decode('utf-8')
                print("Data (Raw): ", raw_data)

                # Tenta processar os dados e adicionar na planilha
                try:
                    parsed_data = {}
                    for line in raw_data.splitlines():
                        if ':' in line:
                            key, value = line.split(':', 1)
                            parsed_data[key.strip()] = value.strip()
                    
                    now = datetime.now()
                    current_date = now.strftime('%d/%m/%Y')
                    current_time = now.strftime('%H:%M:%S')

                    row_to_add = [
                        parsed_data.get('aluno', 'N/A'),
                        parsed_data.get('matricula', 'N/A'),
                        parsed_data.get('codigoDisciplina', 'N/A'),
                        parsed_data.get('disciplina', 'N/A'),
                        current_date,
                        current_time
                    ]

                    worksheet.append_row(row_to_add)
                    print(f"SUCESSO: Linha adicionada na planilha -> {row_to_add}")

                except Exception as e_parse:
                    print(f"ERRO: Não foi possível processar os dados do QR Code. Detalhes: {e_parse}")
                    
            cv2.putText(frame, str(obj.data.decode('utf-8')), (50, 50), font, 2, (255, 0, 0), 3)

        cv2.imshow("live transmission", frame)
    
        key = cv2.waitKey(1)
        if key == 27: #ESC key to break
            break
            
    cv2.destroyAllWindows()

# --- Tratamento de Erros de Conexão/Autenticação ---
except FileNotFoundError:
    print(f"ERRO CRÍTICO: O arquivo de credenciais '{credentials_filename}' não foi encontrado. O programa não pode iniciar.")
except gspread.exceptions.SpreadsheetNotFound:
    print(f"ERRO CRÍTICO: Planilha '{spreadsheet_name}' não encontrada. Verifique o nome ou se ela foi compartilhada com o e-mail da sua credencial.")
except Exception as e_auth:
    print(f"ERRO CRÍTICO durante a autenticação ou ao abrir a planilha: {e_auth}")
