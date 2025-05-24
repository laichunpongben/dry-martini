// src/App.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ThemeProvider, Box, Typography } from '@mui/material';
import Sidebar from './components/Sidebar';
import ChartCard from './components/ChartCard';
import DocumentsPanel from './components/DocumentsPanel';
import PdfViewer from './components/PdfViewer';
import { darkTheme } from './theme';

export default function App() {
  const [list, setList] = useState([]);
  const [security, setSecurity] = useState(null);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [blobCache, setBlobCache] = useState({});
  const [selectedIsin, setSelectedIsin] = useState(null);
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const limit = 100;
  const backend = process.env.REACT_APP_BACKEND_URL || 'http://localhost:6010';

  // Infinite‐scroll observer
  const observer = useRef();
  const lastListItemRef = useCallback(node => {
    if (loading || search) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        setSkip(prev => prev + limit);
      }
    });
    if (node) observer.current.observe(node);
  }, [loading, hasMore, search]);

  // Fetch securities list
  useEffect(() => {
    setLoading(true);
    fetch(`${backend}/securities?skip=${skip}&limit=${limit}`)
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(newItems => {
        setList(prev => {
          const existing = new Set(prev.map(i => i.isin));
          const unique = newItems.filter(item => !existing.has(item.isin));
          return [...prev, ...unique];
        });
        setHasMore(newItems.length === limit);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [skip, backend]);

  // Set document title once
  useEffect(() => {
    document.title = 'Bond Explorer';
  }, []);

  // Load security metadata only
  const loadSecurity = isin => {
    setLoading(true);
    setError(null);
    setSecurity(null);
    setSelectedDoc(null);
    setSelectedIsin(isin);
    setBlobCache({});  // clear prior cache

    fetch(`${backend}/securities/${isin}`)
      .then(r => { if (!r.ok) throw new Error('Not found'); return r.json(); })
      .then(data => {
        setSecurity(data);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  // Download only the clicked document
  const onDocumentClick = async doc => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(doc.url);
      if (!res.ok) throw new Error('Failed to fetch document');
      const blob = await res.blob();
      setBlobCache(prev => ({
        ...prev,
        [doc.id]: URL.createObjectURL(blob)
      }));
      setSelectedDoc(doc);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const filtered = list.filter(
    s =>
      s.isin.includes(search.toUpperCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <ThemeProvider theme={darkTheme}>
      <Box sx={{ display: 'flex', height: '100vh', bgcolor: 'background.default' }}>
        <Sidebar
          list={list}
          filtered={filtered}
          search={search}
          setSearch={setSearch}
          selectedIsin={selectedIsin}
          loadSecurity={loadSecurity}
          loading={loading}
          skip={skip}
          lastListItemRef={lastListItemRef}
        />

        <Box sx={{ width: 540, p: 2, overflowY: 'auto', bgcolor: 'background.default' }}>
          {error && (
            <Typography color="error" align="center">
              {error}
            </Typography>
          )}

          {security && <ChartCard security={security} />}

          {security && (
            <DocumentsPanel
              security={security}
              selectedDoc={selectedDoc}
              onDocumentClick={onDocumentClick}
            />
          )}
        </Box>

        <PdfViewer selectedDoc={selectedDoc} blobCache={blobCache} />
      </Box>
    </ThemeProvider>
  );
}
