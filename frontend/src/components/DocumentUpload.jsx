import React, { useState, useRef } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle, Loader, FileText, Image, Archive } from 'lucide-react';

function DocumentUpload() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const fileInputRef = useRef(null);

  const supportedTypes = {
    'application/pdf': { icon: FileText, label: 'PDF Documents' },
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': { icon: FileText, label: 'Word Documents' },
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': { icon: Archive, label: 'Excel Spreadsheets' },
    'text/plain': { icon: FileText, label: 'Text Files' },
    'application/json': { icon: FileText, label: 'JSON Files' },
    'text/csv': { icon: Archive, label: 'CSV Files' },
    'image/jpeg': { icon: Image, label: 'JPEG Images' },
    'image/png': { icon: Image, label: 'PNG Images' }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    addFiles(selectedFiles);
  };

  const addFiles = (newFiles) => {
    const validFiles = newFiles.filter(file => {
      const isSupported = Object.keys(supportedTypes).includes(file.type);
      const isValidSize = file.size <= 50 * 1024 * 1024; // 50MB limit
      return isSupported && isValidSize;
    });

    const fileObjects = validFiles.map(file => ({
      id: Date.now() + Math.random(),
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      error: null
    }));

    setFiles(prev => [...prev, ...fileObjects]);
  };

  const removeFile = (id) => {
    setFiles(prev => prev.filter(file => file.id !== id));
    setUploadProgress(prev => {
      const newProgress = { ...prev };
      delete newProgress[id];
      return newProgress;
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type) => {
    const IconComponent = supportedTypes[type]?.icon || File;
    return <IconComponent size={20} />;
  };

  const uploadFiles = async () => {
    if (files.length === 0 || uploading) return;

    setUploading(true);
    
    for (const fileObj of files) {
      if (fileObj.status !== 'pending') continue;

      try {
        // Update file status
        setFiles(prev => prev.map(f => 
          f.id === fileObj.id ? { ...f, status: 'uploading' } : f
        ));

        // Simulate upload progress
        for (let progress = 0; progress <= 100; progress += 10) {
          setUploadProgress(prev => ({ ...prev, [fileObj.id]: progress }));
          await new Promise(resolve => setTimeout(resolve, 100));
        }

        // TODO: Replace with actual API call
        const formData = new FormData();
        formData.append('file', fileObj.file);
        formData.append('type', 'knowledge_base');

        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        const result = await response.json();
        
        // Update file status to success
        setFiles(prev => prev.map(f => 
          f.id === fileObj.id ? { 
            ...f, 
            status: 'success',
            uploadedId: result.id,
            message: 'Successfully added to knowledge base'
          } : f
        ));

      } catch (error) {
        console.error('Upload error:', error);
        
        // Update file status to error
        setFiles(prev => prev.map(f => 
          f.id === fileObj.id ? { 
            ...f, 
            status: 'error',
            error: error.message || 'Upload failed'
          } : f
        ));
      }
    }

    setUploading(false);
  };

  const clearCompleted = () => {
    setFiles(prev => prev.filter(file => file.status === 'pending'));
    setUploadProgress({});
  };

  return (
    <div className="container" style={{ maxWidth: '800px', padding: 'var(--space-4)' }}>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <h1>Document Upload</h1>
        <p style={{ color: 'var(--karray-text-secondary)' }}>
          Upload documents to enhance the K-Array knowledge base. Supported formats include PDF, Word, Excel, and text files.
        </p>
      </div>

      {/* Upload Area */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <div
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          style={{
            border: '2px dashed var(--karray-border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-8)',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'border-color 0.2s ease-in-out',
            backgroundColor: 'var(--karray-surface)'
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={48} style={{ color: 'var(--karray-text-secondary)', marginBottom: 'var(--space-4)' }} />
          <h3 style={{ marginBottom: 'var(--space-2)' }}>Drop files here or click to browse</h3>
          <p style={{ color: 'var(--karray-text-secondary)', marginBottom: 'var(--space-4)' }}>
            Supports PDF, Word, Excel, CSV, JSON, and image files up to 50MB
          </p>
          
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.json,.csv,.jpg,.jpeg,.png"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          
          <button className="btn btn-primary">
            <Upload size={16} />
            Choose Files
          </button>
        </div>
      </div>

      {/* Supported File Types */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <h3 style={{ marginBottom: 'var(--space-4)' }}>Supported File Types</h3>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--space-3)'
        }}>
          {Object.entries(supportedTypes).map(([type, info]) => {
            const IconComponent = info.icon;
            return (
              <div key={type} className="flex items-center gap-2" style={{
                padding: 'var(--space-2)',
                backgroundColor: 'var(--karray-surface)',
                borderRadius: 'var(--radius-md)',
                fontSize: 'var(--font-size-sm)'
              }}>
                <IconComponent size={16} style={{ color: 'var(--karray-primary)' }} />
                {info.label}
              </div>
            );
          })}
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between" style={{ marginBottom: 'var(--space-4)' }}>
            <h3 style={{ margin: 0 }}>Files ({files.length})</h3>
            <div className="flex gap-2">
              <button
                onClick={clearCompleted}
                className="btn btn-secondary"
                disabled={!files.some(f => f.status === 'success' || f.status === 'error')}
              >
                Clear Completed
              </button>
              <button
                onClick={uploadFiles}
                className="btn btn-primary"
                disabled={uploading || files.filter(f => f.status === 'pending').length === 0}
              >
                {uploading ? (
                  <>
                    <Loader size={16} className="loading" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload size={16} />
                    Upload All
                  </>
                )}
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {files.map((fileObj) => (
              <div
                key={fileObj.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-3)',
                  padding: 'var(--space-3)',
                  border: '1px solid var(--karray-border)',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: fileObj.status === 'error' 
                    ? 'rgb(239 68 68 / 0.05)' 
                    : fileObj.status === 'success'
                      ? 'rgb(16 185 129 / 0.05)'
                      : 'var(--karray-background)'
                }}
              >
                {/* File Icon */}
                <div style={{ color: 'var(--karray-primary)' }}>
                  {getFileIcon(fileObj.type)}
                </div>

                {/* File Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ 
                    fontWeight: '500',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {fileObj.name}
                  </div>
                  <div style={{ 
                    fontSize: 'var(--font-size-sm)',
                    color: 'var(--karray-text-secondary)'
                  }}>
                    {formatFileSize(fileObj.size)}
                  </div>
                  {fileObj.message && (
                    <div style={{ 
                      fontSize: 'var(--font-size-sm)',
                      color: fileObj.status === 'error' ? 'var(--karray-error)' : 'var(--karray-success)'
                    }}>
                      {fileObj.message}
                    </div>
                  )}
                  {fileObj.error && (
                    <div style={{ 
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--karray-error)'
                    }}>
                      {fileObj.error}
                    </div>
                  )}
                </div>

                {/* Progress Bar */}
                {fileObj.status === 'uploading' && (
                  <div style={{ width: '100px' }}>
                    <div style={{
                      width: '100%',
                      height: '4px',
                      backgroundColor: 'var(--karray-border)',
                      borderRadius: '2px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${uploadProgress[fileObj.id] || 0}%`,
                        height: '100%',
                        backgroundColor: 'var(--karray-primary)',
                        transition: 'width 0.3s ease'
                      }} />
                    </div>
                    <div style={{ 
                      fontSize: 'var(--font-size-xs)',
                      textAlign: 'center',
                      marginTop: 'var(--space-1)'
                    }}>
                      {uploadProgress[fileObj.id] || 0}%
                    </div>
                  </div>
                )}

                {/* Status Icon */}
                <div>
                  {fileObj.status === 'pending' && (
                    <button
                      onClick={() => removeFile(fileObj.id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        color: 'var(--karray-text-secondary)',
                        padding: 'var(--space-1)'
                      }}
                    >
                      <X size={16} />
                    </button>
                  )}
                  {fileObj.status === 'uploading' && (
                    <Loader size={16} className="loading" style={{ color: 'var(--karray-primary)' }} />
                  )}
                  {fileObj.status === 'success' && (
                    <CheckCircle size={16} style={{ color: 'var(--karray-success)' }} />
                  )}
                  {fileObj.status === 'error' && (
                    <AlertCircle size={16} style={{ color: 'var(--karray-error)' }} />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default DocumentUpload;