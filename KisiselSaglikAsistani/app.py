from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import json
import mysql.connector
from dotenv import load_dotenv
import os
import hashlib

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
app.secret_key = 'gizli_anahtar_123'

# Veritabanı bağlantı bilgileri
DB_HOST = 'localhost'
DB_DATABASE = 'KisiselSaglikDB'
DB_USERNAME = 'root'  # MySQL'de varsayılan kullanıcı
DB_PASSWORD = '1212'

# Veritabanı bağlantı fonksiyonu
def get_db_connection():
    conn = mysql.connector.connect(
        host=DB_HOST,
        database=DB_DATABASE,
        user=DB_USERNAME,
        password=DB_PASSWORD
    )
    return conn

# BMI kategorileri
BMI_CATEGORIES = {
    'zayif': {'min': 0, 'max': 18.5},
    'normal': {'min': 18.5, 'max': 24.9},
    'kilolu': {'min': 25, 'max': 29.9},
    'obez': {'min': 30, 'max': float('inf')}
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Kullanıcı adı kontrolü
            cursor.execute("SELECT UserID FROM Users WHERE Username = %s", (username,))
            if cursor.fetchone():
                flash('Bu kullanıcı adı zaten kullanımda!')
                return redirect(url_for('register'))
            
            # Yeni kullanıcı oluştur
            cursor.execute(
                "INSERT INTO Users (Username, Password) VALUES (%s, %s)",
                (username, password)
            )
            conn.commit()
            flash('Kayıt başarılı! Giriş yapabilirsiniz.')
            return redirect(url_for('login'))
            
        except Exception as e:
            conn.rollback()
            flash('Kayıt sırasında bir hata oluştu!')
            print(f"Hata: {str(e)}")
        finally:
            cursor.close()
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT UserID FROM Users WHERE Username = %s AND Password = %s",
                (username, password)
            )
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user[0]
                session['username'] = username
                return redirect(url_for('dashboard'))
            
            flash('Geçersiz kullanıcı adı veya şifre!')
        finally:
            cursor.close()
            conn.close()
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Kullanıcı profili
        cursor.execute(
            "SELECT * FROM UserProfiles WHERE UserID = %s",
            (session['user_id'],)
        )
        profile = cursor.fetchone()
        
        # Son sağlık verileri
        cursor.execute("""
            SELECT * FROM HealthData 
            WHERE UserID = %s 
            ORDER BY KayitTarihi DESC
            LIMIT 1
        """, (session['user_id'],))
        health_data = cursor.fetchone()
        
        user_data = {
            'profile': {
                'boy': profile[2] if profile else 0,
                'kilo': profile[3] if profile else 0,
                'yas': profile[4] if profile else 0,
                'cinsiyet': profile[5] if profile else ''
            },
            'health_data': {
                'su_tuketimi': health_data[2] if health_data else 0,
                'uyku_suresi': health_data[3] if health_data else 0,
                'adim_sayisi': health_data[4] if health_data else 0,
                'ruh_hali': health_data[5] if health_data else ''
            }
        }
        
        recommendations = generate_recommendations(user_data)
        return render_template('dashboard.html', user=user_data, recommendations=recommendations)
    
    finally:
        cursor.close()
        conn.close()

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        boy = float(request.form['boy'])
        kilo = float(request.form['kilo'])
        yas = int(request.form['yas'])
        cinsiyet = request.form['cinsiyet']
        
        try:
            # Mevcut profili kontrol et
            cursor.execute(
                "SELECT ProfileID FROM UserProfiles WHERE UserID = %s",
                (session['user_id'],)
            )
            profile = cursor.fetchone()
            
            if profile:
                # Güncelle
                cursor.execute("""
                    UPDATE UserProfiles 
                    SET Boy = %s, Kilo = %s, Yas = %s, Cinsiyet = %s, LastUpdated = CURRENT_TIMESTAMP()
                    WHERE UserID = %s
                """, (boy, kilo, yas, cinsiyet, session['user_id']))
            else:
                # Yeni profil oluştur
                cursor.execute("""
                    INSERT INTO UserProfiles (UserID, Boy, Kilo, Yas, Cinsiyet)
                    VALUES (%s, %s, %s, %s, %s)
                """, (session['user_id'], boy, kilo, yas, cinsiyet))
            
            conn.commit()
            flash('Profil bilgileri güncellendi!')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            conn.rollback()
            flash('Profil güncellenirken bir hata oluştu!')
            print(f"Hata: {str(e)}")
        
    try:
        # Mevcut profil bilgilerini getir
        cursor.execute(
            "SELECT * FROM UserProfiles WHERE UserID = %s",
            (session['user_id'],)
        )
        profile = cursor.fetchone()
        
        user_data = {
            'profile': {
                'boy': profile[2] if profile else 0,
                'kilo': profile[3] if profile else 0,
                'yas': profile[4] if profile else 0,
                'cinsiyet': profile[5] if profile else ''
            }
        }
        
        return render_template('profile.html', user=user_data)
        
    finally:
        cursor.close()
        conn.close()

