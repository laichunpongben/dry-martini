// src/App.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ThemeProvider, Box, Typography } from '@mui/material';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ChartCard from './components/ChartCard';
import DocumentsPanel from './components/DocumentsPanel';
import PdfViewer from './components/PdfViewer';
import FundHoldingsPanel from './components/FundHoldingsPanel';  // ← new import
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

  const securityCache = useRef({});
  const limit = 100;
  const backend = process.env.REACT_APP_BACKEND_URL || 'http://localhost:6010';

  // IntersectionObserver for infinite scroll
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

  // Load security (with caching & prefetch)
  const loadSecurity = async (isin, idx) => {
    setError(null);
    setSelectedDoc(null);
    setSelectedIsin(isin);

    if (securityCache.current[isin]) {
      setSecurity(securityCache.current[isin]);
    } else {
      setLoading(true);
      try {
        const r = await fetch(`${backend}/securities/${isin}`);
        if (!r.ok) throw new Error('Not found');
        const data = await r.json();
        securityCache.current[isin] = data;
        setSecurity(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }

    // Prefetch next
    const next = list[idx + 1];
    if (next && !securityCache.current[next.isin]) {
      fetch(`${backend}/securities/${next.isin}`)
        .then(r2 => r2.ok && r2.json())
        .then(d2 => { if (d2) securityCache.current[next.isin] = d2; })
        .catch(() => {});
    }
  };

  // Download single document
  const onDocumentClick = async doc => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(doc.url);
      if (!res.ok) throw new Error('Failed to fetch document');
      const blob = await res.blob();
      setBlobCache(prev => ({ ...prev, [doc.id]: URL.createObjectURL(blob) }));
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
      <TopBar />

      <Box sx={{ display: 'flex', height: 'calc(100vh - 48px)', bgcolor: 'background.default' }}>
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

        {/* Increase center panel width to 600, padding = 1 */}
        <Box sx={{ width: 600, p: 1, overflowY: 'auto', bgcolor: 'background.default' }}>
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

          {/* New Fund Holdings section */}
          {security && (
            <FundHoldingsPanel holdings={security.fund_holdings} />
          )}
        </Box>

        <Box sx={{ flex: 1, p: 1, bgcolor: 'background.default' }}>
          <PdfViewer selectedDoc={selectedDoc} blobCache={blobCache} />
        </Box>
      </Box>
    </ThemeProvider>
  );
}
