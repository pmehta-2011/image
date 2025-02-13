from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from flask_mail import Mail, Message
from googleapiclient.discovery import build
import requests
import os
import zipfile
import io
import shutil

app = Flask(__name__)
CORS(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 587 
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'pmsgenerator77@gmail.com' 
app.config['MAIL_PASSWORD'] = 'ffui imce pwrh kxdy' 
app.config['MAIL_DEFAULT_SENDER'] = 'pmsgenerator77@gmail.com' 
mail = Mail(app)

OUTPUT_DIR = os.path.join('static', 'dataset')
API_KEY = 'AIzaSyA7bL4n81IeKEk9S8Lkij4Vj_0UE9I_Gxo'
SEARCH_ENGINE_ID = '5311931a008df4ced'

def google_image_downloader(keyword, num_images, output_dir):
    service = build("customsearch", "v1", developerKey=API_KEY)
    results = service.cse().list(
        q=keyword,
        cx=SEARCH_ENGINE_ID,
        searchType="image",
        num=min(num_images, 10)  
    ).execute()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image_urls = [item['link'] for item in results.get('items', [])]

    for i, url in enumerate(image_urls):
        try:
            img_data = requests.get(url, timeout=10).content
            with open(os.path.join(output_dir, f"{keyword}_{i+1}.jpg"), 'wb') as img_file:
                img_file.write(img_data)
        except Exception as e:
            print(f"Error downloading {url}: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download_images', methods=['POST'])
def download_images():
    data = request.json
    keyword = data.get('keyword').strip()
    num_images = data.get('num_images', 10)
    email = data.get('email')

    output_path = os.path.join(OUTPUT_DIR, keyword)

    os.makedirs(output_path, exist_ok=True)

    try:
        google_image_downloader(keyword, num_images, output_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        try:
            for filename in os.listdir(output_path):
                file_path = os.path.join(output_path, filename)
                zip_file.write(file_path, filename)
        except FileNotFoundError as e:
            return jsonify({'error': f'Directory not found: {str(e)}'}), 500

    zip_buffer.seek(0)

    try:
        msg = Message(f'Your Downloaded Images: {keyword}', recipients=[email])
        msg.body = 'Attached is the zip file containing the downloaded images.'
        msg.attach(f'{keyword}_images.zip', 'application/zip', zip_buffer.getvalue())
        mail.send(msg)
        response_message = f'Zip file has been emailed to {email}'
    except Exception as e:
        return jsonify({'error': f'Error sending email: {str(e)}'}), 500

    zip_buffer.seek(0)

    shutil.rmtree(output_path)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{keyword}_images.zip'
    )

if __name__ == '__main__':
    app.run(debug=True)
