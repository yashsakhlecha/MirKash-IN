# Option 1: Use Online APIs (No model downloads)
import requests
import base64
from PIL import Image
import matplotlib.pyplot as plt

def analyze_with_online_apis(image_path):
    """Use online APIs - no model downloads needed"""
    
    # Method 1: Use Hugging Face Inference API (Free tier available)
    def hf_inference_api(image_path):
        """Use Hugging Face's hosted models"""
        
        # Convert image to base64
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Hugging Face API (you need a free API key)
        API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
        headers = {"Authorization": "Bearer YOUR_HF_TOKEN"}  # Get free token from huggingface.co
        
        response = requests.post(API_URL, headers=headers, data=image_data)
        return response.json()
    
    # Method 2: Use Google Vision API (Text detection)
    def google_vision_api(image_path):
        """Google Vision API for text detection (requires API key)"""
        # This would require Google Cloud setup
        pass
    
    print("Online API methods require API keys but no model downloads!")
    print("1. Get free Hugging Face API key: https://huggingface.co/settings/tokens")
    print("2. Get Google Vision API key: https://cloud.google.com/vision")

# Option 2: Ultra-lightweight local models
def ultra_lightweight_analysis(image_path):
    """Use only the smallest possible models"""
    from transformers import pipeline
    
    print("Using ultra-lightweight model (only ~200MB download)")
    
    # Smallest image captioning model available
    pipe = pipeline("image-to-text", model="ydshieh/vit-gpt2-coco-en")  # ~200MB
    
    image = Image.open(image_path)
    result = pipe(image)
    caption = result[0]['generated_text']
    
    # Display
    plt.figure(figsize=(8, 6))
    plt.imshow(image)
    plt.axis('off')
    plt.title(f"Caption: {caption}", fontsize=12)
    plt.show()
    
    print(f"Caption: {caption}")
    return caption

# Option 3: Text-only OCR (no AI captioning)
def text_only_analysis(image_path):
    """Extract only text using lightweight OCR"""
    import easyocr  # Still ~150MB but much lighter than full AI models
    
    reader = easyocr.Reader(['en'])
    image = Image.open(image_path)
    
    # Extract text
    results = reader.readtext(np.array(image))
    texts = [text for (bbox, text, conf) in results if conf > 0.5]
    
    # Display
    plt.figure(figsize=(8, 6))
    plt.imshow(image)
    plt.axis('off')
    plt.title("Text Detection Only", fontsize=12)
    plt.show()
    
    print("Text found:")
    for i, text in enumerate(texts, 1):
        print(f"{i}. {text}")
    
    return texts

# Option 4: No-download solution using browser-based models
def browser_based_analysis():
    """Use browser-based models (no downloads)"""
    print("""
    🌐 BROWSER-BASED OPTIONS (No Downloads):
    
    1. **Hugging Face Spaces**: 
       - Visit: https://huggingface.co/spaces/Salesforce/BLIP
       - Upload your image directly in browser
    
    2. **Google AI Test Kitchen**:
       - Visit: https://aitestkitchen.withgoogle.com
       - Try their vision models
    
    3. **OpenAI ChatGPT Vision**:
       - Visit: https://chat.openai.com
       - Upload image and ask about it
    
    4. **Replicate.com**:
       - Visit: https://replicate.com/explore
       - Try various vision models online
    """)

# Option 5: Progressive loading (download only what you need)
def progressive_analysis(image_path, features_needed):
    """Only download models for features you actually need"""
    
    results = {}
    
    if 'basic_caption' in features_needed:
        print("Downloading basic captioning model (~200MB)...")
        pipe = pipeline("image-to-text", model="ydshieh/vit-gpt2-coco-en")
        image = Image.open(image_path)
        result = pipe(image)
        results['caption'] = result[0]['generated_text']
        print(f"✅ Caption: {results['caption']}")
    
    if 'text_detection' in features_needed:
        print("Downloading OCR model (~150MB)...")
        import easyocr
        reader = easyocr.Reader(['en'])
        ocr_results = reader.readtext(image_path)
        texts = [text for (bbox, text, conf) in ocr_results if conf > 0.5]
        results['texts'] = texts
        print(f"✅ Text found: {texts}")
    
    if 'detailed_caption' in features_needed:
        print("⚠️  This requires downloading large model (~1GB+)")
        choice = input("Continue? (y/n): ")
        if choice.lower() == 'y':
            pipe = pipeline("image-to-text", model="Salesforce/blip-image-captioning-large")
            image = Image.open(image_path)
            result = pipe(image, max_length=100)
            results['detailed_caption'] = result[0]['generated_text']
            print(f"✅ Detailed caption: {results['detailed_caption']}")
    
    return results

# Example usage with choices
if __name__ == "__main__":
    image_path = "2.png"  # Replace with your image
    
    print("🎯 CHOOSE YOUR APPROACH:")
    print("=" * 40)
    print("1. Ultra-lightweight (~200MB)")
    print("2. Text-only OCR (~150MB)")  
    print("3. Progressive (choose features)")
    print("4. Online APIs (no downloads)")
    print("5. Browser-based (no downloads)")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    try:
        if choice == "1":
            ultra_lightweight_analysis(image_path)
        elif choice == "2":
            text_only_analysis(image_path)
        elif choice == "3":
            features = ['basic_caption', 'text_detection']  # Modify as needed
            progressive_analysis(image_path, features)
        elif choice == "4":
            analyze_with_online_apis(image_path)
        elif choice == "5":
            browser_based_analysis()
        else:
            print("Invalid choice")
            
    except FileNotFoundError:
        print(f"Image not found: {image_path}")
        print("Please replace 'your_image.jpg' with your actual image path")
    except ImportError as e:
        print(f"Missing package: {e}")
        print("Install with: pip install transformers pillow matplotlib easyocr")