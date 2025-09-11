import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import PropTypes from 'prop-types';

function DragAndDrop({ storeImage }) {
  const [image, setImage] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [debugInfo, setDebugInfo] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    console.log('File dropped:', file);
    console.log('File type:', file.type);
    console.log('File size:', file.size);

    setIsProcessing(true);
    setDebugInfo(`Processing ${file.name} (${file.type}, ${Math.round(file.size/1024)}KB)`);
    
    try {
      // Create preview URL for display (browser only)
      const previewUrl = URL.createObjectURL(file);
      setImage(previewUrl);

      // Convert file to base64 for backend
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const result = event.target.result;
          console.log('FileReader result type:', typeof result);
          console.log('FileReader result length:', result?.length);
          console.log('FileReader result preview:', result?.substring(0, 50) + '...');
          
          if (result && typeof result === 'string') {
            // Check if it has the data URL prefix
            if (!result.startsWith('data:')) {
              console.error('Result does not start with data:');
              setDebugInfo('Error: Invalid data URL format');
              setIsProcessing(false);
              return;
            }

            const base64String = result.split(',')[1];
            console.log('Base64 string length:', base64String?.length);
            console.log('Base64 preview:', base64String?.substring(0, 50) + '...');
            
            // Validate base64 string
            if (!base64String || base64String.length === 0) {
              console.error('Empty base64 string');
              setDebugInfo('Error: Empty base64 data');
              setIsProcessing(false);
              return;
            }

            // Test base64 validity
            try {
              atob(base64String); // This will throw if invalid base64
              console.log('Base64 validation: PASSED');
            } catch (e) {
              console.error('Invalid base64:', e);
              setDebugInfo('Error: Invalid base64 encoding');
              setIsProcessing(false);
              return;
            }
            
            setDebugInfo(`Successfully processed base64 (${base64String.length} chars)`);
            
            // Send base64 data to parent component
            if (storeImage && typeof storeImage === 'function') {
              console.log('Calling storeImage with base64 data');
              storeImage(base64String);
            } else {
              console.error('storeImage is not a function:', typeof storeImage);
              setDebugInfo('Error: storeImage prop is not a function');
            }
          } else {
            console.error('Invalid result from FileReader');
            setDebugInfo('Error: FileReader returned invalid data');
          }
          setIsProcessing(false);
        } catch (error) {
          console.error('Error processing base64:', error);
          setDebugInfo(`Error: ${error.message}`);
          setIsProcessing(false);
        }
      };
      
      reader.onerror = (error) => {
        console.error('FileReader error:', error);
        setDebugInfo('Error: Failed to read file');
        setIsProcessing(false);
      };
      
      // Read file as data URL (base64)
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Error in onDrop:', error);
      setDebugInfo(`Error: ${error.message}`);
      setIsProcessing(false);
    }
  }, [storeImage]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    multiple: false,
    maxSize: 10 * 1024 * 1024  // 10MB limit
  });

  const removeImage = () => {
    try {
      if (image) {
        URL.revokeObjectURL(image);
      }
      setImage(null);
      setDebugInfo(null);
      if (storeImage && typeof storeImage === 'function') {
        storeImage(null);
      }
    } catch (error) {
      console.error('Error removing image:', error);
    }
  };

  // Test the backend connection
  const testBackend = async () => {
    if (!image) return;
    
    try {
      // Get the base64 data that we're sending
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        const base64 = canvas.toDataURL('image/jpeg').split(',')[1];
        
        console.log('Testing backend with base64 length:', base64.length);
        
        // Make a test API call
        fetch('/ask', {  // Adjust this URL to match your API endpoint
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            question: "test question",
            image: base64
          })
        })
        .then(response => {
          console.log('Backend response status:', response.status);
          return response.json();
        })
        .then(data => {
          console.log('Backend response:', data);
        })
        .catch(error => {
          console.error('Backend error:', error);
        });
      };
      img.src = image;
    } catch (error) {
      console.error('Test backend error:', error);
    }
  };

  return (
    <div>
      <div {...getRootProps()} style={styles.dropzone}>
        <input {...getInputProps()} />
        {isProcessing ? (
          <p>Processing image...</p>
        ) : isDragActive ? (
          <p>Drop the image here...</p>
        ) : (
          <p>Drag & drop an image here, or click to select</p>
        )}
      </div>
      
      {debugInfo && (
        <div style={styles.debug}>
          <strong>Debug Info:</strong> {debugInfo}
        </div>
      )}
      
      {image && (
        <div style={styles.previewContainer}>
          <img src={image} alt="Preview" style={styles.preview} />
          <div style={styles.buttonContainer}>
            <button onClick={removeImage} style={styles.removeButton}>
              Remove Image
            </button>
            <button onClick={testBackend} style={styles.testButton}>
              Test Backend
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  dropzone: {
    border: "2px dashed #888",
    borderRadius: "10px",
    padding: "20px",
    textAlign: "center",
    cursor: "pointer",
    marginBottom: "1rem",
    transition: "border-color 0.2s ease"
  },
  debug: {
    backgroundColor: "#f0f0f0",
    padding: "10px",
    borderRadius: "5px",
    fontSize: "12px",
    marginBottom: "10px",
    fontFamily: "monospace"
  },
  previewContainer: {
    position: "relative",
    display: "inline-block"
  },
  preview: {
    marginTop: "10px",
    maxWidth: "100%",
    maxHeight: "300px",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
  },
  buttonContainer: {
    marginTop: "10px"
  },
  removeButton: {
    background: "#ff4444",
    color: "white",
    border: "none",
    borderRadius: "4px",
    padding: "5px 10px",
    cursor: "pointer",
    marginRight: "10px"
  },
  testButton: {
    background: "#4444ff",
    color: "white",
    border: "none",
    borderRadius: "4px",
    padding: "5px 10px",
    cursor: "pointer"
  }
};

DragAndDrop.propTypes = {
  storeImage: PropTypes.func.isRequired
};

export default DragAndDrop;