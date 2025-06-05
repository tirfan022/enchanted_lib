from flask import Flask, render_template, jsonify, request
import requests
import re 

app = Flask(__name__)

# Google Books API Base URL
GOOGLE_BOOKS_API_BASE_URL = "https://www.googleapis.com/books/v1/volumes"

@app.route('/')
def home():
    """Renders the main search page."""
    return render_template('index.html')

@app.route('/api/search_books')
def search_books():
    """
    Searches for books based on user query, mood, and choice using Google Books API.
    Returns a JSON response with book data.
    """
    query = request.args.get('query', '')
    mood = request.args.get('mood', '')
    choice = request.args.get('choice', '')

    search_terms = []
    if query:
        search_terms.append(query)
    if mood:
        search_terms.append(mood)
    if choice:
        search_terms.append(choice)

    if not search_terms:
        return jsonify({"message": "Please provide a query, mood, or choice to search."}), 400

    q_param = " ".join(search_terms)

    max_results = 20

    params = {
        "q": q_param,
        "maxResults": max_results
    }

    try:
        response = requests.get(GOOGLE_BOOKS_API_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        books_data = []
        if data.get('items'):
            for item in data['items']:
                volume_info = item.get('volumeInfo', {})
                
                # Extract description and clean HTML tags
                description = volume_info.get('description', 'No summary available.')
                description = re.sub(r'<[^>]+>', '', description) # regex to strip HTML tags

                books_data.append({
                    "id": item.get('id'),
                    "title": volume_info.get('title', 'N/A'),
                    "author": ", ".join(volume_info.get('authors', ['N/A'])),
                    "publishedDate": volume_info.get('publishedDate', 'N/A'),
                    "thumbnail": volume_info.get('imageLinks', {}).get('thumbnail'),
                    "description": description # Cleaned description 
                })
        else:
            return jsonify({"message": "No tales were found in this realm. Try another whisper of interest!"}), 200

        return jsonify({"books": books_data})

    except requests.exceptions.RequestException as e:
        # Handle network errors, connection refused, etc.
        return jsonify({"error": f"Error fetching data from Google Books API: {e}"}), 500
    except Exception as e:
        # Catch any other unexpected errors
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route('/book/<book_id>')
def book_detail(book_id):
    """
    Renders a detailed page for a specific book using its Google Books ID.
    Fetches comprehensive information from Google Books API.
    """
    try:
        # Fetch detailed information for the specific book ID
        response = requests.get(f"{GOOGLE_BOOKS_API_BASE_URL}/{book_id}")
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()

        volume_info = data.get('volumeInfo', {})
        book = {
            "title": volume_info.get('title', 'No Title Available'),
            "author": ", ".join(volume_info.get('authors', ['Unknown Author'])),
            "publishedDate": volume_info.get('publishedDate', 'N/A'),
            "thumbnail": volume_info.get('imageLinks', {}).get('thumbnail'),
            "description": volume_info.get('description', 'No detailed summary available.'),
            "pageCount": volume_info.get('pageCount', 'N/A'),
            "categories": ", ".join(volume_info.get('categories', ['N/A'])),
            "previewLink": volume_info.get('previewLink', '#')
        }
        
        # Clean up HTML tags from the full description
        book['description'] = re.sub(r'<[^>]+>', '', book['description'])

        return render_template('book_detail.html', book=book)

    except requests.exceptions.HTTPError as e:
        # Specific error handling for 404 (Not Found)
        if e.response.status_code == 404:
            return render_template('error.html', message="Book not found! The tale might be lost in the library's forgotten shelves."), 404
        else:
            return render_template('error.html', message=f"Error fetching book details: {e}. The magic ink is smeared!"), 500
    except requests.exceptions.RequestException as e:
        # Handle other request-related errors
        return render_template('error.html', message=f"A network spell has gone awry: {e}. Check your connection to the mystical realms."), 500
    except Exception as e:
        # Catch errors
        return render_template('error.html', message=f"An unexpected event disturbed the narrative: {e}. The story needs rewriting!"), 500

if __name__ == '__main__':
    app.run(debug=True)