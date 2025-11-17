import serial
import struct

# ============================================================================
# PARSER GENÉRICO - Funciones Reutilizables
# ============================================================================

def verify_checksum(payload):
    """
    Verifica la integridad del payload.
    
    Algoritmo:
    1. Suma todos los bytes
    2. Toma solo los 8 bits inferiores
    3. Invierte los bits (complemento a uno)
    4. Retorna el checksum
    
    Args:
        payload: lista de bytes
    
    Returns:
        byte de verificación calculado
    """
    checksum = sum(payload) & 0xFF
    checksum = (~checksum) & 0xFF
    return checksum


def parse_packet(ser):
    """
    Lee 1 paquete completo del puerto serial.
    
    Proceso:
    1. Busca bytes de sincronización (0xAA 0xAA)
    2. Lee la longitud del payload
    3. Lee exactamente ese número de bytes
    4. Verifica el checksum
    5. Retorna el payload si todo es válido
    
    Args:
        ser: puerto serial abierto
    
    Returns:
        lista de bytes (payload) si es válido
        None si hay error o timeout
    """
    SYNC = 0xAA
    
    # Buscar sincronización (0xAA 0xAA)
    while True:
        byte1 = ser.read(1)
        if not byte1 or byte1[0] != SYNC:
            continue
        byte2 = ser.read(1)
        if byte2 and byte2[0] == SYNC:
            break
    
    # Leer longitud del payload
    plen_byte = ser.read(1)
    if not plen_byte or plen_byte[0] > 169:
        return None
    plen = plen_byte[0]
    
    # Leer payload
    payload = ser.read(plen)
    if len(payload) != plen:
        return None
    
    # Verificar checksum
    checksum_byte = ser.read(1)
    if not checksum_byte or checksum_byte[0] != verify_checksum(payload):
        return None
    
    return payload


def process_value(code, data_bytes):
    """
    Procesa bytes según el tipo de código.
    
    Tipos soportados:
    - 0x80: RAW Wave (2 bytes, big-endian signed)
    - 0x83: ASIC EEG Power (8 x 3 bytes, big-endian unsigned)
    - Otros: conversión genérica big-endian
    
    Args:
        code: código del dato (0x80, 0x83, etc)
        data_bytes: bytes a procesar
    
    Returns:
        valor procesado (número o lista)
    """
    if code == 0x80:  # RAW Wave (2 bytes big-endian signed)
        return struct.unpack('>h', data_bytes)[0]
    
    elif code == 0x83:  # EEG Power (8 x 3 bytes)
        powers = []
        for j in range(8):
            bytes_val = data_bytes[j*3:j*3+3]
            power = (bytes_val[0] << 16) | (bytes_val[1] << 8) | bytes_val[2]
            powers.append(power)
        return powers
    
    else:
        return int.from_bytes(data_bytes, 'big')


def extract_data_from_payload(payload, code_handlers):
    """
    Parsea el payload y extrae los datos solicitados.
    
    Proceso:
    1. Recorre el payload byte a byte
    2. Identifica códigos y valores
    3. Procesa solo los códigos en code_handlers
    4. Retorna diccionario con resultados
    
    Args:
        payload: lista de bytes del payload
        code_handlers: dict {código: nombre}
                      Ejemplo: {0x04: 'attention', 0x83: 'eeg_power'}
    
    Returns:
        dict {nombre: valor procesado}
        Ejemplo: {'attention': 13, 'eeg_power': [148, 66, 11, ...]}
    """
    results = {}
    i = 0
    
    while i < len(payload):
        # Contar EXCODE (0x55) - Nivel de extensión
        excode_level = 0
        while i < len(payload) and payload[i] == 0x55:
            excode_level += 1
            i += 1
        
        if i >= len(payload):
            break
        
        # Leer código
        code = payload[i]
        i += 1
        
        # ¿Multi-byte (>= 0x80) o Single-byte (< 0x80)?
        if code >= 0x80:  # Multi-byte: [CODE] [LENGTH] [VALUE...]
            if i >= len(payload):
                break
            length = payload[i]
            i += 1
            
            # Verificar que hay suficientes bytes
            if i + length <= len(payload):
                data_bytes = payload[i:i+length]
                
                # Si pediste este código, procésalo
                if code in code_handlers:
                    name = code_handlers[code]
                    results[name] = process_value(code, data_bytes)
            
            i += length
        
        else:  # Single-byte: [CODE] [VALUE]
            if i < len(payload):
                value = payload[i]
                i += 1
                
                # Si pediste este código, guárdalo
                if code in code_handlers:
                    name = code_handlers[code]
                    results[name] = value
    
    return results