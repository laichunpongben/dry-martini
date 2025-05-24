// src/components/PdfViewer.js
import React from 'react';
import { Box } from '@mui/material';

export default function PdfViewer({ selectedDoc, blobCache }) {
  if (!selectedDoc) return null;
  return (
    <Box
      component="iframe"
      src={blobCache[selectedDoc.id] || selectedDoc.url}
      sx={{ width: '100%', height: '100%', border: 'none' }}
    />
  );
}
