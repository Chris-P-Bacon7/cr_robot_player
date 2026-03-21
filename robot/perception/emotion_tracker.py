import cv2
import os

# Suppress TensorFlow oneDNN warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
# Suppress other TensorFlow logging if desired
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from deepface import DeepFace

def track_emotion():
    # Initialize the webcam
    cap = cv2.VideoCapture(0)
    
    print("Starting emotion tracker. Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
            
        try:
            # Analyze the frame for emotions
            # enforce_detection=False prevents crashes when no face is found
            results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            
            # Extract the first face detected
            if isinstance(results, list):
                result = results[0]
            else:
                result = results
                
            dominant_emotion = result['dominant_emotion']
            confidence = result['emotion'][dominant_emotion]
            
            # Prepare the display text
            text = f"{dominant_emotion.capitalize()}: {confidence:.1f}%"
            
            # Draw the text on the frame
            cv2.putText(
                frame, 
                text, 
                (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (0, 255, 0), 
                2, 
                cv2.LINE_AA
            )
            
        except Exception as e:
            # If there's an error (e.g., DeepFace fails to process), just continue
            pass
            
        # Display the frame
        cv2.imshow('Emotion Tracker', frame)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    # Clean up
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    track_emotion()
