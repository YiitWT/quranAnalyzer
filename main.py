import requests
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from threading import Thread
import time
import re
import unicodedata
from flask_cors import CORS
import os
import json
from collections import defaultdict

class QuranAnalyzer:
    def __init__(self):
        self.arabic_normalizations = {
            # Different forms of Alef
            'ا': ['إ', 'أ', 'ٱ', 'آ'],
            # Different forms of Hamza
            'ء': ['ؤ', 'ئ', 'ٔ', 'ٕ'],
            # Yeh and Alef Maksura
            'ي': ['ى', 'ئ'],
            # Teh Marbuta and Heh
            'ة': ['ه'],
        }
        
    def normalize_arabic_text(self, text, for_search=False):
        """
        Enhanced Arabic text normalization with better handling of different cases
        """
        if not isinstance(text, str):
            return text
            
        # Remove diacritics (tashkeel) - these don't affect meaning
        text = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)
        
        # Remove tatweel (stretching character)
        text = re.sub(r'\u0640', '', text)
        
        if for_search:
            # More aggressive normalization for search
            # Normalize Alef variants
            text = re.sub(r'[إأٱآ]', 'ا', text)
            
            # Normalize Yeh variants
            text = re.sub(r'[ىئ]', 'ي', text)
            
            # Normalize Teh Marbuta and Heh
            text = re.sub(r'ة', 'ه', text)
            
            # Normalize Hamza variants
            text = re.sub(r'ؤ', 'و', text)
            text = re.sub(r'ئ', 'ي', text)
            
        return text.strip()

    def extract_arabic_words(self, text):
        """Extract individual Arabic words from text"""
        # Remove punctuation and split by spaces
        text = re.sub(r'[^\u0600-\u06FF\s]', ' ', text)
        words = [word.strip() for word in text.split() if word.strip()]
        return words

    def fetch_quran_verses(self):
        """Fetch verses from Quran.com API with enhanced error handling"""
        base_url = "https://api.quran.com/api/v4"
        verses_data = []
        
        print("Fetching Quran chapters...")
        try:
            response = requests.get(f"{base_url}/chapters", timeout=10)
            response.raise_for_status()
            chapters = response.json()['chapters']
            print(f"Found {len(chapters)} chapters")
        except Exception as e:
            print(f"Error fetching chapters: {e}")
            return []

        for i, chapter in enumerate(chapters, 1):
            chapter_id = chapter['id']
            chapter_name = chapter.get('name_simple', f'Chapter {chapter_id}')
            
            print(f"Fetching chapter {i}/{len(chapters)}: {chapter_name}")
            
            try:
                # Rate limiting
                time.sleep(0.1)
                
                response = requests.get(
                    f"{base_url}/verses/by_chapter/{chapter_id}",
                    params={
                        "language": "tr",
                        "translations": "77",  # Turkish translation
                        "fields": "text_uthmani,verse_key,verse_number"
                    },
                    timeout=10
                )
                response.raise_for_status()
                
                chapter_verses = response.json()['verses']
                
                for verse in chapter_verses:
                    arabic_text_raw = verse['text_uthmani']
                    arabic_text_normalized = self.normalize_arabic_text(arabic_text_raw)
                    arabic_text_search = self.normalize_arabic_text(arabic_text_raw, for_search=True)
                    
                    # Extract individual Arabic words
                    arabic_words = self.extract_arabic_words(arabic_text_search)
                    
                    verses_data.append({
                        'chapter_id': chapter_id,
                        'chapter_name': chapter_name,
                        'verse_number': verse['verse_number'],
                        'verse_key': verse['verse_key'],
                        'arabic_text_raw': arabic_text_raw,
                        'arabic_text_normalized': arabic_text_normalized,
                        'arabic_text_search': arabic_text_search,
                        'arabic_words': ' '.join(arabic_words),  # Space-separated words for search
                        'turkish_text': verse['translations'][0]['text'] if verse.get('translations') else '',
                    })
                    
            except Exception as e:
                print(f"Error fetching chapter {chapter_id}: {e}")
                continue
        
        print(f"Successfully fetched {len(verses_data)} verses")
        return verses_data

    def create_word_index(self, verses_data):
        """Create an index of Arabic words for faster searching"""
        word_index = defaultdict(list)
        
        for i, verse in enumerate(verses_data):
            words = verse['arabic_words'].split()
            for word in words:
                if len(word) > 1:  # Skip single characters
                    word_index[word].append(i)
        
        return dict(word_index)

def create_quran_dataset():
    """Create and save the enhanced Quran dataset"""
    analyzer = QuranAnalyzer()
    
    if os.path.exists('quran_dataset_enhanced.csv'):
        print("Enhanced dataset already exists, loading...")
        df = pd.read_csv('quran_dataset_enhanced.csv', encoding='utf-8')
        
        # Load word index if it exists
        word_index = {}
        if os.path.exists('word_index.json'):
            with open('word_index.json', 'r', encoding='utf-8') as f:
                word_index = json.load(f)
        
        return df, word_index
    
    print("Creating enhanced Quran dataset...")
    verses = analyzer.fetch_quran_verses()
    
    if not verses:
        print("Error: No verses were fetched!")
        return None, {}
        
    df = pd.DataFrame(verses)
    df.to_csv('quran_dataset_enhanced.csv', index=False, encoding='utf-8')
    
    # Create and save word index
    word_index = analyzer.create_word_index(verses)
    with open('word_index.json', 'w', encoding='utf-8') as f:
        json.dump(word_index, f, ensure_ascii=False, indent=2)
    
    print("Enhanced dataset and word index saved successfully")
    return df, word_index

