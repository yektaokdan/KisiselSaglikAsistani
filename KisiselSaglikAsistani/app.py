from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'gizli_anahtar_123'  # Session için gerekli

# Dummy kullanıcı verileri
USERS = {}

# BMI kategorileri
BMI_CATEGORIES = {
    'zayif': {'min': 0, 'max': 18.5},
    'normal': {'min': 18.5, 'max': 24.9},
    'kilolu': {'min': 25, 'max': 29.9},
    'obez': {'min': 30, 'max': float('inf')}
}

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS:
            flash('Bu kullanıcı adı zaten kullanımda!')
            return redirect(url_for('register'))
        
        USERS[username] = {
            'password': password,
            'profile': {
                'boy': 0,
                'kilo': 0,
                'yas': 0,
                'cinsiyet': ''
            },
            'health_data': {
                'su_tuketimi': [],
                'uyku_suresi': [],
                'adim_sayisi': [],
                'ruh_hali': []
            }
        }
        flash('Kayıt başarılı! Giriş yapabilirsiniz.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        flash('Geçersiz kullanıcı adı veya şifre!')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_data = USERS[session['username']]
    recommendations = generate_recommendations(user_data)
    return render_template('dashboard.html', user=user_data, recommendations=recommendations)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        USERS[session['username']]['profile'] = {
            'boy': float(request.form['boy']),
            'kilo': float(request.form['kilo']),
            'yas': int(request.form['yas']),
            'cinsiyet': request.form['cinsiyet']
        }
        flash('Profil bilgileri güncellendi!')
        return redirect(url_for('dashboard'))
    
    return render_template('profile.html', user=USERS[session['username']])

@app.route('/calculate_bmi')
def calculate_bmi():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    profile = USERS[session['username']]['profile']
    
    # Profil bilgileri kontrolü
    if profile['boy'] == 0 or profile['kilo'] == 0:
        flash('Lütfen önce profil bilgilerinizi doldurun!')
        return redirect(url_for('profile'))
    
    boy_metre = profile['boy'] / 100
    bmi = profile['kilo'] / (boy_metre * boy_metre)
    
    category = None
    for cat, limits in BMI_CATEGORIES.items():
        if limits['min'] <= bmi <= limits['max']:
            category = cat
            break
    
    return render_template('bmi.html', bmi=round(bmi, 2), category=category)

@app.route('/daily_health', methods=['GET', 'POST'])
def daily_health():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        today = datetime.now().strftime('%Y-%m-%d')
        health_data = USERS[session['username']]['health_data']
        
        health_data['su_tuketimi'].append({
            'date': today,
            'value': int(request.form['su_tuketimi'])
        })
        health_data['uyku_suresi'].append({
            'date': today,
            'value': float(request.form['uyku_suresi'])
        })
        health_data['adim_sayisi'].append({
            'date': today,
            'value': int(request.form['adim_sayisi'])
        })
        health_data['ruh_hali'].append({
            'date': today,
            'value': request.form['ruh_hali']
        })
        
        flash('Günlük sağlık verileri kaydedildi!')
        return redirect(url_for('dashboard'))
    
    return render_template('daily_health.html')

@app.route('/recommendations')
def recommendations():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_data = USERS[session['username']]
    recommendations = generate_recommendations(user_data)
    return render_template('recommendations.html', recommendations=recommendations)

def generate_recommendations(user_data):
    recommendations = []
    
    # Su tüketimi önerileri
    if 'health_data' in user_data and 'su_tuketimi' in user_data['health_data'] and user_data['health_data']['su_tuketimi']:
        son_su_tuketimi = user_data['health_data']['su_tuketimi'][-1]['value']
        if son_su_tuketimi < 2000:
            recommendations.append(f"Günlük su tüketiminiz {son_su_tuketimi}ml. Sağlıklı bir yaşam için günde en az 2000ml su içmeyi hedefleyin.")
    
    # Uyku önerileri
    if 'health_data' in user_data and 'uyku_suresi' in user_data['health_data'] and user_data['health_data']['uyku_suresi']:
        son_uyku = user_data['health_data']['uyku_suresi'][-1]['value']
        if son_uyku < 7:
            recommendations.append(f"Son uyku süreniz {son_uyku} saat. Yetişkinler için önerilen günlük uyku süresi 7-9 saattir.")
    
    # Adım sayısı önerileri
    if 'health_data' in user_data and 'adim_sayisi' in user_data['health_data'] and user_data['health_data']['adim_sayisi']:
        son_adim = user_data['health_data']['adim_sayisi'][-1]['value']
        if son_adim < 10000:
            recommendations.append(f"Günlük {son_adim} adım attınız. Sağlıklı bir yaşam için günde 10.000 adım hedefine ulaşmaya çalışın.")
    
    # Ruh hali önerileri
    if 'health_data' in user_data and 'ruh_hali' in user_data['health_data'] and user_data['health_data']['ruh_hali']:
        son_ruh_hali = user_data['health_data']['ruh_hali'][-1]['value']
        if son_ruh_hali in ['kötü', 'çok_kötü']:
            recommendations.append("Ruh halinizi iyileştirmek için egzersiz yapabilir, sevdiğiniz bir aktiviteyle ilgilenebilir veya bir uzmana danışabilirsiniz.")
    
    # Eğer hiç öneri yoksa
    if not recommendations:
        recommendations.append("Tebrikler! Sağlık hedeflerinize uygun ilerliyorsunuz.")
    
    return recommendations

@app.route('/statistics')
def statistics():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_data = USERS[session['username']]['health_data']
    return render_template('statistics.html', data=user_data)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True) 