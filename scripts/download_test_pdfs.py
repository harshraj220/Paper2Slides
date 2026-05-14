import os
import requests
import xml.etree.ElementTree as ET
import time

def download_test_pdfs(download_dir="test_pdfs", num_papers=30):
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        
    print(f"Fetching {num_papers} machine learning papers from arXiv...")
    
    # Query arXiv for recent machine learning papers
    url = f'http://export.arxiv.org/api/query?search_query=cat:cs.CL+OR+cat:cs.CV&sortBy=submittedDate&sortOrder=descending&max_results={num_papers}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch from arXiv API: {e}")
        return

    root = ET.fromstring(response.content)
    
    # arXiv XML namespace
    ns = {'arxiv': 'http://www.w3.org/2005/Atom'}
    
    downloaded = 0
    for entry in root.findall('arxiv:entry', ns):
        if downloaded >= num_papers:
            break
            
        title = entry.find('arxiv:title', ns).text.strip().replace('\n', ' ')
        # Clean title for filename
        safe_title = "".join([c if c.isalnum() else "_" for c in title])
        safe_title = " ".join(safe_title.split("_"))[:50].replace(" ", "_") + ".pdf"
        
        pdf_link = None
        for link in entry.findall('arxiv:link', ns):
            if link.attrib.get('title') == 'pdf':
                pdf_link = link.attrib.get('href')
                break
                
        if pdf_link:
            filepath = os.path.join(download_dir, safe_title)
            if not os.path.exists(filepath):
                print(f"[{downloaded+1}/{num_papers}] Downloading: {safe_title}")
                try:
                    pdf_resp = requests.get(pdf_link, stream=True, timeout=15)
                    with open(filepath, 'wb') as f:
                        for chunk in pdf_resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    downloaded += 1
                    time.sleep(1) # Be polite to arXiv servers
                except Exception as e:
                    print(f"Failed to download {safe_title}: {e}")
            else:
                print(f"[{downloaded+1}/{num_papers}] Already exists: {safe_title}")
                downloaded += 1

    print(f"\nSuccessfully downloaded {downloaded} test PDFs into '{download_dir}'!")

if __name__ == "__main__":
    download_test_pdfs()
