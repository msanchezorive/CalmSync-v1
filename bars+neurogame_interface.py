"""
Interfaz Integrada - CalmSync
Ejecuta simultáneamente el juego de neurofeedback y el visualizador de barras.
"""

import subprocess
import sys
import os
import time
import argparse

def main():
    parser = argparse.ArgumentParser(
        description='Interfaz Integrada - CalmSync Neurofeedback',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python integrated_interface.py              # Modo real (NeuroSky)
  python integrated_interface.py --simulate   # Modo simulación
        """
    )
    parser.add_argument(
        '--simulate', 
        action='store_true',
        help='Ejecuta en modo simulación (sin NeuroSky)'
    )
    
    args = parser.parse_args()
    
    # Determina el modo
    mode_arg = ['--simulate'] if args.simulate else []
    mode_text = "SIMULACIÓN" if args.simulate else "TIEMPO REAL"
    
    print("\n" + "="*70)
    print("🎮 CALMSYNC - INTERFAZ INTEGRADA")
    print("="*70)
    print(f"📊 Modo: {mode_text}")
    print("\n🚀 Iniciando componentes...")
    print("-" * 70)
    
    # Verifica que los archivos existen
    required_files = [
        'neurofeedback_game.py',
        'bars+neurogame_interface.py',
        'generic_parser.py'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("❌ ERROR: Archivos faltantes:")
        for f in missing_files:
            print(f"   - {f}")
        print("\n💡 Asegúrate de tener todos los archivos en el mismo directorio.")
        sys.exit(1)
    
    processes = []
    
    try:
        # Inicia el visualizador de barras
        print("📊 Iniciando visualizador de barras EEG...")
        bars_process = subprocess.Popen(
            [sys.executable, 'bars+neurogame_interface.py'] + mode_arg,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(('Barras EEG', bars_process))
        time.sleep(1)  # Espera para que inicie
        
        # Inicia el juego de neurofeedback
        print("🎮 Iniciando juego de neurofeedback...")
        game_process = subprocess.Popen(
            [sys.executable, 'neurofeedback_game.py'] + mode_arg,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(('Juego', game_process))
        
        print("-" * 70)
        print("✅ Ambos componentes iniciados correctamente")
        print("\n📌 INSTRUCCIONES:")
        print("   • Ambas ventanas se ejecutan simultáneamente")
        print("   • Cierra cualquier ventana para detener todo")
        print("   • O presiona Ctrl+C aquí")
        print("\n🧠 TIP: Coloca las ventanas lado a lado para ver:")
        print("   - Izquierda: Barras Alpha/Beta en tiempo real")
        print("   - Derecha: Escenario que cambia según tu estado mental")
        print("\n⏳ Monitoreando procesos...")
        print("="*70 + "\n")
        
        # Monitorea los procesos
        while True:
            time.sleep(0.5)
            
            # Verifica si algún proceso terminó
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"\n⚠️  {name} terminó (código: {proc.returncode})")
                    
                    # Si uno termina, termina el otro
                    for other_name, other_proc in processes:
                        if other_proc != proc and other_proc.poll() is None:
                            print(f"🛑 Deteniendo {other_name}...")
                            other_proc.terminate()
                            other_proc.wait(timeout=3)
                    
                    print("\n👋 Sesión finalizada.")
                    return
    
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupción detectada (Ctrl+C)")
        print("🧹 Limpiando procesos...")
        
        for name, proc in processes:
            if proc.poll() is None:
                print(f"   • Deteniendo {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print(f"   ⚠️ {name} no respondió, forzando cierre...")
                    proc.kill()
                    proc.wait()
        
        print("✅ Todos los procesos detenidos")
        print("\n👋 Sesión finalizada correctamente.\n")
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("🧹 Limpiando procesos...")
        
        for name, proc in processes:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=3)
        
        sys.exit(1)


if __name__ == "__main__":
    main()