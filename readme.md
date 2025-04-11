# Visual Search App with PyQt5

This application allows you to perform visual product searches using the Inditex API and the imgBB service for uploading images. The graphical interface is built with PyQt5.

## Features

- **Image Upload:** Allows you to select a local image and upload it to imgBB.
- **OAuth2 Authentication:** Obtains an Inditex token using OAuth credentials.
- **Visual Search:** Performs a visual search using the Inditex API and displays the results.
- **Graphical User Interface:** Simple and functional interface built with PyQt5.

## Requirements

- **Python 3.x**
- **PyQt5:** `pip install PyQt5`
- **requests:** `pip install requests`
- **PyYAML:** `pip install pyyaml`
- **BeautifulSoup4:** `pip install beautifulsoup4`

> **Note:** It is recommended to create a virtual environment for this project.

## Project Structure
visual-search-app/
├── venv/                    # Virtual environment directory (optional, as per your preference)
├── config.yml               # Real configuration file with sensitive data (DO NOT upload this)
├── config.example.yml       # Example configuration file that shows what values to include
├── main.py                  # Main application source code file
└── README.md                # This file

## Configuration

The application uses a YAML configuration file to store the credentials needed for the APIs:

- **imgBB API:** Requires an `api_key` to upload images.
- **Inditex API:** Requires an `oauth_client_id` and an `oauth_client_secret` to obtain an OAuth2 token.

**Important:**
- The **config.yml** file contains sensitive information and is included in `.gitignore`, so it will not be uploaded to the repository.
- Instead, an example file **config.example.yml** is provided as a guideline.

### To set up the application:

1. Copy the example file and rename it to **config.yml**:
   ```bash
   cp config.example.yml config.yml

## Usage

Once the application is running, follow these steps:

1. **Select an Image:**  
   Click the **"Select image and search"** button. A file dialog will appear for you to choose an image from your local machine.

2. **Image Preview:**  
   After selecting an image, a preview will be displayed in the application's GUI.

3. **Upload and Search:**  
   - The application uploads the image to imgBB and retrieves the public URL.
   - Then it uses your Inditex credentials (specified in **config.yml**) to obtain an OAuth2 token.
   - Next, it performs a visual search using the Inditex API.

4. **View Results:**  
   The application processes the API response and displays the search results (such as product details and thumbnails) directly in the interface.  
   Click any links provided in the results to get more details.

5. **Error Handling:**  
   If an error occurs during any step (image upload, token retrieval, or visual search), an error message will be displayed on-screen and printed to the console for troubleshooting.