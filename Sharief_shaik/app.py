from flask import Flask, request, render_template, redirect, url_for, flash, session
import pandas as pd
import random
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from rapidfuzz import process, fuzz
from datetime import datetime
import numpy as np
import re
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load files
trending_products = pd.read_csv("models/trending_products.csv").head(100)
random_prices = [random.randint(300, 1000) for _ in range(len(trending_products))]
train_data = pd.read_csv("models/clean_data.csv")

# Database configuration
app.secret_key = "alskdjfwoeieiurlskdjfslkdjf"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Sharief%407@localhost/ecom'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100))
    price = db.Column(db.Integer)
    image_url = db.Column(db.String(500))

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100))
    price = db.Column(db.Integer)
    image_url = db.Column(db.String(500))

# Utility Functions
def truncate(text, length):
    return text[:length] + "..." if len(text) > length else text

def is_in_wishlist(product_name):
    """Check if a product is in the user's wishlist"""
    if 'wishlist' not in session:
        return False
    return any(item['product_name'] == product_name for item in session['wishlist'])

def is_in_cart(product_name):
    """Check if a product is in the user's cart"""
    return Cart.query.filter_by(product_name=product_name).first() is not None




from rapidfuzz import process, fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

def content_based_recommendations(train_data, item_name, top_n=10):
    # Step 1: Exact match
    if item_name in train_data['Name'].values:
        matched_name = item_name
    else:
        # Step 2: Fuzzy match (strict, 80+)
        match = process.extractOne(item_name, train_data['Name'], scorer=fuzz.WRatio)
        if match and match[1] > 80:  # strict match
            matched_name = match[0]
        else:
            # Step 3: Tag-based match
            tag_matches = train_data[train_data['Tags'].str.contains(item_name, case=False, na=False)]
            if not tag_matches.empty:
                matched_name = tag_matches.iloc[0]['Name']
            else:
                # Step 4: Fuzzy match (loose, 60+)
                match = process.extractOne(item_name, train_data['Name'], scorer=fuzz.WRatio)
                if match and match[1] >= 60:
                    matched_name = match[0]
                else:
                    return pd.DataFrame()  # No match at all

    # Step 5: TF-IDF on Tags
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(train_data['Tags'].fillna(''))
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    item_index = train_data[train_data['Name'] == matched_name].index[0]
    similar_items = list(enumerate(cosine_sim[item_index]))
    sorted_similar = sorted(similar_items, key=lambda x: x[1], reverse=True)[1:top_n+1]
    indices = [i[0] for i in sorted_similar]

    return train_data.iloc[indices][['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']]


# Price generator
random_image_urls = [
    "static/img/img_1.png", "static/img/img_2.png", "static/img/img_3.png",
    "static/img/img_4.png", "static/img/img_5.png", "static/img/img_6.png",
    "static/img/img_7.png", "static/img/img_8.png"
]
price_list = [150, 200, 400, 350, 100, 120, 500, 550, 300, 650]

def get_price_map(products):
    price_map = {}
    for i, name in enumerate(products['Name']):
        price_map[name] = price_list[i % len(price_list)]
    return price_map

# Routes
@app.route("/")
def index():
    product_images = [random.choice(random_image_urls) for _ in range(len(trending_products.head(11)))]
    price_map = get_price_map(trending_products.head(11))
    cart_items = Cart.query.all()
    cart_count = Cart.query.count()
    wishlist_count = len(session.get('wishlist', []))
    return render_template("index.html",
                           trending_products=trending_products.head(11),
                           truncate=truncate,
                           random_product_image_urls=product_images,
                           random_prices=[price_map[name] for name in trending_products.head(11)['Name']],
                           cart_items=cart_items,
                           cart_count=cart_count,
                           wishlist_count=wishlist_count,
                           is_in_wishlist=is_in_wishlist,
                           is_in_cart=is_in_cart)

