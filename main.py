from crawl4ai import AsyncWebCrawler
from weasyprint import HTML
from fastapi import FastAPI,HTTPException
from datetime import datetime
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import asyncio
import os
import re



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)






class Manga(BaseModel):
    link: str



@app.post("/")
async def main(manga: Manga):
    try:
        name,chapter,fullname = extract_informations(manga.link)
        await createManga(fullname,name,manga.link)
        return {"response": f"{fullname} saved"}
    except:
        return {"response": "Something went wrong"}




async def createManga(name, folder, link):
    # Folder kontrolü ve oluşturma
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(link)
        html = result.cleaned_html
        html5 = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{name}</title>
        """
        
        img_urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        for image in img_urls:
            if "data" in image:
                img = f"<img src='{image}' style='width:100%;'> <br> \n"
                html5 += img
        
        html5 += "</head>\n<body></body></html>"
        
        # Dosya yollarını folder ile birleştir
        html_path = os.path.join(folder, f"{name}.html")
        pdf_path = os.path.join(folder, f"{name}.pdf")
        
        with open(html_path, "w") as file:  # "x" yerine "w" kullan
            file.write(html5)
        
        HTML(html_path).write_pdf(pdf_path)
        os.remove(html_path)


def extract_informations(link):
    parts = link.strip("/").split("/")
    name = parts[4] if len(parts) > 4 else "unknown"
    episode = parts[5] if len(parts) > 5 and parts[5] else name
    fullname = f"{name} - {episode}"

    return name, episode, fullname








# PDF okuma endpoint'leri
@app.get("/read/{series_name}/{chapter_name}")
async def read_chapter(series_name: str, chapter_name: str):
    """PDF dosyasını okuma için döndür"""
    try:
        file_path = os.path.join(series_name, chapter_name)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Bölüm bulunamadı")
        
        if not chapter_name.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Sadece PDF dosyaları okunabilir")
        
        return FileResponse(
            file_path,
            media_type='application/pdf',
            headers={"Content-Disposition": f"inline; filename={chapter_name}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{series_name}/{chapter_name}")
async def download_chapter(series_name: str, chapter_name: str):
    """PDF dosyasını indirme için döndür"""
    try:
        file_path = os.path.join(series_name, chapter_name)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Bölüm bulunamadı")
        
        if not chapter_name.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Sadece PDF dosyaları indirilebilir")
        
        return FileResponse(
            file_path,
            media_type='application/pdf',
            filename=chapter_name,
            headers={"Content-Disposition": f"attachment; filename={chapter_name}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Arayüz için ekstra fonksiyonlar
@app.get("/series")
async def get_series_list():
    """Mevcut manga serilerini listele"""
    try:
        if not os.path.exists("."):
            return []
        
        series_list = []
        for item in os.listdir("."):
            if os.path.isdir(item) and not item.startswith('.'):
                chapter_count = len([f for f in os.listdir(item) if f.endswith('.pdf')])
                if chapter_count > 0:  # Sadece PDF'i olan klasörleri göster
                    series_list.append({
                        "name": item,
                        "chapter_count": chapter_count,
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(item)).strftime("%Y-%m-%d %H:%M")
                    })
        
        return sorted(series_list, key=lambda x: x["last_modified"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/series/{series_name}/chapters")
async def get_chapters_in_series(series_name: str):
    """Serideki bölümleri listele"""
    try:
        if not os.path.exists(series_name):
            raise HTTPException(status_code=404, detail="Seri bulunamadı")
        
        chapters = []
        for file in os.listdir(series_name):
            if file.endswith('.pdf'):
                file_path = os.path.join(series_name, file)
                file_size = os.path.getsize(file_path)
                chapters.append({
                    "name": file,
                    "size": f"{file_size / 1024 / 1024:.2f} MB",
                    "date": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M")
                })
        
        return sorted(chapters, key=lambda x: x["name"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/series/{series_name}/chapters/{chapter_name}")
async def delete_chapter(series_name: str, chapter_name: str):
    """Bölüm sil"""
    try:
        file_path = os.path.join(series_name, chapter_name)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Bölüm bulunamadı")
        
        if not chapter_name.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Sadece PDF dosyaları silinebilir")
        
        os.remove(file_path)
        
        # Klasör boşsa sil
        if len(os.listdir(series_name)) == 0:
            os.rmdir(series_name)
            return {"response": f"{chapter_name} silindi ve {series_name} klasörü boş olduğu için silindi"}
        
        return {"response": f"{chapter_name} silindi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/series/{series_name}")
async def delete_series(series_name: str):
    """Seriyi tamamen sil"""
    try:
        if not os.path.exists(series_name):
            raise HTTPException(status_code=404, detail="Seri bulunamadı")
        
        import shutil
        shutil.rmtree(series_name)
        return {"response": f"{series_name} serisi tamamen silindi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/series/{series_name}/open")
async def open_series_folder(series_name: str):
    """Seri klasörünü dosya yöneticisinde aç"""
    try:
        if not os.path.exists(series_name):
            raise HTTPException(status_code=404, detail="Seri bulunamadı")
        
        import subprocess
        import platform
        
        if platform.system() == "Windows":
            subprocess.run(["explorer", os.path.abspath(series_name)])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", os.path.abspath(series_name)])
        else:  # Linux
            subprocess.run(["xdg-open", os.path.abspath(series_name)])
        
        return {"response": f"{series_name} klasörü açıldı"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Genel istatistikler"""
    try:
        total_series = 0
        total_chapters = 0
        total_size = 0
        
        for item in os.listdir("."):
            if os.path.isdir(item) and not item.startswith('.'):
                chapter_count = 0
                for file in os.listdir(item):
                    if file.endswith('.pdf'):
                        chapter_count += 1
                        total_size += os.path.getsize(os.path.join(item, file))
                
                if chapter_count > 0:
                    total_series += 1
                    total_chapters += chapter_count
        
        return {
            "total_series": total_series,
            "total_chapters": total_chapters,
            "total_size": f"{total_size / 1024 / 1024:.2f} MB"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)