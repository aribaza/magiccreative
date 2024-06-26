# Magic Creative
## Overview
Magic Creative allows you to create a populated IDML file from an IDML template by replacing text fields and images as specified.

## Instructions
1. Uploading Your Template
Ensure that text fields to be replaced are in the form ###text###.
For example, a field where a name should go should be pre-filled with ###name###.
2. Special Note
For templates with only image replacement, please add an "invisible" template text field.
Otherwise, you will be prompted to upload an appropriate IDML file.

## Application Routes
### 1. Index Route
Route: /
Description: Redirects to the upload page.
### 2. Upload Page
Route: /upload
Methods: GET, POST
Description: Handles the upload of the IDML template.
On GET: Renders the upload form.
On POST:
Clears the upload directory.
Checks if the uploaded file is a valid .idml file.
Saves the uploaded file.
Redirects to the appropriate page based on the form submission.
### 3. Replace Page
Route: /replace
Methods: GET, POST
Description: Handles the replacement of images in the IDML file.
On GET: Renders the image replacement form.
On POST:
Saves the uploaded image.
Processes the IDML file to replace images.
Redirects to the download page.
### 4. Download Page
Route: /download
Methods: GET, POST
Description: Handles the text replacement and file download.
On GET:
Scans the IDML template for text fields to be replaced.
Renders the form for text field replacement.
On POST:
Processes the form data to replace text fields in the IDML file.
Generates and downloads the populated IDML file.
