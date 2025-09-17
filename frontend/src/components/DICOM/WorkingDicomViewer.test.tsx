import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import WorkingDicomViewer from './WorkingDicomViewer';

const theme = createTheme();

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
);

const mockStudy = {
  id: '1',
  study_uid: '1.2.3.4.5.6.7.8.9.1',
  patient_id: 'PAT001',
  patient_name: 'John Doe',
  study_date: '2024-03-10',
  modality: 'CT',
  exam_type: 'chest_ct',
  study_description: 'CT Chest with IV Contrast',
  image_urls: ['http://localhost:8042/wado?studyUID=1.2.3.4.5.6.7.8.9.1&seriesUID=1&objectUID=1'],
  status: 'completed' as const,
  created_at: '2024-03-10T10:00:00Z'
};

describe('WorkingDicomViewer', () => {
  test('should render loading state initially', () => {
    render(
      <TestWrapper>
        <WorkingDicomViewer study={mockStudy} />
      </TestWrapper>
    );
    
    expect(screen.getByText('Initializing viewer...')).toBeInTheDocument();
  });

  test('should display study information', () => {
    render(
      <TestWrapper>
        <WorkingDicomViewer study={mockStudy} />
      </TestWrapper>
    );
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText(/CT Chest with IV Contrast/)).toBeInTheDocument();
  });
});