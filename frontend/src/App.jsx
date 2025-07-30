import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Download, Eye, Loader } from 'lucide-react';

const App = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [isExporting, setIsExporting] = useState(false);
  const [exportResult, setExportResult] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError(null);
      setUploadResult(null);
      setExportResult(null);
    } else {
      setError('Please select a PDF file');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError(null);
      setUploadResult(null);
      setExportResult(null);
    } else {
      setError('Please drop a PDF file');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const result = await response.json();
      setUploadResult(result);
    } catch (err) {
      setError(`Upload failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleExport = async () => {
    if (!uploadResult) return;

    setIsExporting(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/export-to-sheets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(uploadResult),
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const result = await response.json();
      setExportResult(result);
    } catch (err) {
      setError(`Export failed: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const resetProcess = () => {
    setSelectedFile(null);
    setUploadResult(null);
    setExportResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">M&A Entry Tool</h1>
          <p className="text-gray-600">Automated document processing and data extraction</p>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          {/* File Upload Section */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 flex items-center">
              <Upload className="mr-2" size={24} />
              Upload Document
            </h2>
            
            <div 
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              {selectedFile ? (
                <div className="flex items-center justify-center">
                  <FileText className="text-blue-500 mr-2" size={32} />
                  <div>
                    <p className="text-lg font-medium text-gray-700">{selectedFile.name}</p>
                    <p className="text-sm text-gray-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
              ) : (
                <div>
                  <Upload className="mx-auto text-gray-400 mb-4" size={48} />
                  <p className="text-lg text-gray-600">Drag and drop your PDF file here</p>
                  <p className="text-sm text-gray-500">or click to select a file</p>
                </div>
              )}
            </div>

            {selectedFile && !uploadResult && (
              <div className="mt-4 flex justify-center">
                <button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium flex items-center disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <Loader className="animate-spin mr-2" size={20} />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2" size={20} />
                      Process Document
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg flex items-center">
              <AlertCircle className="mr-2" size={20} />
              {error}
            </div>
          )}

          {/* Upload Result */}
          {uploadResult && (
            <div className="mb-8">
              <h2 className="text-2xl font-semibold mb-4 flex items-center">
                <CheckCircle className="mr-2 text-green-500" size={24} />
                Extraction Results
              </h2>
              
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-gray-600">Document Type</p>
                    <p className="font-medium">{uploadResult.doc_type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Processing ID</p>
                    <p className="font-medium">{uploadResult.processing_id}</p>
                  </div>
                </div>
                
                {/* Deal Summary Preview */}
                {uploadResult.extracted_data?.deal_summary && (
                  <div className="mb-4">
                    <h3 className="font-semibold mb-2">Deal Summary</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-600">Deal Name:</span>
                        <span className="ml-2">{uploadResult.extracted_data.deal_summary.deal_name || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Target Company:</span>
                        <span className="ml-2">{uploadResult.extracted_data.deal_summary.target_company || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Buyer:</span>
                        <span className="ml-2">{uploadResult.extracted_data.deal_summary.buyer || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Deal Size:</span>
                        <span className="ml-2">{uploadResult.extracted_data.deal_summary.deal_size_usd || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="flex space-x-4">
                  <button
                    onClick={handleExport}
                    disabled={isExporting}
                    className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-medium flex items-center disabled:opacity-50"
                  >
                    {isExporting ? (
                      <>
                        <Loader className="animate-spin mr-2" size={16} />
                        Exporting...
                      </>
                    ) : (
                      <>
                        <Download className="mr-2" size={16} />
                        Export to Sheets
                      </>
                    )}
                  </button>
                  
                  <button
                    onClick={() => setUploadResult(null)}
                    className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg font-medium flex items-center"
                  >
                    <Eye className="mr-2" size={16} />
                    View Details
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Export Result */}
          {exportResult && (
            <div className="mb-6">
              <h2 className="text-2xl font-semibold mb-4 flex items-center">
                <CheckCircle className="mr-2 text-green-500" size={24} />
                Export Complete
              </h2>
              
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-800 mb-2">{exportResult.message}</p>
                <a
                  href={exportResult.sheet_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  View Google Sheet
                </a>
              </div>
            </div>
          )}

          {/* Reset Button */}
          {(uploadResult || exportResult) && (
            <div className="text-center">
              <button
                onClick={resetProcess}
                className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium"
              >
                Process Another Document
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-gray-500 text-sm">
          <p>Supported formats: PDF • Maximum file size: 10MB</p>
        </div>
      </div>
    </div>
  );
};

export default App;