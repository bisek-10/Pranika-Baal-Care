from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_mail import Mail, Message
import os
import time
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pediatric_physio_nepal')

app.config['GOOGLE_PLACES_API_KEY'] = os.environ.get('GOOGLE_PLACES_API_KEY')
app.config['GOOGLE_PLACE_ID'] = os.environ.get(
    'GOOGLE_PLACE_ID',
    'ChIJKxm9XgD7lDkRziRwynuZFPo'
)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'prakash.shrestha986914@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') 

mail = Mail(app)

_google_reviews_cache = {
    'timestamp': 0,
    'data': None
}


def _build_star_icons(rating):
    rounded = round(rating * 2) / 2
    stars = []

    for index in range(1, 6):
        if rounded >= index:
            stars.append('fas fa-star')
        elif rounded >= index - 0.5:
            stars.append('fas fa-star-half-alt')
        else:
            stars.append('far fa-star')

    return stars


def _get_google_reviews():
    cache_ttl = 30 * 60
    now = time.time()
    cached = _google_reviews_cache.get('data')

    if cached and now - _google_reviews_cache['timestamp'] < cache_ttl:
        return cached

    api_key = app.config.get('GOOGLE_PLACES_API_KEY')
    place_id = app.config.get('GOOGLE_PLACE_ID')

    if not api_key or not place_id:
        return cached

    try:
        response = requests.get(
            'https://maps.googleapis.com/maps/api/place/details/json',
            params={
                'place_id': place_id,
                'fields': 'rating,user_ratings_total',
                'key': api_key
            },
            timeout=5
        )
        response.raise_for_status()
    except requests.RequestException:
        return cached

    payload = response.json()
    if payload.get('status') != 'OK':
        return cached

    result = payload.get('result', {})
    rating = result.get('rating')
    total = result.get('user_ratings_total')

    if rating is None or total is None:
        return cached

    data = {
        'rating': f"{rating:.1f}",
        'total': total,
        'stars': _build_star_icons(rating)
    }

    _google_reviews_cache['timestamp'] = now
    _google_reviews_cache['data'] = data

    return data


@app.context_processor
def inject_google_reviews():
    return {
        'google_reviews': _get_google_reviews()
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        msg = Message(subject=f"New Website Inquiry from {name}",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=['prakash.shrestha986914@gmail.com'])
        msg.body = f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}"
        
        try:
            val = app.config['MAIL_PASSWORD']
            if not val:
                raise Exception("Mail password is not set in environment variables")
            
            mail.send(msg)
            flash('Your message has been sent successfully!', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
        
        return redirect(url_for('contact'))
        
    return render_template('contact.html')


@app.route('/debug/google-reviews')
def debug_google_reviews():
    api_key = app.config.get('GOOGLE_PLACES_API_KEY')
    place_id = app.config.get('GOOGLE_PLACE_ID')

    if not api_key or not place_id:
        return jsonify({
            'ok': False,
            'error': 'Missing GOOGLE_PLACES_API_KEY or GOOGLE_PLACE_ID'
        })

    try:
        response = requests.get(
            'https://maps.googleapis.com/maps/api/place/details/json',
            params={
                'place_id': place_id,
                'fields': 'rating,user_ratings_total',
                'key': api_key
            },
            timeout=5
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return jsonify({
            'ok': False,
            'error': str(exc)
        })

    payload = response.json()
    return jsonify({
        'ok': payload.get('status') == 'OK',
        'status': payload.get('status'),
        'error_message': payload.get('error_message'),
        'result': payload.get('result', {})
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)