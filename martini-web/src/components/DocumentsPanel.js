// src/components/DocumentsPanel.js
import React from 'react';
import { Box, Typography, List, ListItemButton, Divider } from '@mui/material';
import { titleCase } from '../utils/titleCase';

export default function DocumentsPanel({ security, selectedDoc, onDocumentClick }) {
  const count = Array.isArray(security.documents) ? security.documents.length : 0;

  return (
    <Box>
      <Typography
        variant="h6"
        sx={{ color: 'text.primary', mb: 1, pl: 2 }}
      >
        Documents ({count})
      </Typography>
      <List disablePadding>
        {security.documents.map(doc => (
          <React.Fragment key={doc.id}>
            <ListItemButton
              selected={selectedDoc?.id === doc.id}
              onClick={() => onDocumentClick(doc)}
              sx={{ py: 0.5 }}
            >
              <Typography sx={{ color: 'text.primary', pl: 2 }}>
                {titleCase(doc.doc_type)}
              </Typography>
            </ListItemButton>
            <Divider sx={{ bgcolor: '#333' }} />
          </React.Fragment>
        ))}
      </List>
    </Box>
  );
}
