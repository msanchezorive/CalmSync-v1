import serial
import time
from generic_parser import parse_packet, extract_data_from_payload

# ===== CONFIG =====
PORT = "COM10" #cambiarlo segun el port que use tu ordenador 
BAUD = 57600

# Códigos de NeuroSky
CODE_HANDLERS_ATT_MED = {0x04: 'attention', 0x05: 'meditation'}
CODE_HANDLERS_EEG = {0x83: 'eeg_power'}

# Índices de bandas
#esto por que el eeg_power devuelve una lista así [Delta, Theta, Low-Alpha, High-Alpha, Low-Beta, High-Beta, Low-Gamma, Mid-Gamma]

ALPHA_IDX = [2, 3]  # Low-Alpha, High-Alpha
BETA_IDX = [4, 5]   # Low-Beta, High-Beta

# Suavizado exponencial , esto sirve para hacer una media de valores 
SMOOTHING_ALPHA = 0.2

# ===== VARIABLES =====
state = {
    'attention': 0,
    'meditation': 0,
    'alpha': 0,
    'beta': 0
}

# ===== FUNCIONES =====
def get_attention(payload):
    data = extract_data_from_payload(payload, CODE_HANDLERS_ATT_MED)
    if 'attention' in data:
        val = data['attention']
        state['attention'] = SMOOTHING_ALPHA*val + (1-SMOOTHING_ALPHA)*state['attention']
        return state['attention']
    return state['attention']

def get_meditation(payload):
    data = extract_data_from_payload(payload, CODE_HANDLERS_ATT_MED)
    if 'meditation' in data:
        val = data['meditation']
        state['meditation'] = SMOOTHING_ALPHA*val + (1-SMOOTHING_ALPHA)*state['meditation']
        return state['meditation']
    return state['meditation']

def get_alpha(payload):
    data = extract_data_from_payload(payload, CODE_HANDLERS_EEG)
    if 'eeg_power' in data:
        powers = data['eeg_power']
        alpha_val = sum([powers[i] for i in ALPHA_IDX]) / len(ALPHA_IDX)
        state['alpha'] = SMOOTHING_ALPHA*alpha_val + (1-SMOOTHING_ALPHA)*state['alpha']
        return state['alpha']
    return state['alpha']

def get_beta(payload):
    data = extract_data_from_payload(payload, CODE_HANDLERS_EEG)
    if 'eeg_power' in data:
        powers = data['eeg_power']
        beta_val = sum([powers[i] for i in BETA_IDX]) / len(BETA_IDX)
        state['beta'] = SMOOTHING_ALPHA*beta_val + (1-SMOOTHING_ALPHA)*state['beta']
        return state['beta']
    return state['beta']
    

# codigo modo ejemplo para ver las 4 variables 
try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print(f"✅ Conectado a {PORT} @ {BAUD} baud")
    print("📊 Leyendo en tiempo real: atención, meditación, alfa, beta...\n")

    while True:
        payload = parse_packet(ser)
        if payload is None:
            continue

        att = get_attention(payload)
        med = get_meditation(payload)
        alpha = get_alpha(payload)
        beta = get_beta(payload)

        print(f"Atención: {att:6.1f} | Meditación: {med:6.1f} | Alfa: {alpha:8.1f} | Beta: {beta:8.1f}", end='\r')

except KeyboardInterrupt:
    print("\n\n🧠 Lectura detenida por usuario.")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("🔌 Puerto cerrado correctamente.")
