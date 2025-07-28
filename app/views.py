from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
import pandas as pd
from fuzzywuzzy import fuzz
from .models import ContactMessage
import os

# Load data once
df = pd.read_csv(os.path.join(settings.BASE_DIR, 'data/smartphones.csv'))
df.columns = df.columns.str.lower()
df['full_name'] = df['name'].str.lower().fillna('') + ' ' + df['model'].str.lower().fillna('')
df['slug'] = df['model'].str.lower().str.replace(' ', '-')
df['model_slug'] = df['slug'].str.replace(r'[^a-z0-9\-]', '', regex=True)


def home(request):
    if request.user.is_anonymous:
        return redirect('login_')
    return render(request, 'main.html')


def signup(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not password or not confirm_password:
            return render(request, 'signup.html', {'message': 'Password fields cannot be empty'})

        if password != confirm_password:
            return render(request, 'signup.html', {'message': 'Passwords do not match'})

        if User.objects.filter(username=email).exists():
            return render(request, 'signup.html', {'message': 'Email already registered'})

        user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
        user.save()

        return redirect('login_')
    return render(request, 'signup.html')


@csrf_exempt  # ✅ Remove this if CSRF token works
def login_(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            print("✅ Login successful for:", user.username)
            return redirect('home')
        else:
            print("❌ Invalid login attempt")
            return render(request, 'login.html', {'message': 'Invalid credentials'})
    return render(request, 'login.html')


def logoutuser(request):
    logout(request)
    return redirect('login_')


def recommend_phones(request):
    recommendations = None
    error = None

    if request.method == 'POST':
        try:
            brand = request.POST.get('brand', '').strip().lower()
            max_price = float(request.POST.get('max_price', 999999))
            min_ram = float(request.POST.get('min_ram', 0))
            min_storage = float(request.POST.get('min_storage', 0))

            df = pd.read_csv(os.path.join(settings.BASE_DIR, 'data/smartphones.csv'))
            df['ram'] = df['ram'].astype(str)
            df['storage'] = df['storage'].astype(str)
            df['price'] = df['price'].astype(str)
            df['RAM_GB'] = df['ram'].str.extract(r'(\d+)').astype(float)
            df['Storage_GB'] = df['storage'].str.extract(r'(\d+)').astype(float)
            df['Price_INR'] = df['price'].str.replace('₹', '', regex=False).str.replace(',', '', regex=False).astype(float)

            if brand and brand != "any":
                filtered = df[
                    (df['Price_INR'] <= max_price) &
                    (df['RAM_GB'] >= min_ram) &
                    (df['Storage_GB'] >= min_storage) &
                    (df['name'].str.lower().str.contains(brand))
                ].copy()
            else:
                filtered = df[
                    (df['Price_INR'] <= max_price) &
                    (df['RAM_GB'] >= min_ram) &
                    (df['Storage_GB'] >= min_storage)
                ].copy()

            def compute_score(row, alpha=2, beta=1.5, gamma=0.02):
                return (alpha * row['RAM_GB']) + (beta * row['Storage_GB']) - (gamma * row['Price_INR'])

            filtered['Score'] = filtered.apply(compute_score, axis=1)
            request.session['filtered_phones'] = filtered.to_dict('records')

            top_10 = filtered.sort_values(by='Score', ascending=False).head(6)
            recommendations = top_10.to_dict('records')

        except Exception as e:
            error = f"Error: {str(e)}"

    elif request.method == 'GET' and 'filtered_phones' in request.session:
        sort_by = request.GET.get('sort_by', '')
        filtered = pd.DataFrame(request.session['filtered_phones'])

        if sort_by == 'name':
            filtered = filtered.sort_values(by='name')
        elif sort_by == 'price_asc':
            filtered = filtered.sort_values(by='Price_INR')
        elif sort_by == 'price_desc':
            filtered = filtered.sort_values(by='Price_INR', ascending=False)
        else:
            filtered = filtered.sort_values(by='Score', ascending=False)

        recommendations = filtered.head(6).to_dict('records')

    return render(request, 'main.html', {
        'recommendations': recommendations,
        'error': error
    })


def phone_detail_view(request, model_slug):
    phone_data = df[df['model_slug'] == model_slug]
    if phone_data.empty:
        return render(request, 'error.html', {'error': 'Phone not found'})
    phone = phone_data.iloc[0].to_dict()
    return render(request, 'phone_detail.html', {'phone': phone})


def search_suggestions(request):
    query = request.GET.get('q', '').lower()
    suggestions = []
    if query:
        df['similarity'] = df['full_name'].apply(lambda x: fuzz.partial_ratio(x, query))
        matches = df.sort_values(by='similarity', ascending=False).head(5)
        suggestions = matches['model'].tolist()
    return JsonResponse(suggestions, safe=False)


def search_results(request):
    query = request.GET.get('q', '').lower()
    results = []
    if query:
        df['similarity'] = df['full_name'].apply(lambda x: fuzz.partial_ratio(x, query))
        matches = df.sort_values(by='similarity', ascending=False)
        valid_matches = matches[matches['model_slug'].notnull() & (matches['model_slug'] != '')]
        results = valid_matches.head(10).to_dict('records')
    return render(request, 'search_results.html', {'query': query, 'results': results})


def compare(request):
    comparison = {}
    if request.method == 'POST':
        phone1_query = request.POST.get('phone1', '').lower().strip()
        phone2_query = request.POST.get('phone2', '').lower().strip()

        phone1_data = df[df['full_name'].str.contains(phone1_query, na=False)].head(1)
        phone2_data = df[df['full_name'].str.contains(phone2_query, na=False)].head(1)

        if not phone1_data.empty and not phone2_data.empty:
            phone1 = phone1_data.iloc[0]
            phone2 = phone2_data.iloc[0]

            comparison = {
                'phone1': {
                    'img_url': phone1['img_url'],
                    'name': f"{phone1['name']} {phone1['model']}",
                    'ram': phone1['ram'],
                    'storage': phone1['storage'],
                    'battery': phone1['battery'],
                    'camera': phone1['primary_camera'],
                    'processor': phone1['processor']
                },
                'phone2': {
                    'img_url': phone2['img_url'],
                    'name': f"{phone2['name']} {phone2['model']}",
                    'ram': phone2['ram'],
                    'storage': phone2['storage'],
                    'battery': phone2['battery'],
                    'camera': phone2['primary_camera'],
                    'processor': phone2['processor']
                },
                'better': decide_better(phone1, phone2)
            }
        else:
            comparison['error'] = "One or both smartphones not found!"

    return render(request, 'compare.html', {'comparison': comparison})


def decide_better(phone1, phone2):
    def safe_float(val):
        try:
            return float(str(val).split()[0])
        except:
            return 0

    score1 = safe_float(phone1['ram']) + safe_float(phone1['storage']) + safe_float(phone1['battery']) + safe_float(phone1['primary_camera'])
    score2 = safe_float(phone2['ram']) + safe_float(phone2['storage']) + safe_float(phone2['battery']) + safe_float(phone2['primary_camera'])

    if score1 > score2:
        return f"{phone1['name']} {phone1['model']}"
    elif score2 > score1:
        return f"{phone2['name']} {phone2['model']}"
    else:
        return "Both are equally good"


def search_phones(request):
    query = request.GET.get('term', '').lower()
    matches = df[df['full_name'].str.contains(query, na=False)]['full_name'].head(10).tolist()
    return JsonResponse(matches, safe=False)


def contact_view(request):
    message = None
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        user_message = request.POST.get('message')

        contact = ContactMessage.objects.create(name=name, email=email, message=user_message)
        message = "Thank you for contacting us!"

    return render(request, 'contact.html', {'message': message})


def about_view(request):
    return render(request, 'about.html')
