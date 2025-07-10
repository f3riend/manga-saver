import eel
import asyncio
import threading
import uvicorn
from main import app as fastapi_app
import os
import sys

# Eel'i başlat
eel.init('web')

# FastAPI sunucusunu ayrı thread'de çalıştır
def run_fastapi_server():
    """FastAPI sunucusunu arka planda çalıştır"""
    try:
        uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="error")
    except Exception as e:
        print(f"FastAPI sunucusu başlatılırken hata: {e}")

# Eel fonksiyonları (isteğe bağlı - direkt API kullanılabilir)
@eel.expose
def get_app_info():
    """Uygulama bilgilerini döndür"""
    return {
        "name": "Advanced Manga Saver",
        "version": "1.0.0",
        "api_url": "http://127.0.0.1:8000"
    }

@eel.expose
def open_downloads_folder():
    """İndirme klasörünü aç"""
    try:
        import subprocess
        import platform
        
        current_dir = os.getcwd()
        
        if platform.system() == "Windows":
            subprocess.run(["explorer", current_dir])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", current_dir])
        else:  # Linux
            subprocess.run(["xdg-open", current_dir])
        
        return True
    except Exception as e:
        print(f"Klasör açılırken hata: {e}")
        return False

@eel.expose
def minimize_to_tray():
    """Uygulamayı sistem tepsisine küçült (gelecek özellik)"""
    # Bu özellik için system tray kütüphanesi gerekli
    pass

def main():
    """Ana uygulama başlatıcısı"""
    print("🎌 Advanced Manga Saver başlatılıyor...")
    
    # FastAPI sunucusunu arka planda başlat
    print("📡 API sunucusu başlatılıyor...")
    fastapi_thread = threading.Thread(target=run_fastapi_server, daemon=True)
    fastapi_thread.start()
    
    # Kısa bir süre bekle ki sunucu hazır olsun
    import time
    time.sleep(2)
    
    # Eel arayüzünü başlat
    print("🖥️ Arayüz açılıyor...")
    try:
        eel.start(
            'index.html',
            size=(1200, 800),
            position=(100, 100),
            disable_cache=True,
            host='localhost',
            port=8080,
            close_callback=on_close
        )
    except Exception as e:
        print(f"Arayüz başlatılırken hata: {e}")
        input("Programı kapatmak için Enter tuşuna basın...")

def on_close(route, websockets):
    """Uygulama kapatılırken çağrılır"""
    print("👋 Uygulama kapatılıyor...")
    # Cleanup işlemleri burada yapılabilir
    sys.exit(0)

if __name__ == "__main__":
    main()