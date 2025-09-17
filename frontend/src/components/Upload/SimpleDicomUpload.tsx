import React, { useState, useRef } from 'react';
import {
  Box, Typography, Paper, Button, LinearProgress, Alert,
  Card, CardContent, List, ListItem, ListItemText, ListItemIcon,
  Chip, Divider
} from '@mui/material';
import {
  CloudUpload, CheckCircle, Error, Description
} from '@mui/icons-material';
import { patientService } from '../../services/patientService';

interface SimpleDicomUploadProps {
  patientId: string;
  onUploadComplete?: (results: any[]) => void;
  onError?: (error: string) => void;
}

interface UploadResult {
  filename: string;
  success: boolean;
  study_uid?: string;
  processing_result?: any;
  error?: string;
  file_size?: number;
  upload_time?: string;
}

const SimpleDicomUpload: React.FC<SimpleDicomUploadProps> = ({ 
  patientId, 
  onUploadComplete, 
  onError 
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadProgress(0);
    setUploadResults([]);

    const results: UploadResult[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      try {
        console.log(`🚀 Uploading: ${file.name}`);
        
        // Update progress
        setUploadProgress((i / files.length) * 100);

        // Upload file
        const response = await patientService.uploadFile(patientId, file, 'DICOM study');
        
        console.log('📊 Upload response:', response);

        if (response.success) {
          results.push({
            filename: file.name,
            success: true,
            study_uid: (response as any).study_uid,
            processing_result: (response as any).processing_result,
            file_size: file.size,
            upload_time: new Date().toISOString()
          });
        } else {
          results.push({
            filename: file.name,
            success: false,
            error: response.message || 'Upload failed',
            file_size: file.size
          });
        }

      } catch (error: unknown) {
        console.error(`❌ Upload failed for ${file.name}:`, error);
        results.push({
          filename: file.name,
          success: false,
          error: error instanceof Error ? error.message : 'Upload failed',
          file_size: file.size
        });
      }
    }

    setUploadProgress(100);
    setUploadResults(results);
    setUploading(false);

    // Notify parent component
    if (onUploadComplete) {
      onUploadComplete(results);
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const getSuccessCount = () => {
    return uploadResults.filter(r => r.success).length;
  };

  const getTotalFileSize = () => {
    return uploadResults.reduce((total, result) => total + (result.file_size || 0), 0);
  };

  return (
    <Box>
      {/* Upload Area */}
      <Paper
        sx={{
          p: 4,
          textAlign: 'center',
          border: '2px dashed #ccc',
          cursor: uploading ? 'not-allowed' : 'pointer',
          '&:hover': {
            borderColor: 'primary.main',
            bgcolor: 'primary.50'
          }
        }}
        onClick={!uploading ? handleUploadClick : undefined}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".dcm,.dicom"
          style={{ display: 'none' }}
          onChange={handleFileSelect}
          disabled={uploading}
        />
        
        <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
        
        <Typography variant="h6" gutterBottom>
          📤 DICOM File Upload
        </Typography>
        
        <Typography variant="body1" gutterBottom>
          Click to select DICOM files (.dcm, .dicom)
        </Typography>
        
        <Typography variant="body2" color="text.secondary">
          Multiple files supported • Automatic processing
        </Typography>

        {uploading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress 
              variant="determinate" 
              value={uploadProgress} 
              sx={{ mb: 1 }}
            />
            <Typography variant="body2">
              Uploading... {Math.round(uploadProgress)}%
            </Typography>
          </Box>
        )}

        {!uploading && (
          <Button
            variant="contained"
            startIcon={<CloudUpload />}
            sx={{ mt: 2 }}
            onClick={handleUploadClick}
          >
            Select Files
          </Button>
        )}
      </Paper>

      {/* Upload Results */}
      {uploadResults.length > 0 && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                📊 Upload Results
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Chip 
                  label={`${getSuccessCount()}/${uploadResults.length} successful`}
                  color={getSuccessCount() === uploadResults.length ? 'success' : 'warning'}
                  size="small"
                />
                <Chip 
                  label={`${Math.round(getTotalFileSize() / 1024)} KB total`}
                  variant="outlined"
                  size="small"
                />
              </Box>
            </Box>

            <List dense>
              {uploadResults.map((result, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemIcon>
                      {result.success ? (
                        <CheckCircle color="success" />
                      ) : (
                        <Error color="error" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle2">
                            {result.filename}
                          </Typography>
                          {result.success && result.study_uid && (
                            <Chip 
                              label="Study Created" 
                              color="success" 
                              size="small" 
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          {result.success ? (
                            <Typography variant="body2" color="success.main">
                              ✅ Uploaded successfully
                              {result.study_uid && ` • Study UID: ${result.study_uid.substring(0, 20)}...`}
                            </Typography>
                          ) : (
                            <Typography variant="body2" color="error.main">
                              ❌ {result.error}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < uploadResults.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default SimpleDicomUpload;