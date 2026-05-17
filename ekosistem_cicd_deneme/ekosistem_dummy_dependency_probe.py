# ekosistem_dummy_probe.py

# --- KIPKIRMIZI BÖLGE (Kritik / Zafiyetli / Terk Edilmiş) ---
import pycrypto          # Yıllar önce terk edildi, devasa açıklar var
import yaml              # PyYAML'ın eski sürümlerinde RCE (Uzaktan Kod Çalıştırma) açığı meşhurdur
import PIL               # Pillow'un eski sürümleri görüntü işleme zafiyetleriyle doludur
import urllib3           # Ağ katmanı zafiyetleri
import lxml              # XML External Entity (XXE) zafiyetleri
import paramiko          # Eski sürümlerinde SSH zafiyetleri var
import oauth2            # Deprecated (kullanımdan kaldırılmış) paket

# --- SARI BÖLGE (Orta Risk / Teknik Borç / Eskimiş) ---
import django            # Eski sürüm simülasyonu için
import flask             # Microframework, eski bağımlılıklar tetikleyebilir
import celery            # Task queue, bağımlılık ağacı çok derindir
import redis             # Standart ama eski sürümleri risklidir
import tornado           # Modern asenkron yapıların gerisinde kalmış olabilir
import werkzeug          # Flask'ın alt katmanı, sık sık orta seviye uyarı verir
import bs4               # BeautifulSoup, eski bağımlılıkları olabilir
import sqlalchemy        # ORM, çok fazla dolaylı bağımlılık çeker
import psycopg2          # PostgreSQL adaptörü

# --- YEŞİL BÖLGE (Güvenli / Modern / Güncel) ---
import fastapi           # Modern, hızlı ve temiz
import pydantic          # Veri doğrulama, son derece güvenli
import cryptography      # Pycrypto'nun modern ve güvenli alternatifi
import httpx             # Modern asenkron HTTP istemcisi
import numpy             # Veri bilimi standardı
import pandas            # Veri analizi standardı
import pytest            # Modern test kütüphanesi
import rich              # Terminal renklendirme, güvenli
import typer             # Modern CLI aracı
import uvicorn           # ASGI sunucusu