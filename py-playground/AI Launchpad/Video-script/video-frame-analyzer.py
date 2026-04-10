import cv2
import os
import base64
import json
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
from datetime import timedelta

class VideoContextExtractor:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the video context extractor.
        
        Args:
            api_key: API key for vision model (OpenAI GPT-4V, Google Vision, etc.)
                    If None, will try to read from OPENAI_API_KEY environment variable
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
    def extract_frames(self, video_path: str, 
                      interval_seconds: float = 2.0,
                      max_frames: int = 50,
                      output_dir: Optional[str] = None) -> List[str]:
        """
        Extract frames from video at specified intervals.
        
        Args:
            video_path: Path to the video file
            interval_seconds: Time interval between frame extractions
            max_frames: Maximum number of frames to extract
            output_dir: Directory to save frames (optional)
            
        Returns:
            List of frame file paths
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = int(fps * interval_seconds)
        
        print(f"Video Info: {fps} FPS, {total_frames} total frames")
        print(f"Extracting every {frame_interval} frames ({interval_seconds}s intervals)")
        
        frames_extracted = []
        frame_count = 0
        extracted_count = 0
        
        # Create output directory if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        while cap.isOpened() and extracted_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                
                if output_dir:
                    # Save frame to file
                    frame_filename = f"frame_{extracted_count:04d}_{timestamp:.1f}s.jpg"
                    frame_path = os.path.join(output_dir, frame_filename)
                    cv2.imwrite(frame_path, frame)
                    frames_extracted.append(frame_path)
                else:
                    # Store frame in memory
                    frames_extracted.append({
                        'frame': frame,
                        'timestamp': timestamp,
                        'frame_number': frame_count
                    })
                
                extracted_count += 1
                print(f"Extracted frame {extracted_count} at {timestamp:.1f}s")
            
            frame_count += 1
        
        cap.release()
        print(f"Total frames extracted: {extracted_count}")
        return frames_extracted
    
    def frame_to_base64(self, frame_path: str) -> str:
        """Convert frame image to base64 string."""
        with open(frame_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_frame_with_openai(self, frame_path: str, 
                                 custom_prompt: Optional[str] = None) -> Dict:
        """
        Analyze a single frame using OpenAI GPT-4V.
        Requires: pip install openai
        """
        try:
            import openai
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        
        if not self.api_key:
            raise ValueError("API key required for OpenAI analysis")
        
        client = openai.OpenAI(api_key=self.api_key)
        
        # Convert frame to base64
        base64_image = self.frame_to_base64(frame_path)
        
        prompt = custom_prompt or """
        Analyze this video frame and describe:
        1. What objects, people, or animals are visible?
        2. What actions or activities are taking place?
        3. What is the setting/environment?
        4. Any notable details or context?
        
        Provide a concise but comprehensive description.
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        return {
            "frame_path": frame_path,
            "description": response.choices[0].message.content,
            "model": "gpt-4-vision-preview"
        }
    
    def analyze_frames_batch(self, frame_paths: List[str], 
                           custom_prompt: Optional[str] = None) -> List[Dict]:
        """Analyze multiple frames and return descriptions."""
        results = []
        
        for i, frame_path in enumerate(frame_paths):
            print(f"Analyzing frame {i+1}/{len(frame_paths)}: {frame_path}")
            try:
                result = self.analyze_frame_with_openai(frame_path, custom_prompt)
                results.append(result)
            except Exception as e:
                print(f"Error analyzing frame {frame_path}: {e}")
                results.append({
                    "frame_path": frame_path,
                    "description": f"Error: {str(e)}",
                    "model": "error"
                })
        
        return results
    
    def generate_video_summary(self, frame_analyses: List[Dict]) -> Dict:
        """Generate an overall summary of the video based on frame analyses."""
        if not frame_analyses:
            return {"summary": "No frames analyzed"}
        
        # Extract all descriptions
        descriptions = [analysis.get("description", "") for analysis in frame_analyses]
        valid_descriptions = [desc for desc in descriptions if not desc.startswith("Error:")]
        
        if not valid_descriptions:
            return {"summary": "No valid frame analyses available"}
        
        # Simple summary generation (you could enhance this with another AI call)
        summary = {
            "total_frames_analyzed": len(frame_analyses),
            "successful_analyses": len(valid_descriptions),
            "video_context": {
                "key_elements": self._extract_common_elements(valid_descriptions),
                "chronological_summary": self._create_chronological_summary(frame_analyses)
            }
        }
        
        return summary
    
    def _extract_common_elements(self, descriptions: List[str]) -> List[str]:
        """Extract common elements mentioned across descriptions."""
        # Simple keyword extraction (can be enhanced with NLP)
        common_words = {}
        for desc in descriptions:
            words = desc.lower().split()
            for word in words:
                if len(word) > 3 and word.isalpha():
                    common_words[word] = common_words.get(word, 0) + 1
        
        # Return most common words
        sorted_words = sorted(common_words.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:10] if count > 1]
    
    def _create_chronological_summary(self, frame_analyses: List[Dict]) -> List[Dict]:
        """Create a chronological summary of the video."""
        summary = []
        for i, analysis in enumerate(frame_analyses):
            if not analysis.get("description", "").startswith("Error:"):
                # Extract timestamp from frame path if available
                frame_path = analysis.get("frame_path", "")
                timestamp = "unknown"
                if "_" in frame_path and "s.jpg" in frame_path:
                    try:
                        timestamp = frame_path.split("_")[-1].replace("s.jpg", "") + "s"
                    except:
                        timestamp = f"frame_{i+1}"
                
                summary.append({
                    "timestamp": timestamp,
                    "description": analysis["description"][:200] + "..." if len(analysis["description"]) > 200 else analysis["description"]
                })
        
        return summary
    
    def process_video(self, video_path: str, 
                     output_dir: str = "extracted_frames",
                     interval_seconds: float = 2.0,
                     max_frames: int = 20,
                     custom_prompt: Optional[str] = None) -> Dict:
        """
        Complete video processing pipeline.
        
        Args:
            video_path: Path to video file
            output_dir: Directory to save frames
            interval_seconds: Interval between frame extractions
            max_frames: Maximum frames to extract
            custom_prompt: Custom analysis prompt
            
        Returns:
            Complete analysis results
        """
        print(f"Processing video: {video_path}")
        
        # Step 1: Extract frames
        frame_paths = self.extract_frames(
            video_path, 
            interval_seconds=interval_seconds,
            max_frames=max_frames,
            output_dir=output_dir
        )
        
        # Step 2: Analyze frames (only if API key provided)
        if self.api_key:
            print("Analyzing frames with AI...")
            frame_analyses = self.analyze_frames_batch(frame_paths, custom_prompt)
            
            # Step 3: Generate summary
            summary = self.generate_video_summary(frame_analyses)
            
            results = {
                "video_path": video_path,
                "frames_extracted": len(frame_paths),
                "frame_analyses": frame_analyses,
                "summary": summary
            }
        else:
            print("No API key provided - frames extracted but not analyzed")
            results = {
                "video_path": video_path,
                "frames_extracted": len(frame_paths),
                "frame_paths": frame_paths,
                "note": "Frames extracted but not analyzed (no API key provided)"
            }
        
        return results
    
    def save_results(self, results: Dict, output_file: str = "video_analysis.json"):
        """Save analysis results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to: {output_file}")


# Example usage
def main():
    """Example usage of the VideoContextExtractor."""
    
    # Method 1: Using environment variable (recommended)
    extractor = VideoContextExtractor()  # Will read from OPENAI_API_KEY env var
    
    # Method 2: Direct API key (less secure)
    # extractor = VideoContextExtractor(api_key="sk-your-actual-api-key-here")
    
    # Example 1: Basic frame extraction only (no API key needed)
    video_path = "Video-656.mp4"
    
    try:
        # Check if we have an API key
        if extractor.api_key:
            print("API key found - will perform full analysis")
            results = extractor.process_video(
                video_path=video_path,
                output_dir="video_frames",
                interval_seconds=3.0,
                max_frames=15,
                custom_prompt="Describe what's happening in this video frame, focusing on actions and emotions."
            )
            extractor.save_results(results, "video_context_analysis.json")
        else:
            print("No API key found - performing frame extraction only")
            results = extractor.process_video(
                video_path=video_path,
                output_dir="video_frames",
                interval_seconds=3.0,
                max_frames=15
            )
        
        print("Processing completed!")
        print(f"Extracted {results['frames_extracted']} frames")
        
    except Exception as e:
        print(f"Error processing video: {e}")
        print("Make sure your video path is correct and you have the required dependencies installed.")


if __name__ == "__main__":
    main()