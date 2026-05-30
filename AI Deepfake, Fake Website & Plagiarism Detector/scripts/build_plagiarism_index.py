import os
import joblib
from sentence_transformers import SentenceTransformer
import PyPDF2
import docx

def extract_text_from_file(file_path):
    ext = file_path.rsplit('.', 1)[1].lower()
    text = ""
    try:
        if ext == 'txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        elif ext == 'pdf':
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif ext == 'docx':
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
    return text

def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

def build_index():
    corpus_dir = 'data/plagiarism_corpus'
    output_path = 'weights/plagiarism_index.pkl'
    
    if not os.path.exists(corpus_dir):
        os.makedirs(corpus_dir)
        print(f"Created {corpus_dir}. Please place PDF/DOCX/TXT files here and rerun.")
        return
        
    files = [f for f in os.listdir(corpus_dir) if f.lower().endswith(('.txt', '.pdf', '.docx'))]
    
    if not files:
        print(f"No documents found in {corpus_dir}. Please add some reference documents.")
        return
        
    print(f"Found {len(files)} files in corpus. Loading model...")
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        print(f"Failed to load sentence-transformers model: {e}")
        return

    all_chunks = []
    all_sources = []
    
    for f in files:
        file_path = os.path.join(corpus_dir, f)
        print(f"Processing {f}...")
        text = extract_text_from_file(file_path)
        if text.strip():
            chunks = chunk_text(text)
            all_chunks.extend(chunks)
            all_sources.extend([f] * len(chunks))
            
    if not all_chunks:
        print("No valid text could be extracted from the corpus.")
        return
        
    print(f"Encoding {len(all_chunks)} text chunks...")
    embeddings = model.encode(all_chunks, convert_to_tensor=True)
    
    index_data = {
        'embeddings': embeddings,
        'chunks': all_chunks,
        'sources': all_sources
    }
    
    os.makedirs('weights', exist_ok=True)
    joblib.dump(index_data, output_path)
    
    print(f"Index built successfully and saved to {output_path}.")

if __name__ == "__main__":
    build_index()