app = Flask(__name__, static_folder='static')
CORS(app)
analyzer = QuranAnalyzer()

# Global variables to store dataset and word index
df_global = None
word_index_global = {}

def load_dataset():
    global df_global, word_index_global
    if df_global is None:
        try:
            df_global, word_index_global = create_quran_dataset()
        except Exception as e:
            print(f"Error loading dataset: {e}")
            return None, {}
    return df_global, word_index_global

@app.route('/', methods=['GET'])
def index():
    try:
        return send_from_directory('static', 'index.html')
    except FileNotFoundError:
        return jsonify({"error": "index.html not found"}), 404

@app.route('/search', methods=['GET'])
def search():
    word = request.args.get('word', '').strip()
    language = request.args.get('language', 'turkish').lower()
    exact_word = request.args.get('exactWord', 'false').lower() == 'true'
    
    if not word:
        return jsonify({"error": "Please provide a word to search"}), 400
        
    df, word_index = load_dataset()
    if df is None:
        return jsonify({"error": "Dataset not available"}), 500
    
    results = []
    total_word_count = 0
    
    if language == 'arabic':
        # Normalize the search word
        search_word = analyzer.normalize_arabic_text(word, for_search=True)
        
        if exact_word:
            # Exact word matching using word index
            if search_word in word_index:
                verse_indices = word_index[search_word]
                matches = df.iloc[verse_indices]
            else:
                matches = pd.DataFrame()  # Empty dataframe
        else:
            # Partial matching in normalized Arabic text
            matches = df[df['arabic_text_search'].str.contains(search_word, case=False, na=False)]
        
        # Count occurrences and prepare results
        for _, verse in matches.iterrows():
            if exact_word:
                # Count exact word occurrences
                verse_words = verse['arabic_words'].split()
                word_count = verse_words.count(search_word)
            else:
                # Count partial occurrences
                word_count = verse['arabic_text_search'].count(search_word)
            
            if word_count > 0:
                total_word_count += word_count
                results.append({
                    'chapter': int(verse['chapter_id']),
                    'chapter_name': verse['chapter_name'],
                    'verse': int(verse['verse_number']),
                    'verse_key': verse['verse_key'],
                    'text': verse['arabic_text_raw'],
                    'translation': verse['turkish_text'],
                    'word_count': word_count
                })
    
    else:  # Turkish search
        if exact_word:
            # Use word boundaries for exact Turkish word matching
            pattern = r'\b' + re.escape(word) + r'\b'
            matches = df[df['turkish_text'].str.contains(pattern, case=False, na=False, regex=True)]
        else:
            # Partial matching
            matches = df[df['turkish_text'].str.contains(word, case=False, na=False)]
        
        for _, verse in matches.iterrows():
            if exact_word:
                # Count exact word occurrences with word boundaries
                pattern = r'\b' + re.escape(word) + r'\b'
                word_count = len(re.findall(pattern, verse['turkish_text'], re.IGNORECASE))
            else:
                # Count all occurrences
                word_count = verse['turkish_text'].lower().count(word.lower())
            
            if word_count > 0:
                total_word_count += word_count
                results.append({
                    'chapter': int(verse['chapter_id']),
                    'chapter_name': verse['chapter_name'],
                    'verse': int(verse['verse_number']),
                    'verse_key': verse['verse_key'],
                    'text': verse['turkish_text'],
                    'translation': None,
                    'word_count': word_count
                })
    
    # Remove duplicates and sort by chapter and verse
    unique_results = []
    seen = set()
    for result in results:
        key = (result['chapter'], result['verse'])
        if key not in seen:
            seen.add(key)
            unique_results.append(result)
    
    unique_results.sort(key=lambda x: (x['chapter'], x['verse']))
    
    return jsonify({
        'word': word,
        'search_term': search_word if language == 'arabic' else word,
        'language': language,
        'exact_word': exact_word,
        'total_verses': len(unique_results),
        'total_word_count': total_word_count,
        'verses': unique_results
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get general statistics about the dataset"""
    df, word_index = load_dataset()
    if df is None:
        return jsonify({"error": "Dataset not available"}), 500
    
    stats = {
        'total_verses': len(df),
        'total_chapters': df['chapter_id'].nunique(),
        'total_arabic_words': len(word_index),
        'dataset_status': 'loaded'
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    print("Starting Quran Analyzer...")
    print("Loading dataset...")
    load_dataset()  # Pre-load the dataset
    print("Server ready!")
    app.run(host='0.0.0.0', port=5000, debug=False)