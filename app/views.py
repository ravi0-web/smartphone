from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from fuzzywuzzy import fuzz
from .models import ContactMessage, Smartphone


def home(request):
    if request.user.is_anonymous:
        return redirect('login_')
    latest_phones = Smartphone.objects.filter(is_latest=True)[:8]
    best_sellers = Smartphone.objects.filter(is_best_seller=True)[:8]
    return render(request, 'main.html', {
        'latest_phones': latest_phones,
        'best_sellers': best_sellers,
    })


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


def login_(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
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
            # Get form inputs
            brand = request.POST.get('brand', '').strip().lower()

            max_price_val = request.POST.get('max_price')
            max_price = float(max_price_val) if max_price_val else 999999

            min_ram_val = request.POST.get('min_ram')
            min_ram = float(min_ram_val) if min_ram_val else 0

            min_storage_val = request.POST.get('min_storage')
            min_storage = float(min_storage_val) if min_storage_val else 0

            # Get all phones from database
            phones = Smartphone.objects.all()

            # Apply brand filter
            if brand and brand != "any":
                phones = phones.filter(name__icontains=brand)

            # Convert to list and apply numeric filters + scoring
            phone_list = []
            for phone in phones:
                ram_gb = phone.ram_gb
                storage_gb = phone.storage_gb
                price_inr = phone.price_inr

                if price_inr > max_price:
                    continue
                if ram_gb < min_ram:
                    continue
                if storage_gb < min_storage:
                    continue

                # Scoring logic
                score = (2 * ram_gb) + (1.5 * storage_gb) - (0.02 * price_inr)

                phone_list.append({
                    'name': phone.name,
                    'model': phone.model,
                    'storage': phone.storage,
                    'ram': phone.ram,
                    'price': phone.price,
                    'img_url': phone.img_url,
                    'Score': round(score, 2),
                    'Price_INR': price_inr,
                    'RAM_GB': ram_gb,
                    'Storage_GB': storage_gb,
                    'slug': phone.slug,
                })

            # Save to session for sorting
            request.session['filtered_phones'] = phone_list

            # Default sort by score
            phone_list.sort(key=lambda x: x['Score'], reverse=True)
            recommendations = phone_list[:6]

        except Exception as e:
            error = f"Error: {str(e)}"

    elif request.method == 'GET' and 'filtered_phones' in request.session:
        sort_by = request.GET.get('sort_by', '')
        phone_list = request.session['filtered_phones']

        if sort_by == 'name':
            phone_list.sort(key=lambda x: x.get('name', ''))
        elif sort_by == 'price_asc':
            phone_list.sort(key=lambda x: x.get('Price_INR', 0))
        elif sort_by == 'price_desc':
            phone_list.sort(key=lambda x: x.get('Price_INR', 0), reverse=True)
        else:
            phone_list.sort(key=lambda x: x.get('Score', 0), reverse=True)

        recommendations = phone_list[:6]

    latest_phones = Smartphone.objects.filter(is_latest=True)[:8]
    best_sellers = Smartphone.objects.filter(is_best_seller=True)[:8]

    return render(request, 'main.html', {
        'recommendations': recommendations,
        'error': error,
        'latest_phones': latest_phones,
        'best_sellers': best_sellers,
    })


def phone_detail_view(request, model_slug):
    phone = get_object_or_404(Smartphone, slug=model_slug)
    # Convert to dict for template compatibility
    phone_dict = {
        'name': phone.name,
        'model': phone.model,
        'storage': phone.storage,
        'ram': phone.ram,
        'primary_camera': phone.primary_camera,
        'secondary_camera': phone.secondary_camera,
        'colors': phone.colors,
        'processor': phone.processor,
        'GPU': phone.gpu,
        'OS': phone.os,
        'display_resolution': phone.display_resolution,
        'memory': phone.memory,
        'loud_speaker': phone.loud_speaker,
        'sensors': phone.sensors,
        'battery': phone.battery,
        'price': phone.price,
        'img_url': phone.img_url,
    }
    return render(request, 'phone_detail.html', {'phone': phone_dict})


def search_suggestions(request):
    query = request.GET.get('q', '').lower()
    suggestions = []
    if query:
        phones = Smartphone.objects.all()
        scored = []
        for phone in phones:
            score = fuzz.partial_ratio(phone.full_name, query)
            scored.append((score, phone.model))
        scored.sort(key=lambda x: x[0], reverse=True)
        suggestions = [item[1] for item in scored[:5]]
    return JsonResponse(suggestions, safe=False)


def search_results(request):
    query = request.GET.get('q', '').lower()
    results = []
    if query:
        phones = Smartphone.objects.all()
        scored = []
        for phone in phones:
            score = fuzz.partial_ratio(phone.full_name, query)
            if phone.slug:
                scored.append((score, phone))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for _, phone in scored[:10]:
            results.append({
                'name': phone.name,
                'model': phone.model,
                'price': phone.price,
                'img_url': phone.img_url,
                'model_slug': phone.slug,
            })
    return render(request, 'search_results.html', {'query': query, 'results': results})


def compare(request):
    comparison = {}
    if request.method == 'POST':
        phone1_query = request.POST.get('phone1', '').lower().strip()
        phone2_query = request.POST.get('phone2', '').lower().strip()

        # Fuzzy match phone 1
        phone1 = _find_best_match(phone1_query)
        phone2 = _find_best_match(phone2_query)

        if phone1 and phone2:
            comparison = {
                'phone1': {
                    'img_url': phone1.img_url,
                    'name': f"{phone1.name} {phone1.model}",
                    'ram': phone1.ram,
                    'storage': phone1.storage,
                    'battery': phone1.battery,
                    'camera': phone1.primary_camera,
                    'processor': phone1.processor,
                },
                'phone2': {
                    'img_url': phone2.img_url,
                    'name': f"{phone2.name} {phone2.model}",
                    'ram': phone2.ram,
                    'storage': phone2.storage,
                    'battery': phone2.battery,
                    'camera': phone2.primary_camera,
                    'processor': phone2.processor,
                },
                'better': _decide_better(phone1, phone2)
            }
        else:
            comparison['error'] = "One or both smartphones not found!"

    return render(request, 'compare.html', {'comparison': comparison})


def _find_best_match(query):
    """Find the best matching phone using fuzzy search."""
    phones = Smartphone.objects.all()
    best_score = 0
    best_phone = None
    for phone in phones:
        score = fuzz.partial_ratio(phone.full_name, query)
        if score > best_score:
            best_score = score
            best_phone = phone
    return best_phone if best_score > 50 else None


def _decide_better(phone1, phone2):
    def safe_float(val):
        try:
            return float(str(val).split()[0])
        except:
            return 0

    score1 = safe_float(phone1.ram) + safe_float(phone1.storage) + safe_float(phone1.battery) + safe_float(phone1.primary_camera)
    score2 = safe_float(phone2.ram) + safe_float(phone2.storage) + safe_float(phone2.battery) + safe_float(phone2.primary_camera)

    if score1 > score2:
        return f"{phone1.name} {phone1.model}"
    elif score2 > score1:
        return f"{phone2.name} {phone2.model}"
    else:
        return "Both are equally good"


def search_phones(request):
    query = request.GET.get('term', '').lower()
    phones = Smartphone.objects.all()
    matches = []
    for phone in phones:
        if query in phone.full_name:
            matches.append(phone.full_name)
            if len(matches) >= 10:
                break
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
