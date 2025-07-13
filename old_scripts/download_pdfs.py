import os
import requests
from urllib.parse import urlparse

def download_pdfs(pdf_urls, save_dir):
    """
    Downloads a list of PDF files to a specified directory.

    Args:
        pdf_urls (list): A list of URLs pointing to PDF files.
        save_dir (str): The directory to save the downloaded PDFs.
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for pdf_url in pdf_urls:
        try:
            # Extract filename from URL
            parsed_url = urlparse(pdf_url)
            filename = os.path.basename(parsed_url.path)
            if not filename or not filename.lower().endswith('.pdf'):
                # Fallback if filename is not clear or not a PDF
                filename = f"downloaded_file_{abs(hash(pdf_url))}.pdf"

            pdf_path = os.path.join(save_dir, filename)

            print(f"Downloading {pdf_url} to {pdf_path}...")
            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()  # Raise an exception for bad status codes

            with open(pdf_path, 'wb') as pdf_file:
                for chunk in response.iter_content(chunk_size=8192):
                    pdf_file.write(chunk)
            print(f"Successfully downloaded {filename}")

        except requests.exceptions.RequestException as e:
            print(f"Error downloading {pdf_url}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for {pdf_url}: {e}")

if __name__ == '__main__':
    print("This script is designed to be called with a list of PDF URLs.")
    print("Please provide the PDF URLs to download.")
