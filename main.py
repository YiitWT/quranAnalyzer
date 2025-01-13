import requests
import pandas as pd
from flask import Flask, request, jsonify
from threading import Thread
import time
import re
import unicodedata
from flask_cors import CORS

def normalize_arabic_text(text):
    """
    Normalize Arabic text by:
    1. Removing diacritics (tashkeel)
    2. Normalizing different forms of Alef and Hamza
    3. Removing tatweel (stretching character)
    """
    if not isinstance(text, str):
        return text
        
    # Remove tashkeel (diacritics)
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    
    # Normalize alef variants
    text = re.sub('[إأٱآا]', 'ا', text)
    
    # Normalize hamza variants
    text = re.sub('ؤ', 'و', text)
    text = re.sub('ئ', 'ي', text)
    
    # Remove tatweel (stretching character)
    text = re.sub('ـ', '', text)
    
    return text

def fetch_quran_verses():
    """Fetch verses from Quran.com API with proper error handling and rate limiting"""
    base_url = "https://api.quran.com/api/v4"
    verses_data = []
    
    try:
        response = requests.get(f"{base_url}/chapters")
        chapters = response.json()['chapters']
    except Exception as e:
        print(f"Error fetching chapters: {e}")
        return []

    for chapter in chapters:
        chapter_id = chapter['id']
        try:
            time.sleep(0.001)
            
            response = requests.get(
                f"{base_url}/verses/by_chapter/{chapter_id}",
                params={
                    "language": "tr",
                    "translations": "77",
                    "fields": "text_uthmani,verse_key,verse_number"
                }
            )
            
            chapter_verses = response.json()['verses']
            
            for verse in chapter_verses:
                # Normalize Arabic text before storing
                arabic_text = normalize_arabic_text(verse['text_uthmani'])
                
                verses_data.append({
                    'chapter_id': chapter_id,
                    'verse_number': verse['verse_number'],
                    'verse_key': verse['verse_key'],
                    'arabic_text': arabic_text,
                    'arabic_text_raw': verse['text_uthmani'],  # Keep original text too
                    'turkish_text': verse['translations'][0]['text'] if verse.get('translations') else '',
                })
                
        except Exception as e:
            print(f"Error fetching chapter {chapter_id}: {e}")
            continue
            
    return verses_data

def create_quran_dataset():
    if(pd.io.common.file_exists('quran_dataset.csv')):
        return pd.read_csv('quran_dataset.csv', encoding='utf-8')
    """Create and save the Quran dataset"""
    print("Fetching Quran verses...")
    verses = fetch_quran_verses()
    
    if not verses:
        print("Error: No verses were fetched!")
        return None
        
    df = pd.DataFrame(verses)
    df.to_csv('quran_dataset.csv', index=False, encoding='utf-8')
    print("Dataset saved to quran_dataset.csv")
    return df

app = Flask(__name__)
CORS(app)

def load_dataset():
    try:
        return pd.read_csv('quran_dataset.csv', encoding='utf-8')
    except FileNotFoundError:
        print("Dataset not found, creating new one...")
        return create_quran_dataset()

@app.route('/search', methods=['GET'])
def search():
    word = request.args.get('word', '').strip()
    language = request.args.get('language', 'turkish').lower()
    stripSpaces = request.args.get('stripSpaces', 'true').lower()
    
    if not word:
        return jsonify({"error": "Please provide a word to search"}), 400
        
    df = load_dataset()
    if df is None:
        return jsonify({"error": "Dataset not available"}), 500
    
    if language == 'arabic':
        # Normalize the search word
        word = normalize_arabic_text(word) 
        # Search in normalized Arabic text
        matches = df[df['arabic_text'].str.contains(word, case=False, na=False)]
        # Use raw Arabic text for display
        text_column = 'arabic_text_raw'
    else:
        # For Turkish, search as before
        text_column = 'turkish_text'
        if stripSpaces == 'false':
            word = f' {word} '
        matches = df[df[text_column].str.contains(word, case=False, na=False)]
    
    # Aynı chapter_id ve verse_number kombinasyonuna sahip kayıtları tekilleştir
    matches = matches.drop_duplicates(subset=['chapter_id', 'verse_number'])
    
    results = []
    total_word_count = 0  # Toplam kelime sayısını tutacak değişken
    
    for _, verse in matches.iterrows():
        # Kelimenin ayette kaç kez geçtiğini say
        if language == 'arabic':
            word_count = verse['arabic_text'].count(word)
        else:
            word_count = verse['turkish_text'].lower().count(word.lower())
        
        total_word_count += word_count  # Toplam kelime sayısını güncelle
        
        results.append({
            'chapter': int(verse['chapter_id']),
            'verse': int(verse['verse_number']),
            'verse_key': verse['verse_key'],
            'text': verse[text_column],
            'translation': verse['turkish_text'] if language == 'arabic' else None,
            'word_count': word_count  # Ayetteki kelime sayısını ekle
        })
    
    return jsonify({
        'word': word,
        'total_occurrences': len(results),  # Eşleşen ayet sayısı
        'total_word_count': total_word_count,  # Toplam kelime sayısı
        'verses': results
    })

if __name__ == '__main__':
    if not pd.io.common.file_exists('quran_dataset.csv'):
        create_quran_dataset()
    app.run(host='0.0.0.0', port=5000, debug=False)