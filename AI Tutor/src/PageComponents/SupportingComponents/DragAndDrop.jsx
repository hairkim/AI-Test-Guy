import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import PropTypes from 'prop-types';
import '../CSS/DragAndDrop.css';

function DragAndDrop({ 
  question, 
  setQuestion, 
  onSubmit, 
  isLoading, 
  storeImage 
}) {
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    console.log('File dropped:', file);
    setIsProcessing(true);
    
    try {
      // Create preview URL for display
      const previewUrl = URL.createObjectURL(file);
      setImagePreview(previewUrl);

      // Convert file to base64 for backend
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const result = event.target.result;
          
          if (result && typeof result === 'string' && result.startsWith('data:')) {
            const base64String = result.split(',')[1];
            
            // Validate base64
            if (base64String && base64String.length > 0) {
              try {
                atob(base64String);
                console.log('Base64 validation: PASSED');
                
                // Store in local state and notify parent
                setImage(base64String);
                if (storeImage && typeof storeImage === 'function') {
                  storeImage(base64String);
                }
              } catch (e) {
                console.error('Invalid base64:', e);
              }
            }
          }
          setIsProcessing(false);
        } catch (error) {
          console.error('Error processing base64:', error);
          setIsProcessing(false);
        }
      };
      
      reader.onerror = (error) => {
        console.error('FileReader error:', error);
        setIsProcessing(false);
      };
      
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Error in onDrop:', error);
      setIsProcessing(false);
    }
  }, [storeImage]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    multiple: false,
    maxSize: 10 * 1024 * 1024,
    noClick: false,
    noKeyboard: false
  });

  const removeImage = () => {
    try {
      if (imagePreview) {
        URL.revokeObjectURL(imagePreview);
      }
      setImage(null);
      setImagePreview(null);
      if (storeImage && typeof storeImage === 'function') {
        storeImage(null);
      }
    } catch (error) {
      console.error('Error removing image:', error);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="unified-input-container">
      {/* Image Preview - shows above the input */}
      {imagePreview && (
        <div className="image-preview-wrapper">
          <div className="image-preview-container">
            <img src={imagePreview} alt="Preview" className="image-preview" />
            <button 
              onClick={removeImage} 
              className="remove-image-button"
              type="button"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Drag and Drop Overlay + Input Wrapper */}
      <div 
        {...getRootProps()} 
        className={`input-dropzone-wrapper ${isDragActive ? 'drag-active' : ''}`}
      >
        <input {...getInputProps()} />
        
        {/* Drag overlay indicator */}
        {isDragActive && (
          <div className="drag-overlay">
            <div className="drag-overlay-content">
              📷 Drop image here
            </div>
          </div>
        )}

        {/* The actual input wrapper */}
        <div className="input-wrapper" onClick={(e) => e.stopPropagation()}>
          <textarea
            className="prompt auto-resize"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={image ? "Ask about the image..." : "Ask me anything..."}
            disabled={isLoading || isProcessing}
            rows={1}
            onClick={(e) => e.stopPropagation()}
          />
          <button 
            className="submit-button"
            onClick={(e) => {
              e.stopPropagation();
              onSubmit();
            }}
            disabled={isLoading || (!question.trim() && !image)}
            type="button"
          >
            {isLoading ? '⏳' : '➤'}
          </button>
        </div>
      </div>
    </div>
  );
}

DragAndDrop.propTypes = {
  question: PropTypes.string.isRequired,
  setQuestion: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
  isLoading: PropTypes.bool.isRequired,
  storeImage: PropTypes.func.isRequired
};

export default DragAndDrop;
