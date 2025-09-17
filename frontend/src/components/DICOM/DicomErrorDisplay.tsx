import React from 'react';
import {
  Alert,
  AlertTitle,
  Box,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { DicomError, DicomLoadingState } from '../../types';

interface DicomErrorDisplayProps {
  error: DicomError;
  loadingState?: DicomLoadingState;
  onRetry?: () => void;
  onClear?: () => void;
  showDetails?: boolean;
}

const DicomErrorDisplay: React.FC<DicomErrorDisplayProps> = ({
  error,
  loadingState,
  onRetry,
  onClear,
  showDetails = false
}) => {
  const getSeverityColor = (severity: DicomError['severity']) => {
    switch (severity) {
      case 'low': return 'info';
      case 'medium': return 'warning';
      case 'high': return 'error';
      case 'critical': return 'error';
      default: return 'warning';
    }
  };

  const getErrorIcon = (type: DicomError['type']) => {
    switch (type) {
      case 'network': return '🌐';
      case 'timeout': return '⏱️';
      case 'authentication': return '🔐';
      case 'not_found': return '📋';
      case 'parsing': return '📄';
      case 'memory': return '💾';
      case 'corrupted': return '💥';
      default: return '❌';
    }
  };

  const getActionableMessage = (error: DicomError): string => {
    switch (error.type) {
      case 'network':
        return 'Check your internet connection and try again.';
      case 'timeout':
        return 'The request took too long. Try again or check your connection.';
      case 'authentication':
        return 'Please check your credentials and try again.';
      case 'not_found':
        return 'This image could not be found. It may have been moved or deleted.';
      case 'parsing':
        return 'The image file appears to be corrupted or in an unsupported format.';
      case 'memory':
        return 'Not enough memory to load this image. Try closing other applications.';
      case 'corrupted':
        return 'The image data is corrupted and cannot be displayed.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  };

  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <Box sx={{ mb: 2 }}>
      <Alert 
        severity={getSeverityColor(error.severity)}
        action={
          <Box sx={{ display: 'flex', gap: 1 }}>
            {error.retryable && onRetry && (
              <Button
                size="small"
                startIcon={<RefreshIcon />}
                onClick={onRetry}
                disabled={loadingState?.status === 'retrying'}
              >
                {loadingState?.status === 'retrying' ? 'Retrying...' : 'Retry'}
              </Button>
            )}
            {onClear && (
              <Button size="small" onClick={onClear}>
                Clear
              </Button>
            )}
          </Box>
        }
      >
        <AlertTitle>
          {getErrorIcon(error.type)} DICOM Loading Error
        </AlertTitle>
        
        <Typography variant="body2" sx={{ mb: 1 }}>
          {error.message}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {getActionableMessage(error)}
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          <Chip label={error.code} size="small" />
          <Chip label={error.type} size="small" variant="outlined" />
          <Chip 
            label={error.retryable ? 'Retryable' : 'Not Retryable'} 
            size="small" 
            color={error.retryable ? 'success' : 'error'}
            variant="outlined"
          />
        </Box>

        {loadingState && loadingState.attempts.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Retry Progress ({loadingState.attempts.length}/{loadingState.retryConfig.maxAttempts})
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={(loadingState.attempts.length / loadingState.retryConfig.maxAttempts) * 100}
              sx={{ mb: 1 }}
            />
            {loadingState.status === 'retrying' && (
              <Typography variant="caption" color="text.secondary">
                Retrying... Please wait.
              </Typography>
            )}
          </Box>
        )}

        {showDetails && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle2">
                Error Details & Attempts
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {error.details && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Error Details:
                  </Typography>
                  <Box sx={{ 
                    backgroundColor: 'grey.100', 
                    p: 1, 
                    borderRadius: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.75rem'
                  }}>
                    {JSON.stringify(error.details, null, 2)}
                  </Box>
                </Box>
              )}

              {loadingState && loadingState.attempts.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Attempt History:
                  </Typography>
                  <List dense>
                    {loadingState.attempts.map((attempt, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          {attempt.success ? (
                            <CheckCircleIcon color="success" fontSize="small" />
                          ) : attempt.error ? (
                            <ErrorIcon color="error" fontSize="small" />
                          ) : (
                            <InfoIcon color="info" fontSize="small" />
                          )}
                        </ListItemIcon>
                        <ListItemText
                          primary={`Attempt ${attempt.attempt}`}
                          secondary={
                            <Box>
                              <Typography variant="caption" display="block">
                                {new Date(attempt.timestamp).toLocaleTimeString()}
                                {attempt.duration && ` • ${formatDuration(attempt.duration)}`}
                              </Typography>
                              {attempt.error && (
                                <Typography variant="caption" color="error">
                                  {attempt.error.message}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                <Typography variant="caption" color="text.secondary">
                  Request ID: {error.requestId}<br/>
                  Timestamp: {new Date(error.timestamp).toLocaleString()}
                </Typography>
              </Box>
            </AccordionDetails>
          </Accordion>
        )}
      </Alert>
    </Box>
  );
};

export default DicomErrorDisplay;