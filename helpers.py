from io import BytesIO
from PIL import Image
import os
import re
from base64 import b64decode, b64encode
import zipfile
import re
import xml.etree.ElementTree as ET

def unzip_idml(idml_file):
    try:
        # Create a directory to extract the contents
        extract_dir = os.path.splitext(idml_file)[0]
        os.makedirs(extract_dir, exist_ok=True)
        
        # Unzip the IDML file
        with zipfile.ZipFile(idml_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    except Exception:
        pass
    
    return extract_dir

def extract_cdata_values(template):
    spreads_folder = 'uploads/uploaded_template/Spreads'
    cdata_values = []

    # Regular expression to find content inside [CDATA[xxx]]
    cdata_pattern = re.compile(r'\[CDATA\[(.*?)\]\]', re.DOTALL)

    # Check each XML file in the Spreads folder
    for filename in os.listdir(spreads_folder):
        try:
            if filename.endswith('.xml'):
                xml_path = os.path.join(spreads_folder, filename)
                with open(xml_path, 'r', encoding='utf-8') as xml_file:
                    xml_content = xml_file.read()
                    # Find all occurrences of [CDATA[xxx]]
                    matches = cdata_pattern.findall(xml_content)
                    # Add found values to the list
                    cdata_values.extend(matches)
        except Exception as e:
            pass
    
    return cdata_values

def sanitize_base64_string(b64_string):
    # Define the valid characters for Base64
    base64_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
    
    # Remove any characters that are not valid Base64 characters
    sanitized_string = ''.join(c for c in b64_string if c in base64_chars)
    
    return sanitized_string

def decode_base64_to_jpg(b64_string, output_directory, file_index):
    try:
        # Sanitize the Base64 string
        sanitized_string = sanitize_base64_string(b64_string)
        
        # Decode the Base64 string, making sure that it contains only valid characters
        file_bytes = b64decode(sanitized_string, validate=True)
        
        # Create a BytesIO object to handle the image data
        image_stream = BytesIO(file_bytes)

        # Open the image using Pillow (PIL)
        image = Image.open(image_stream)

        # Convert the image to RGB mode if it is in RGBA mode
        if image.mode == 'RGBA':
            image = image.convert('RGB')

        # Define the output file path with a unique index
        output_file = os.path.join(output_directory, f'file_{file_index}.jpg')

        # Save the image as JPG
        image.save(output_file, format='JPEG')
        
        print(f'File saved as {output_file}')

        return True

    except Exception as e:
        pass

def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            # Read the image file as binary data
            image_binary = image_file.read()
            # Encode the binary data into Base64 string
            base64_encoded = b64encode(image_binary).decode('utf-8')
            return base64_encoded
    except IOError as e:
        print(f"Error reading the image file: {e}")
        return None


def update_xml_with_base64(spreads_folder, base64_encoded, value):
    try:
        for filename in os.listdir(spreads_folder):
            try:
                if filename.endswith('.xml'):
                    xml_path = os.path.join(spreads_folder, filename)
                    tree = ET.parse(xml_path)
                    root = tree.getroot()

                    # Function to recursively search and replace 'value' with 'base64_encoded'
                    def replace_value(element):
                        if element.text and value in element.text:
                            element.text = element.text.replace(value, base64_encoded)
                        for child in element:
                            replace_value(child)

                    # Start replacement from the root element
                    replace_value(root)

                    # Write the updated XML content back to the original file
                    tree.write(xml_path, encoding='utf-8')

                    print(f"Updated XML file: {xml_path}")

            except Exception as e:
                print(f"Error updating XML file {filename}: {e}")

        return True

    except Exception as e:
        print(f"Error updating XML files: {e}")
        return False

def zip_idml(idml_dir, output_idml_file):
    try:
        with zipfile.ZipFile(output_idml_file, 'w') as zip_ref:
            # Iterate over all files and add them to the zip file
            for root, _, files in os.walk(idml_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_ref.write(file_path, os.path.relpath(file_path, idml_dir))
        
        print(f"IDML file saved: {output_idml_file}")
        return True

    except Exception as e:
        print(f"Error zipping IDML file: {e}")
        return False