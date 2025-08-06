import { React, useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

function DragAndDrop() {
  const [image, setImage] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    const previewUrl = URL.createObjectURL(file);
    setImage(previewUrl);
    // You can also upload to a server here
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] }
  });

  return (
    <div {...getRootProps()} style={styles.dropzone}>
      <input {...getInputProps()} />
      {isDragActive ? (
        <p>Drop the image here ...</p>
      ) : (
        <p>Drag & drop an image here, or click to select</p>
      )}
      {image && <img src={image} alt="Preview" style={styles.preview} />}
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
    marginBottom: "1rem"
  },
  preview: {
    marginTop: "10px",
    maxWidth: "100%",
    maxHeight: "300px"
  }
};

export default DragAndDrop;