@app.route("/main")
def main():
    cart_items = Cart.query.all()
    cart_count = Cart.query.count()
    wishlist_count = len(session.get('wishlist', []))
    return render_template("main.html",
                           cart_items=cart_items,
                           cart_count=cart_count,
                           wishlist_count=wishlist_count,
                           is_in_wishlist=is_in_wishlist,
                           is_in_cart=is_in_cart)

@app.route("/index")
def indexredirect():
    return redirect("/")



@app.route("/signup")
def signup_page():
    return render_template("signup.html")



@app.route("/signin")
def signin_page():
    return render_template("signin.html")



@app.route("/signup_submit", methods=['POST'])
def signup_submit():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    existing_user = Signup.query.filter_by(username=username).first()
    if existing_user:
        flash("Username already exists.", "danger")
        return redirect(url_for('signup_page'))
    new_user = Signup(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    session['username'] = username
    flash("Signed up successfully!", "success")
    return redirect(url_for('index'))



@app.route("/signin_submit", methods=['POST'])
def signin_submit():
    username = request.form['signinUsername']
    password = request.form['signinPassword']
    user = Signup.query.filter_by(username=username, password=password).first()
    if user:
        session['username'] = username
        flash("Signed in successfully!", "success")
        return redirect(url_for('index'))
    else:
        flash("Invalid credentials.", "danger")
        return redirect(url_for('signin_page'))



@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out successfully.', 'info')
    return redirect('/')




@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    product_name = request.form.get("product_name")
    brand = request.form.get("brand")
    price = request.form.get("price")
    image_url = request.form.get("image_url")

    # Check if product is already in cart
    existing_cart_item = Cart.query.filter_by(product_name=product_name).first()
    if existing_cart_item:
        flash("Product is already in your cart!", "info")
        return redirect(request.referrer or url_for("product_detail", product_name=product_name))

    # Remove from wishlist if it exists there
    if 'wishlist' in session:
        wishlist_item = next((item for item in session['wishlist'] 
                             if item['product_name'] == product_name), None)
        if wishlist_item:
            session['wishlist'].remove(wishlist_item)
            session.modified = True
            flash("Product moved from wishlist to cart!", "success")
        else:
            flash("Product added to cart!", "success")

    new_item = Cart(product_name=product_name, brand=brand, price=price, image_url=image_url)
    db.session.add(new_item)
    db.session.commit()

    # Redirect back to the product detail page
    return redirect(request.referrer or url_for("product_detail", product_name=product_name))





@app.route("/cart_count")
def cart_count_api():
    return {"count": Cart.query.count()}



@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    cart_id = request.form.get("cart_id")
    item = Cart.query.get(cart_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Product removed from your cart!", "info")
    
    # Redirect to the cart page itself
    return redirect(url_for("view_cart"))




@app.route("/buy_now", methods=["POST"])
def buy_now():
    cart_id = request.form.get("cart_id")
    item = Cart.query.get(cart_id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect("/cart")


@app.route("/clear_cart")
def clear_cart():
    db.session.query(Cart).delete()
    db.session.commit()
    return redirect("/index")


@app.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    product_name = request.form['product_name']
    brand = request.form['brand']
    price = request.form['price']
    image_url = request.form['image_url']
    
    # Initialize wishlist if it doesn't exist
    if 'wishlist' not in session:
        session['wishlist'] = []
    
    # Check if product is already in wishlist
    existing_item = next((item for item in session['wishlist'] 
                         if item['product_name'] == product_name), None)
    
    if existing_item:
        flash('Product is already in your wishlist!', 'info')
    else:
        # Remove from cart if it exists there
        cart_item = Cart.query.filter_by(product_name=product_name).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
            flash('Product moved from cart to wishlist!', 'success')
        else:
            flash('Product added to your wishlist!', 'success')
        
        wishlist_item = {
            'product_name': product_name,
            'brand': brand,
            'price': price,
            'image_url': image_url
        }
        session['wishlist'].append(wishlist_item)
        session.modified = True  # Ensure session is saved
    
    return redirect(request.referrer)

@app.route('/wishlist')
def view_wishlist():
    wishlist_items = session.get('wishlist', [])
    return render_template('wishlist.html', wishlist_items=wishlist_items)

@app.route('/remove_from_wishlist', methods=['POST'])
def remove_from_wishlist():
    product_name = request.form.get('product_name')
    
    if 'wishlist' in session:
        # Remove the specific product from wishlist
        session['wishlist'] = [item for item in session['wishlist'] 
                              if item['product_name'] != product_name]
        session.modified = True
        flash('Product removed from your wishlist!', 'info')
    
    return redirect(url_for('view_wishlist'))

@app.route('/clear_wishlist')
def clear_wishlist():
    if 'wishlist' in session:
        session.pop('wishlist')
        flash('Your wishlist has been cleared!', 'info')
    
    return redirect(url_for('view_wishlist'))


@app.route("/cart")
def view_cart():
    cart_items = Cart.query.all()
    cart_count = Cart.query.count()
    wishlist_count = len(session.get('wishlist', []))
    return render_template("cart.html", cart_items=cart_items, cart_count=cart_count, wishlist_count=wishlist_count)



@app.route("/recommendations", methods=["POST", "GET"])
def recommendations():
    if request.method == "POST":
        product_name = request.form.get("prod", "").strip()
        top_n = int(request.form.get("nbr", 10))

        if not product_name:
            return render_template("main.html", message="Please enter a product name.")

        recommended = content_based_recommendations(train_data, product_name, top_n=top_n)

        if recommended.empty:
            return render_template("main.html", message=f"No recommendations found for '{product_name}'.")
        else:
            price_map = get_price_map(recommended)
            return render_template(
                "main.html",
                content_based_rec=recommended,
                truncate=truncate,
                random_prices=[price_map[name] for name in recommended['Name']],
                is_in_wishlist=is_in_wishlist,
                is_in_cart=is_in_cart
            )
    else:
        return redirect(url_for('main'))


        

@app.route('/categories')
def categories():
    products = []
    for index, row in trending_products.iterrows():
        image = row['ImageURL'].split('|')[0].strip()
        products.append({
            'name': row['Name'],
            'brand': row['Brand'],
            'rating': row['Rating'],
            'image_url': image
        })
    return render_template('categories.html', 
                         products=products,
                         is_in_wishlist=is_in_wishlist,
                         is_in_cart=is_in_cart)





@app.route('/product/<product_name>')
def product_detail(product_name):
    product_row = trending_products[trending_products['Name'] == product_name].iloc[0]

    image = product_row['ImageURL'].split('|')[0].strip()
    
    # Get price from price map instead of CSV column
    price_map = get_price_map(trending_products)
    price = price_map.get(product_row['Name'], 'N/A')

    product_data = {
        'name': product_row['Name'],
        'brand': product_row['Brand'],
        'rating': product_row['Rating'],
        'description': product_row.get('Description', 'No description available.'),
        'price': price,
        'image_url': image
    }
    return render_template('product_detail.html', 
                         product=product_data,
                         is_in_wishlist=is_in_wishlist,
                         is_in_cart=is_in_cart)









@app.route('/deals')
def deals():
    deals_list = []
    for index, row in trending_products.sample(8).iterrows():
        image = row['ImageURL'].split('|')[0].strip()
        deals_list.append({
            'name': row['Name'],
            'brand': row['Brand'],
            'rating': row['Rating'],
            'image_url': image,
            'original_price': random.randint(700, 1200),
            'deal_price': random.randint(300, 699)
        })
    return render_template('deals.html', 
                         deals=deals_list,
                         is_in_wishlist=is_in_wishlist,
                         is_in_cart=is_in_cart)

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

if __name__ == "__main__":
    app.run(debug=True)
