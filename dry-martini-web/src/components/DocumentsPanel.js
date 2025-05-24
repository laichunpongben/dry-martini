// src/components/DocumentsPanel.js
import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItemButton,
  Divider
} from '@mui/material';
import { titleCase } from '../utils/titleCase';

export default function DocumentsPanel({
  security,
  selectedDoc,
  setSelectedDoc
}) {
  return (
    <Box>
      <Typography variant="h6" sx={{ color: 'text.primary', mb: 1 }}>
        Documents
      </Typography>
      <List disablePadding>
        {security.documents.map(doc => (
          <React.Fragment key={doc.id}>
            <ListItemButton
              selected={selectedDoc?.id === doc.id}
              onClick={() => setSelectedDoc(doc)}
              sx={{ py: 0.5 }}
            >
              <Typography sx={{ color: 'text.primary' }}>
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