@app.route('/daily_health', methods=['GET', 'POST'])
def daily_health():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO HealthData 
                (UserID, SuTuketimi, UykuSuresi, AdimSayisi, RuhHali)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                session['user_id'],
                int(request.form['su_tuketimi']),
                float(request.form['uyku_suresi']),
                int(request.form['adim_sayisi']),
                request.form['ruh_hali']
            ))
            
            conn.commit()
            flash('Günlük sağlık verileri kaydedildi!')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            conn.rollback()
            flash('Veriler kaydedilirken bir hata oluştu!')
            print(f"Hata: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('daily_health.html')

@app.route('/statistics')
def statistics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Son 7 günlük verileri getir
        cursor.execute("""
            SELECT 
                KayitTarihi,
                SuTuketimi,
                UykuSuresi,
                AdimSayisi,
                RuhHali
            FROM HealthData 
            WHERE UserID = %s
            AND KayitTarihi >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
            ORDER BY KayitTarihi DESC
        """, (session['user_id'],))
        
        health_data = {
            'su_tuketimi': [],
            'uyku_suresi': [],
            'adim_sayisi': [],
            'ruh_hali': []
        }
        
        for row in cursor.fetchall():
            date_str = row[0].strftime('%Y-%m-%d')
            health_data['su_tuketimi'].append({'date': date_str, 'value': row[1]})
            health_data['uyku_suresi'].append({'date': date_str, 'value': row[2]})
            health_data['adim_sayisi'].append({'date': date_str, 'value': row[3]})
            health_data['ruh_hali'].append({'date': date_str, 'value': row[4]})
        
        return render_template('statistics.html', data=health_data)
        
    finally:
        cursor.close()
        conn.close()

@app.route('/calculate_bmi')
def calculate_bmi():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT Boy, Kilo FROM UserProfiles WHERE UserID = %s",
            (session['user_id'],)
        )
        profile = cursor.fetchone()
        
        if not profile or profile[0] == 0 or profile[1] == 0:
            flash('Lütfen önce profil bilgilerinizi doldurun!')
            return redirect(url_for('profile'))
        
        boy_metre = profile[0] / 100
        bmi = profile[1] / (boy_metre * boy_metre)
        
        category = None
        for cat, limits in BMI_CATEGORIES.items():
            if limits['min'] <= bmi <= limits['max']:
                category = cat
                break
        
        # BMI değerini kaydet
        cursor.execute("""
            INSERT INTO BMIHistory (UserID, BMIDegeri, Kategori)
            VALUES (%s, %s, %s)
        """, (session['user_id'], bmi, category))
        conn.commit()
        
        return render_template('bmi.html', bmi=round(bmi, 2), category=category)
        
    finally:
        cursor.close()
        conn.close()

def generate_recommendations(user_data):
    recommendations = []
    
    # Su tüketimi önerileri
    if user_data['health_data']['su_tuketimi'] < 2000:
        recommendations.append(
            f"Günlük su tüketiminiz {user_data['health_data']['su_tuketimi']}ml. "
            "Sağlıklı bir yaşam için günde en az 2000ml su içmeyi hedefleyin."
        )
    
    # Uyku önerileri
    if user_data['health_data']['uyku_suresi'] < 7:
        recommendations.append(
            f"Son uyku süreniz {user_data['health_data']['uyku_suresi']} saat. "
            "Yetişkinler için önerilen günlük uyku süresi 7-9 saattir."
        )
    
    # Adım sayısı önerileri
    if user_data['health_data']['adim_sayisi'] < 10000:
        recommendations.append(
            f"Günlük {user_data['health_data']['adim_sayisi']} adım attınız. "
            "Sağlıklı bir yaşam için günde 10.000 adım hedefine ulaşmaya çalışın."
        )
    
    # Ruh hali önerileri
    if user_data['health_data']['ruh_hali'] in ['kötü', 'çok_kötü']:
        recommendations.append(
            "Ruh halinizi iyileştirmek için egzersiz yapabilir, "
            "sevdiğiniz bir aktiviteyle ilgilenebilir veya bir uzmana danışabilirsiniz."
        )
    
    # Eğer hiç öneri yoksa
    if not recommendations:
        recommendations.append("Tebrikler! Sağlık hedeflerinize uygun ilerliyorsunuz.")
    
    return recommendations

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True) 