from flask import Flask, render_template, send_file, request, redirect, url_for
from helpers import unzip_idml, extract_cdata_values, decode_base64_to_jpg, image_to_base64, update_xml_with_base64, zip_idml
from PIL import ImageFile
import pandas as pd
import csv
import os
import shutil
import codecs
import re

ImageFile.LOAD_TRUNCATED_IMAGES = True

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return redirect(url_for('upload_page'))

@app.route('/upload', methods=["GET", "POST"])
def upload_page():
    if request.method == "POST":        
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '' or not file.filename.endswith('.idml'):
            return redirect(request.url)
        
        filename = 'uploaded_template.idml'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        extract_dir = unzip_idml(file_path)

        replace_images = 'replace_images' in request.form

        if replace_images:
            return redirect(url_for('replace_page'))
        else:
            return redirect(url_for('download_page'))

    return render_template('upload.html')

@app.route('/replace', methods=["GET", "POST"])
def replace_page():
    if request.method == "POST":
        if 'image' not in request.files:
            return redirect(request.url)
        
        image = request.files['image']
        if image.filename == '':
            return redirect(request.url)
        
        replacement_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'replacement_image.jpg')
        image.save(replacement_image_path)

        idml_file = 'uploads/uploaded_template.idml'
        extract_dir = 'uploads/uploaded_template/'
        cdata_values = extract_cdata_values(extract_dir)

        output_directory = 'uploads/image_files'
        os.makedirs(output_directory, exist_ok=True)

        # Decode and save each Base64 string as a JPG file
        for idx, value in enumerate(cdata_values, start=1):
            success = decode_base64_to_jpg(value, output_directory, idx)
            if success:
                base64_encoded_image = image_to_base64(replacement_image_path)
                if base64_encoded_image:
                    update_xml_with_base64(os.path.join(extract_dir, 'Spreads'), base64_encoded_image, value)
        
        return redirect(url_for('download_page'))

    return render_template('replace.html')

@app.route('/download', methods=["GET", "POST"])
def download_page():
    idml_file = 'uploads/uploaded_template.idml'
    template = 'uploads/uploaded_template/'

    fields_found = set()
    stories_path = os.path.join(template, 'Stories')
    stories = os.listdir(stories_path)

    for entry in stories:
        with codecs.open(os.path.join(stories_path, entry), "r", encoding='utf-8') as fin:
            for line in fin:
                matches = re.findall(r'###(.*?)###', line)
                fields_found.update(matches)

    if request.method != "POST" and not fields_found:
        return render_template('download.html', fields=fields_found, error=True)

    if request.method == "POST":
        form_data = {field: request.form.get(field) for field in fields_found}

        entry = {field: form_data.get(field, "") for field in fields_found}
        df = pd.DataFrame.from_dict([entry])
        csv_file = 'entries.csv'
        df.to_csv(csv_file, index=False)

        output_filename_template = 'uploaded_template'

        try:
            with codecs.open(csv_file, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                header = next(reader)

                for row in reader:
                    filename = output_filename_template
                    for field in fields_found:
                        placeholder = f'###{field}###'
                        try:
                            filename = filename.replace(placeholder, row[header.index(field)])
                        except ValueError:
                            print(f"\nPlease check that {csv_file} is encoded using 'utf-8' or try using 'utf-8-sig'")
                            break

                    for entry in os.listdir(stories_path):
                        try:
                            tmp_file_path = os.path.join('uploads/', 'tmp.tmp')
                            with codecs.open(tmp_file_path, "w", encoding='utf-8') as fout:
                                with codecs.open(os.path.join(stories_path, entry), "r", encoding='utf-8') as fin:
                                    for line in fin:
                                        line2 = line
                                        for field in fields_found:
                                            line2 = line2.replace(f'###{field}###', row[header.index(field)])
                                        fout.write(line2)
                        except PermissionError:
                            break
                        shutil.move(tmp_file_path, os.path.join(stories_path, entry))

                    shutil.make_archive(filename, 'zip', template)
                    shutil.move(filename + '.zip', idml_file)
                    try:
                        return send_file('uploads/uploaded_template.idml', as_attachment=True, download_name='modified_template.idml')
                    finally:
                        #Clear Upload Directory:
                        #Commented out for this version, will delete for next version
                        '''for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                        except Exception as e:
                            print(f'Failed to delete {file_path}. Reason: {e}')'''
        finally:
            os.remove(csv_file)

    return render_template('download.html', fields=fields_found, error=False)

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
