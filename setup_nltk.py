import nltk

def setup():
    print("Downloading required NLTK datasets...")
    try:
        nltk.download('stopwords')
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        print("\nAll NLTK datasets downloaded successfully!")
    except Exception as e:
        print(f"\nError downloading NLTK datasets: {e}")

if __name__ == "__main__":
    setup()
